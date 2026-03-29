"""Logic to paginate the Github API."""

import httpx
import time
import logging


from typing import Optional
from enum import Enum

 
def hit_api(key_manager, url: str, logger: logging.Logger, timeout: float = 10, method: str = 'GET', follow_redirects=True) -> Optional[httpx.Response]:
    """Ping the api and get the data back for the page.

    Returns:
        A httpx response that contains the data. None if a timeout occurs
    """
    # self.logger.info(f"Hitting endpoint with {method} request: {url}...\n")

    with httpx.Client() as client:

        try:
            response = client.request(
                method=method, url=url, auth=key_manager, timeout=timeout, follow_redirects=follow_redirects)

        except TimeoutError:
            logger.info(f"Request timed out. Sleeping {round(timeout)} seconds and trying again...\n")
            time.sleep(round(timeout))
            return None
        except httpx.TimeoutException:
            logger.info(f"Request timed out. Sleeping {round(timeout)} seconds and trying again...\n")
            time.sleep(round(timeout))
            return None
        except httpx.NetworkError:
            logger.info(f"Network Error. Sleeping {round(timeout)} seconds and trying again...\n")
            time.sleep(round(timeout))
            return None
        except httpx.ProtocolError:
            logger.info(f"Protocol Error. Sleeping {round(timeout*1.5)} seconds and trying again...\n")
            time.sleep(round(timeout*1.5))
            return None

    return response 


def process_dict_response(logger: logging.Logger, response: httpx.Response, page_data: dict) -> Optional[str]:
    """Process dict response from the api and return the status.

    Args:
        logger: handles logging
        response: used to access the url of the request and the headers
        page_data: dict response from the api

    Returns:
        A string explaining what happened is returned if what happened is determined, otherwise None is returned.
    """
    #logger.info("Request returned a dict: {}\n".format(page_data))

    message = page_data.get('message')
    errors = page_data.get('errors')

    if not message and not errors:
        return GithubApiResult.SUCCESS

    if message == "Not Found":
        logger.error(
            "Github repo was not found or does not exist for endpoint: "
            f"{response.url}"
        )
        return GithubApiResult.REPO_NOT_FOUND

    if message and "You have exceeded a secondary rate limit. Please wait a few minutes before you try again" in message:

        # sleeps for the specified amount of time that github says to retry after
        retry_after = int(response.headers["Retry-After"])
        logger.info(
            f'\n\n\n\nSleeping for {retry_after} seconds due to secondary rate limit issue.\n\n\n\n')
        time.sleep(retry_after)

        return GithubApiResult.SECONDARY_RATE_LIMIT
        # return "do_not_increase_attempts"
    
    if message and "API rate limit exceeded for user" in message:

        current_epoch = int(time.time())
        epoch_when_key_resets = int(response.headers["X-RateLimit-Reset"])
        key_reset_time =  epoch_when_key_resets - current_epoch
        
        if key_reset_time < 0:
            logger.error(f"Key reset time was less than 0 setting it to 0.\nThe current epoch is {current_epoch} and the epoch that the key resets at is {epoch_when_key_resets}")
            key_reset_time = 0
            
        logger.info(f"\n\n\nAPI rate limit exceeded. Sleeping until the key resets ({key_reset_time} seconds)")
        time.sleep(key_reset_time)

        return GithubApiResult.RATE_LIMIT_EXCEEDED

    if message and "You have triggered an abuse detection mechanism." in message:
        # self.update_rate_limit(response, temporarily_disable=True,platform=platform)
        

        # sleeps for the specified amount of time that github says to retry after
        retry_after = int(response.headers["Retry-After"])
        logger.info(f"Abuse mechanism detected sleeping for {retry_after} seconds")
        time.sleep(retry_after)

        return GithubApiResult.ABUSE_MECHANISM_TRIGGERED

    if message == "Bad credentials":
        logger.error("\n\n\n\n\n\n\n Bad Token Detected \n\n\n\n\n\n\n")
        # self.update_rate_limit(response, bad_credentials=True, platform=platform)
        return GithubApiResult.BAD_CREDENTIALS
    
    if errors:
        for error in errors:
            if "API rate limit exceeded for user" in error['message']:
                current_epoch = int(time.time())
                epoch_when_key_resets = int(response.headers["X-RateLimit-Reset"])
                key_reset_time =  epoch_when_key_resets - current_epoch
                
                if key_reset_time < 0:
                    logger.error(f"Key reset time was less than 0 setting it to 0.\nThe current epoch is {current_epoch} and the epoch that the key resets at is {epoch_when_key_resets}")
                    key_reset_time = 0
                    
                logger.info(f"\n\n\nAPI rate limit exceeded. Sleeping until the key resets ({key_reset_time} seconds)")
                time.sleep(key_reset_time)
                return GithubApiResult.RATE_LIMIT_EXCEEDED
            
            err_type = error.get('type')

            if err_type and 'NOT_FOUND' in err_type:
                return GithubApiResult.REPO_NOT_FOUND


    return GithubApiResult.NEW_RESULT

class GithubApiResult(Enum):
    """All the different results of querying the Github API."""

    NEW_RESULT = -1
    SUCCESS = 0
    TIMEOUT = 1
    NO_MORE_ATTEMPTS = 2
    REPO_NOT_FOUND = 3
    SECONDARY_RATE_LIMIT = 4
    RATE_LIMIT_EXCEEDED = 5
    ABUSE_MECHANISM_TRIGGERED = 6
    # TODO: Add bad credentials detection that removes key 
    # from redis if bad credentials are detected
    BAD_CREDENTIALS = 7
    HTML = 8
    EMPTY_STRING = 9
