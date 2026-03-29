"""This module defines the RandomKeyAuth class"""
from typing import List, Optional, Generator

from httpx import Auth, Request, Response
from random import choice
import hashlib
from augur.util.keys import mask_key


class RandomKeyAuth(Auth):
    """Custom Auth class for httpx that randomly assigns an api key to each request.

    Attributes:
        list_of_keys (List[str]): list of keys which are randomly selected from on each request
        header_name (str): name of header that the keys need to be set to
        key_format (str): format string that defines the structure of the key and leaves a {} for the key to be inserted
    """

    def __init__(self, list_of_keys: List[str], header_name: str, logger, key_format: Optional[str] = None):
        self.list_of_keys = list_of_keys
        self.header_name = header_name
        self.key_format = key_format
        self.logger = logger

    def auth_flow(self, request: Request) -> Generator[Request, Response, None]:
        """Attach a randomly selected API key to the request headers."""
        if not self.list_of_keys:
            self.logger.error("No valid keys available to make a request.")
            yield request
            return

        key_value = choice(self.list_of_keys)

        # Log only masked or hashed form, never the full key
        masked = mask_key(key_value)
        self.logger.debug(f"Key used for request (masked): {masked}")

        # Apply formatting if needed
        if self.key_format:
            key_string = self.key_format.format(key_value)
        else:
            key_string = key_value

        # Set header
        request.headers[self.header_name] = key_string
        # sends the request back with modified headers 
        # basically it saves our changes to the request object
        yield request
