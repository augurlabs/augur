from os import getpid
import time
import json
from logging import Logger
from redis.client import PubSub

from augur.tasks.init.redis_connection import get_redis_connection
from keyman.KeyOrchestrationAPI import spec, WaitKeyTimeout

class KeyClient:
    """Worker-side interface for requesting API keys from the orchestrator.

    NOT THREAD SAFE! Only one KeyClient can exist at a time per *process*
    as the process ID is used for async communication between the client
    and the orchestrator.

    All functions will block indefinitely if the orchestration server is
    not running or not responding.

    Args:
        platform: Default platform for key requests (e.g., 'github_rest')
        logger: Logger instance for debugging

    Raises:
        ValueError: If platform is empty or None
    """
    # pylint: disable=no-member
    def __init__(self, platform: str, logger: Logger):
        self.id = getpid()
        
        # Load channel names and IDs from the spec
        for channel in spec["channels"]:
            # IE: self.ANNOUNCE = "augur-oauth-announce"
            setattr(self, channel["name"], channel["id"])
            
        if not platform:
            raise ValueError("Platform must not be empty")
        
        self.conn = get_redis_connection()
        
        self.stdout = self.conn
        self.stdin: PubSub = self.conn.pubsub(ignore_subscribe_messages = True)
        self.stdin.subscribe(f"{self.REQUEST}-{self.id}")
        self.platform = platform
        self.logger = logger
    
    def _send(self, req_type: str, **kwargs) -> None:
        """Send a request message to the orchestrator via Redis pub/sub.

        Args:
            req_type: Request type ('NEW', 'EXPIRE', 'INVALIDATE')
            **kwargs: Additional message parameters (e.g., key_platform, key_str)

        Returns:
            None
        """
        kwargs["type"] = req_type
        kwargs["requester_id"] = self.id

        self.stdout.publish(self.REQUEST, json.dumps(kwargs))
    
    def _recv(self, timeout: int | None = None) -> dict:
        """Receive a response message from the orchestrator.

        Args:
            timeout: Optional timeout in seconds for get_message()

        Returns:
            dict: Parsed JSON response message from orchestrator

        Raises:
            WaitKeyTimeout: If orchestrator requests client to wait
        """
        if timeout is not None:
            return self.stdin.get_message(timeout = timeout)

        stream = self.stdin.listen()

        reply = next(stream)

        msg = json.loads(reply["data"])

        if "wait" in msg:
            raise WaitKeyTimeout(msg["wait"])
        return msg
    
    def request(self, platform: str | None = None) -> str:
        """Request a new key from the orchestrator.

        Will block until a key is available. Will block *indefinitely*
        if no keys are available for the requested platform.

        Args:
            platform: Optional platform override. If None, uses the default
                platform provided during initialization.

        Returns:
            str: A fresh API key for the requested platform

        Raises:
            Exception: If orchestrator returns invalid response format
        """
        while True:
            self._send("NEW", key_platform = platform or self.platform)
            try:
                msg = self._recv()
                if "key" in msg:
                    return msg["key"]
                raise Exception(f"Invalid response type: {msg}")
            except WaitKeyTimeout as e:
                self.logger.debug(f"NO FRESH KEYS: sleeping for {e.timeout_seconds} seconds")
                time.sleep(e.timeout_seconds)
            except Exception as e:
                self.logger.exception(f"Error during key request: {e}")
                time.sleep(20)
    
    def expire(self, key: str, refresh_timestamp: int, platform: str | None = None) -> str:
        """Expire a key and get a new key in return.

        Multiple expiration messages can be sent for the same key
        simultaneously. The final expiration message to be received
        will take precedence.

        Will block until a key is available. Will block *indefinitely*
        if no keys are available for the requested platform.

        Args:
            key: The API key to mark as temporarily expired
            refresh_timestamp: Unix timestamp when the key becomes available again
            platform: Optional platform override. If None, uses the default
                platform. The platform given *must* match the old key and
                also the new key.

        Returns:
            str: A fresh API key for the requested platform

        Raises:
            Exception: If orchestrator returns invalid response format
        """
        message = {
            "type": "EXPIRE",
            "key_str": key,
            "key_platform": platform or self.platform,
            "refresh_time": refresh_timestamp,
            "requester_id": self.id
        }

        self.stdout.publish(self.REQUEST, json.dumps(message))
        time.sleep(0.1)
        return self.request(platform)
    
    def invalidate(self, key: str, platform: str | None = None) -> str:
        """Notify the orchestration server that the given key is permanently invalid.

        The key cannot be used to service any future requests and will not refresh.
        Multiple invalidation messages can be sent for the same key simultaneously.
        The initial invalidation message to be received will take precedence.

        Will block until a key is available. Will block *indefinitely* if less than
        two remaining valid keys were available for the given platform before
        invalidation.

        Args:
            key: The API key to mark as permanently invalid
            platform: Optional platform override. If None, uses the default
                platform. The platform given *must* match the old key and
                also the new key.

        Returns:
            str: A fresh API key for the requested platform

        Raises:
            Exception: If orchestrator returns invalid response format
        """
        message = {
            "type": "INVALIDATE",
            "key_str": key,
            "key_platform": platform or self.platform,
            "requester_id": self.id
        }

        self.stdout.publish(self.REQUEST, json.dumps(message))
        time.sleep(0.1)
        return self.request(platform)

class KeyPublisher:
    """Admin interface for publishing/unpublishing keys to orchestrator.

    NOT THREAD SAFE! Only one KeyPublisher can exist at a time per *process*
    as the process ID is used for async communication between the publisher
    and the orchestrator.

    Typically used during Augur startup to load keys from database.
    """
    # pylint: disable=no-member

    def __init__(self) -> None:
        # Load channel names and IDs from the spec
        for channel in spec["channels"]:
            # IE: self.ANNOUNCE = "augur-oauth-announce"
            setattr(self, channel["name"], channel["id"])
        self.conn = get_redis_connection()
        self.id = getpid()
        self.stdin: PubSub = self.conn.pubsub(ignore_subscribe_messages = True)
        self.stdin.subscribe(f"{self.ANNOUNCE}-{self.id}")

    def publish(self, key: str, platform: str) -> None:
        """Publish a key to the orchestration server.

        No reply is sent, and keys are added or overwritten silently.

        Args:
            key: The API key to publish
            platform: The platform type (e.g., 'github_rest', 'gitlab_rest')

        Returns:
            None
        """
        message = {
            "type": "PUBLISH",
            "key_str": key,
            "key_platform": platform
        }

        self.conn.publish(self.ANNOUNCE, json.dumps(message))
    
    def unpublish(self, key: str, platform: str) -> None:
        """Unpublish a key and remove it from orchestration.

        The key will remain in use by workers currently using it,
        but won't be assigned to new requests.

        No reply is sent, and non-existent keys or platforms are ignored silently.

        Args:
            key: The API key to unpublish
            platform: The platform type (e.g., 'github_rest', 'gitlab_rest')

        Returns:
            None
        """
        message = {
            "type": "UNPUBLISH",
            "key_str": key,
            "key_platform": platform
        }

        self.conn.publish(self.ANNOUNCE, json.dumps(message))
    
    def wait(self, timeout_seconds: int = 30, republish: bool = False) -> bool:
        """Wait for ACK from the orchestrator.

        If a lot of publish or unpublish messages are waiting to be processed,
        this will block until all of them have been read.

        Args:
            timeout_seconds: Maximum time to wait for ACK (default: 30)
            republish: If True, resend ACK request 10 times per second until
                response received. Should only be used to wait for the orchestrator
                to come online, as it could put unnecessary messages on the queue
                if the orchestrator is running but very busy.

        Returns:
            bool: True if orchestrator acknowledged within time limit, False if timeout

        Raises:
            ValueError: If timeout_seconds is negative
        """
        if timeout_seconds < 0:
            raise ValueError("timeout cannot be negative")
        
        message = {
            "type": "ACK",
            "requester_id": self.id
        }
        
        listen_delta = 0.1
        self.conn.publish(self.ANNOUNCE, json.dumps(message))
        
        # Just wait for and consume the next incoming message
        while timeout_seconds >= 0:
            # get_message supposedly takes a 'timeout' parameter, but that did not work
            reply = self.stdin.get_message(ignore_subscribe_messages = True)
            
            if reply:
                return True
            elif timeout_seconds < listen_delta:
                break
            elif republish:
                self.conn.publish(self.ANNOUNCE, json.dumps(message))
            
            time.sleep(listen_delta)
            timeout_seconds -= listen_delta
        
        return False

    def list_platforms(self) -> list[str]:
        """Get a list of currently loaded orchestration platforms.

        Returns:
            list[str]: List of platform names (e.g., ['github_rest', 'gitlab_rest'])

        Raises:
            ValueError: If the orchestration server returns a malformed response
        """
        message = {
            "type": "LIST_PLATFORMS",
            "requester_id": self.id
        }
        
        self.conn.publish(self.ANNOUNCE, json.dumps(message))
        
        reply = next(self.stdin.listen())
        
        try:
            reply = json.loads(reply["data"])
        except Exception:
            raise ValueError("Exception during platform list decoding")
        
        if isinstance(reply, list):
            return reply
        
        raise ValueError(f"Unexpected reply during list operation: {reply}")
        
    def list_keys(self, platform: str) -> list[str]:
        """Get a list of currently loaded keys for the given platform.

        Args:
            platform: The platform type (e.g., 'github_rest', 'gitlab_rest')

        Returns:
            list[str]: List of API keys for the platform

        Raises:
            ValueError: If the orchestration server returns a malformed response
                or if the platform does not exist
        """
        message = {
            "type": "LIST_KEYS",
            "requester_id": self.id,
            "key_platform": platform
        }
        
        self.conn.publish(self.ANNOUNCE, json.dumps(message))
        
        reply = next(self.stdin.listen())
        
        try:
            reply = json.loads(reply["data"])
        except Exception:
            raise ValueError("Exception during key list decoding")
        
        if isinstance(reply, list):
            return reply
        elif isinstance(reply, dict) and "status" in reply:
            raise ValueError(f"Orchestration error: {reply['status']}")
        else:
            raise ValueError(f"Unexpected reply during list operation: {reply}")
        
    def list_invalid_keys(self, platform: str) -> list[str]:
        """Get a list of invalid keys for the given platform.

        Args:
            platform: The platform type (e.g., 'github_rest', 'gitlab_rest')

        Returns:
            list[str]: List of permanently invalid API keys for the platform

        Raises:
            ValueError: If the orchestration server returns a malformed response
                or if the platform does not exist
        """
        message = {
            "type": "LIST_INVALID_KEYS",
            "requester_id": self.id,
            "key_platform": platform
        }
        
        self.conn.publish(self.ANNOUNCE, json.dumps(message))
        
        reply = next(self.stdin.listen())
        
        try:
            reply = json.loads(reply["data"])
        except Exception:
            raise ValueError("Exception during key list decoding")
        
        if isinstance(reply, list):
            return reply
        elif isinstance(reply, dict) and "status" in reply:
            raise ValueError(f"Orchestration error: {reply['status']}")
        else:
            raise ValueError(f"Unexpected reply during list operation: {reply}")
        
    def shutdown(self) -> None:
        """Instruct the orchestration server to shutdown.

        The orchestration server will process any requests sent prior to
        this message, then shut down immediately.

        Returns:
            None
        """
        self.conn.publish(self.ANNOUNCE, json.dumps({"type": "SHUTDOWN"}))
