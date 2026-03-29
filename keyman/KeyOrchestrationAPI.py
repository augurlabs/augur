
"""This is a hybrid-fixed specification

The names of the channels *MUST NOT* change, but the channel IDs are free to change.
"""
spec = {
    "channels": [
        {
            "name": "ANNOUNCE",
            "id": "augur-oauth-announce",
            "message_types": {
                "PUBLISH": {
                    "key_str": str,
                    "key_platform": str
                },
                "UNPUBLISH": {
                    "key_str": str,
                    "key_platform": str
                },
                "ACK": {
                    "fields": {
                        "requester_id": { "required": str }
                    },
                    "response": ""
                },
                "LIST_PLATFORMS": {
                    "fields": {
                        "requester_id": { "required": str }
                    },
                    "response": [
                        { "required": list[str] }
                    ]
                },
                "LIST_KEYS": {
                    "fields": {
                        "requester_id": { "required": str },
                        "key_platform": { "required": str }
                    },
                    "response": [
                        { "optional": list[str] },
                        { "optional": { "status": "error" } }
                    ]
                },
                "LIST_INVALID_KEYS": {
                    "fields": {
                        "requester_id": { "required": str },
                        "key_platform": { "required": str }
                    },
                    "response": [
                        { "optional": list[str] },
                        { "optional": { "status": "error" }}
                    ]
                },
                "SHUTDOWN": {}
            }
        }, {
            "name": "REQUEST",
            "id": "worker-oath-request",
            "message_types": {
                "NEW": {
                    "fields": {
                        "key_platform": { "required": str },
                        "requester_id": { "required": str }
                    },
                    "response": {
                        "key": { "optional": str },
                        "wait": { "optional": int }
                    }
                },
                "EXPIRE": {
                    "fields": {
                        "key_str": str,
                        "key_platform": str,
                        "refresh_time": int,
                        "requester_id": str
                    },
                    "response": {

                    }
                },
                "INVALIDATE": {
                    "fields": {
                        "key_str": str,
                        "key_platform": str,
                        "requester_id": str
                    }
                }
            }
        }
    ]
}

class WaitKeyTimeout(Exception):
    """Raised when the Key Orchestrator returns a 'wait' message.

    This indicates that there are no fresh keys available for the requested
    platform.

    Args:
        timeout_seconds: How long the client needs to sleep (in seconds)
            before a fresh key will become available.
    """
    def __init__(self, timeout_seconds: int) -> None:
        self.timeout_seconds = timeout_seconds

class InvalidRequest(Exception):
    """Raised when a request doesn't conform to the KeyOrchestrationAPI spec.

    This can occur due to unknown message type, missing required fields,
    invalid field types, or malformed JSON payload.
    """
    pass