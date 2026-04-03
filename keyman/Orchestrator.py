import os
import json
import random
import time

from keyman.KeyOrchestrationAPI import spec, WaitKeyTimeout, InvalidRequest

if os.environ.get("KEYMAN_DOCKER"):
    import sys
    import redis
    import logging

    sys.path.append("/augur")

    # Only create a Redis connection if a connection string is provided.
    redis_url = os.environ.get("REDIS_CONN_STRING")
    if redis_url:
        conn = redis.Redis.from_url(redis_url)
    else:
        conn = None

    # Just log to stdout if we're running in docker
    logger = logging.Logger("KeyOrchestrator")
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)  # Attach the handler to the logger
    logger.setLevel(logging.DEBUG)
else:
    from augur.tasks.init.redis_connection import get_redis_connection
    from augur.application.logs import AugurLogger

    logger = AugurLogger("KeyOrchestrator").get_logger()
    conn = get_redis_connection()

class KeyOrchestrator:
    """Central API key management server for distributed workers.

    Manages three key pools per platform:
    - fresh_keys: Available for assignment to workers
    - expired_keys: Rate-limited keys with refresh timestamps
    - invalid_keys: Permanently bad keys (never refreshed)

    Listens on two Redis pub/sub channels:
    - ANNOUNCE: Admin operations (PUBLISH, UNPUBLISH, LIST_*, SHUTDOWN)
    - REQUEST: Worker operations (NEW, EXPIRE, INVALIDATE)

    Single-threaded process that handles all key requests synchronously.
    """
    def __init__(self) -> None:

        self.stdin = conn.pubsub(ignore_subscribe_messages = True)
        self.logger = logger

        # Load channel names and IDs from the spec
        for channel in spec["channels"]:
            # IE: self.ANNOUNCE = "augur-oauth-announce"
            setattr(self, channel["name"], channel["id"])
            self.stdin.subscribe(channel["id"])

        self.fresh_keys: dict[str, list[str]] = {}
        self.expired_keys: dict[str, dict[str, int]] = {}
        self.invalid_keys: dict[str, set[str]] = {}

    def publish_key(self, key: str, platform: str) -> None:
        """Add a key to the fresh pool for the given platform.

        Args:
            key: API key string
            platform: Platform identifier (e.g., 'github_rest')
        """
        if platform not in self.fresh_keys:
            self.fresh_keys[platform] = [key]
            self.expired_keys[platform] = {}
            self.invalid_keys[platform] = set()
        else:
            self.fresh_keys[platform].append(key)

    def unpublish_key(self, key: str, platform: str) -> None:
        """Remove a key from circulation (fresh or expired pool).

        Args:
            key: API key string
            platform: Platform identifier
        """
        if platform not in self.fresh_keys:
            return

        if key in self.fresh_keys[platform]:
            self.fresh_keys[platform].remove(key)
        elif key in self.expired_keys[platform]:
            self.expired_keys[platform].pop(key)

    def expire_key(self, key: str, platform: str, timeout: int) -> None:
        """Move key from fresh to expired pool with refresh timestamp.

        Args:
            key: API key string
            platform: Platform identifier
            timeout: Unix timestamp when key becomes fresh again
        """
        if platform not in self.fresh_keys or key not in self.fresh_keys[platform]:
            return

        self.fresh_keys[platform].remove(key)
        self.expired_keys[platform][key] = timeout

    def invalidate_key(self, key: str, platform: str) -> None:
        """Permanently invalidate a key (typically due to 401 response).

        Args:
            key: API key string
            platform: Platform identifier
        """
        if platform not in self.fresh_keys:
            return

        if key in self.fresh_keys[platform]:
            self.fresh_keys[platform].remove(key)
            self.logger.debug("Invalidating fresh key")
        elif key in self.expired_keys[platform]:
            self.logger.debug("Invalidating expired key")
            self.expired_keys[platform].pop(key)
        else:
            self.logger.debug(f"No such valid key {key} for platform: {platform}")

        self.invalid_keys[platform].add(key)

    def refresh_keys(self) -> None:
        """Move expired keys back to fresh pool if their timeout has passed."""
        curr_time = time.time()

        for platform in self.expired_keys:
            refreshed_keys = []

            for key, timeout in self.expired_keys[platform].items():
                if timeout <= curr_time:
                    refreshed_keys.append(key)

            for key in refreshed_keys:
                self.fresh_keys[platform].append(key)
                self.expired_keys[platform].pop(key)

    def new_key(self, platform: str) -> str | None:
        """Get a random fresh key for the platform, or raise WaitKeyTimeout.

        Args:
            platform: Platform identifier

        Returns:
            Random key from fresh pool, or None if no keys published

        Raises:
            InvalidRequest: If platform doesn't exist
            WaitKeyTimeout: If no fresh keys available (includes wait duration)
        """
        if platform not in self.fresh_keys:
            self.logger.warning(
                f"Key requested for uninitialized platform '{platform}'; this may occur during startup after state cleanup."
            )
            return

        if not len(self.fresh_keys[platform]):
            if not len(self.expired_keys[platform]):
                self.logger.warning(f"Key was requested for {platform}, but none are published")
                return

            min_timeout = 0
            for _, timeout in self.expired_keys[platform].items():
                if not min_timeout or timeout < min_timeout:
                    min_timeout = timeout

            delta = int(min_timeout - time.time())

            raise WaitKeyTimeout(delta + 5 if delta > 0 else 5)

        return random.choice(self.fresh_keys[platform])

    def run(self) -> None:
        """Main event loop - listens for Redis pub/sub messages and processes requests."""
        self.logger.info("Ready")
        for msg in self.stdin.listen():
            try:
                if msg.get("type") != "message":
                    # Filter out unwanted events
                    continue
                elif not (channel := msg.get("channel")):
                    # The pub/sub API makes no guarantee that a channel will be specified
                    continue
            
                # The docs say that msg.channel is a bytes, but testing shows it's a str ?
                channel: str = channel.decode() if isinstance(channel, bytes) else channel

                request = json.loads(msg.get("data"))
            except KeyboardInterrupt:
                # Do not continue on SIGINT
                break
            except Exception as e:
                self.logger.error("Error during request decoding")
                self.logger.exception(e)
                continue
            
            """For performance reasons: Instead of dynamically checking that the
            given channel matches one that we're listening for, just check against each
            channel that we have actions prepared for.
            """
            if channel == self.ANNOUNCE:
                if "requester_id" in request:
                    stdout = f"{self.ANNOUNCE}-{request['requester_id']}"
                try:
                    if request["type"] == "PUBLISH":
                        self.publish_key(request["key_str"], request["key_platform"])
                    elif request["type"] == "UNPUBLISH":
                        self.unpublish_key(request["key_str"], request["key_platform"])
                    elif request["type"] == "ACK":
                        conn.publish(stdout, "")
                        self.logger.info(f"ACK; for: {request['requester_id']}")
                    elif request["type"] == "LIST_PLATFORMS":
                        platforms = [ p for p in self.fresh_keys.keys() ]
                        conn.publish(stdout, json.dumps(platforms))
                    elif request["type"] == "LIST_KEYS":
                        keys = list(self.fresh_keys[request["key_platform"]])
                        keys += list(self.expired_keys[request["key_platform"]].keys())
                        conn.publish(stdout, json.dumps(keys))
                    elif request["type"] == "LIST_INVALID_KEYS":
                        keys = list(self.invalid_keys[request["key_platform"]])
                        conn.publish(stdout, json.dumps(keys))
                    elif request["type"] == "SHUTDOWN":
                        self.logger.info("Shutting down")
                        # Close
                        return
                except KeyboardInterrupt:
                    break
                except Exception:
                    # This is a bare exception, because we don't really care why failure happened
                    self.logger.exception("Error during ANNOUNCE")
                    continue
                
            elif channel == self.REQUEST:
                self.refresh_keys()
                stdout = f"{self.REQUEST}-{request['requester_id']}"

                try:
                    if request["type"] == "NEW":
                        new_key = self.new_key(request["key_platform"])
                    elif request["type"] == "EXPIRE":
                        self.expire_key(request["key_str"], request["key_platform"], request["refresh_time"])
                        self.logger.debug(f"EXPIRE; from: {request['requester_id']}, platform: {request['key_platform']}")
                        continue
                    elif request["type"] == "INVALIDATE":
                        self.invalidate_key(request["key_str"], request["key_platform"])
                        self.logger.debug(f"INVALIDATE; from: {request['requester_id']}, platform: {request['key_platform']}")
                        continue
                except KeyboardInterrupt:
                    break
                except WaitKeyTimeout as w:
                    timeout = w.timeout_seconds
                    conn.publish(stdout, json.dumps({
                        "wait": timeout
                    }))
                    continue
                except Exception:
                    # This is a bare exception, because we don't really care why failure happened
                    self.logger.exception("Error during REQUEST")
                    continue

                self.logger.debug(f"REPLY; for: {request['requester_id']}, platform: {request['key_platform']}")
                conn.publish(stdout, json.dumps({
                    "key": new_key
                }))
                    
if __name__ == "__main__":
    manager = KeyOrchestrator()
    
    try:
        manager.run()
    except KeyboardInterrupt:
        # Exit silently on sigint
        manager.logger.info("Interrupted")
        pass
