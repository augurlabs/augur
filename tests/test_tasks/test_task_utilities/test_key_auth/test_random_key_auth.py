import pytest
import httpx
import random
import time
import logging

from augur.tasks.util.random_key_auth import RandomKeyAuth

logger = logging.getLogger(__name__)

def test_if_header_is_set():

    key = "asubasdfobhaosf"
    
    key_auth = RandomKeyAuth([key], "Authorization", logger)

    with httpx.Client() as client:

            response = client.request(method="GET", url="https://www.google.com/", auth=key_auth, timeout=180)

            assert key == response.request.headers["Authorization"]

def test_token_formatting():

    key = "asubasdfobhaosf"
    key_format = "proprietary key {0}"
    
    key_auth = RandomKeyAuth([key], "Special_Key", logger, key_format)

    with httpx.Client() as client:

            response = client.request(method="GET", url="https://www.google.com/", auth=key_auth, timeout=180)

            assert key_format.format(key) == response.request.headers["Special_Key"]

def test_token_header():

    key = "asubasdfobhaosf"
    header = "werid_header"
    
    key_auth = RandomKeyAuth([key], header, logger)

    with httpx.Client() as client:

            response = client.request(method="GET", url="https://www.google.com/", auth=key_auth, timeout=180)

            assert key == response.request.headers[header]

# def test_if_headers_are_random():

#     urls = ["https://www.google.com/", "https://www.yahoo.com/", "https://www.amazon.com/", "https://www.walmart.com/", "https://github.com/", "https://www.apple.com/", "https://www.instagram.com/", "https://www.facebook.com/"]

#     num_requests = 10
#     key_count = 3
#     total_attempts = 15

#     keys = [str(x) for x in range(0, key_count)]
#     key_counts = [0 for key in keys]

#     key_auth = RandomKeyAuth(keys, "Authorization", logger, "token {0}")

#     success = False
#     with httpx.Client() as client:
#         attempts = 1
#         while attempts <= total_attempts:
#             # print(f"Attempt {attempts}: Making {num_requests} requests")

#             for i in range(0, num_requests): 

#                 url = random.choice(urls)

#                 response = client.request(method="GET", url=url, auth=key_auth, timeout=180)

#                 key = int(response._request.headers["Authorization"].split(" ")[1])

#                 key_counts[key] += 1

#             perfect_uniform_count  = num_requests * attempts / len(keys)
#             less_than_this_count = perfect_uniform_count * 1.2
#             # print(f"{num_requests} requests made. With these counts: {key_counts}. Goal count was: {less_than_this_count}")

#             invalid_count_found = False

#             max_key_count = max(key_counts)
#             if max_key_count > less_than_this_count:
#                 # print(f"Found count of {max_key_count}. Goal count is less than: {less_than_this_count}")
#                 attempts += 1
#                 continue
#             else:
#                 success = True
#                 break

#     assert success

