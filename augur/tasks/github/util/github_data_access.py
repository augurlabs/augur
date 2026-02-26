import logging
import time
import httpx
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception, RetryError
from urllib.parse import urlparse, parse_qs, urlencode
from keyman.KeyClient import KeyClient
from augur.util.keys import mask_key

GITHUB_RATELIMIT_REMAINING_CAP = 50


class RatelimitException(Exception):

    def __init__(self, response, keys_used, message="Github Rate limit exceeded") -> None:

        self.response = response
        keys_used = [ mask_key(k) for k in keys_used]
        super().__init__(f"{message}. Keys used: {keys_used}")

class UrlNotFoundException(Exception):
    pass

class NotAuthorizedException(Exception):
    pass

class ResourceGoneException(Exception):
    """Exception class indicating the requested resource (or necessary parent resource)
    is intentionally unavailable (such as requesting issues for a repo when they are disabled)

    example: https://api.github.com/repos/openshift/release/issues/4352/comments

    See also: https://httpstatuses.com/410
    """
    def __init__(self, message="Resource returned HTTP 410 Gone. It is likely intentionally removed"):
        super().__init__(message)

class GithubDataAccess:
    """Utilities for accessing the GitHub REST API
    """

    def _base_url(self) -> str:
        """the github base URL with HTTP scheme and trailing slash, suitable for building specific API urls.

        Returns:
            str: the base url
        """
        return "https://api.github.com/"

    def issues_endpoint_url(self, owner:str, repo:str, trailing_slash = True) -> str:
        """the github REST API url for the issues endpoint

        Args:
            owner (str): the owner/org of the repo
            repo (str): the repo name
            trailing_slash (bool, optional): Whether to include the trailing slash or not. Defaults to True.

        Returns:
            str: the assembled URL with values filled in. Example: https://api.github.com/repos/owner/repo/issues/
        """
    
        return f"{self._base_url()}repos/{owner}/{repo}/issues" + ("/" if trailing_slash else "")
    
    def contributors_endpoint_url(self, owner:str, repo:str, trailing_slash = True) -> str:
        """the github REST API url for the contributors endpoint

        Args:
            owner (str): the owner/org of the repo
            repo (str): the repo name
            trailing_slash (bool, optional): Whether to include the trailing slash or not. Defaults to True.

        Returns:
            str: the assembled URL with values filled in. Example: https://api.github.com/repos/owner/repo/contributors/
        """
    
        return f"{self._base_url()}repos/{owner}/{repo}/contributors" + ("/" if trailing_slash else "")

    def user_endpoint_url(self, username:str, trailing_slash = True) -> str:
        """the github REST API url for the users endpoint

        Args:
            username (str): the github username to query
            trailing_slash (bool, optional): Whether to include the trailing slash or not. Defaults to True.

        Returns:
            str: the assembled URL with values filled in. Example: https://api.github.com/repos/owner/repo/contributors/
        """
    
        return f"{self._base_url()}users/{username}" + ("/" if trailing_slash else "")
    
    def __init__(self, key_manager, logger: logging.Logger, feature="rest"):
    
        self.logger = logger
        self.feature = feature
        self.key_client = KeyClient(f"github_{feature}", logger)
        self.key = None
        self.expired_keys_for_request = []

    def get_resource_count(self, url):

        # set per_page to 100 explicitly so we know each page is 100 long
        params = {"per_page": 100}
        url = self.__add_query_params(url, params)

        num_pages = self.get_resource_page_count(url)

        # get data for last page
        params = {"page": num_pages}
        url = self.__add_query_params(url, params)

        data = self.get_resource(url)

        return (100 * (num_pages -1)) + len(data)

    def paginate_resource(self, url):

        response = self.make_request_with_retries(url)
        data = response.json()

        # need to ensure data is a list so yield from works properly
        if not isinstance(data, list):
            raise Exception(f"GithubApiHandler.paginate_resource must be used with url that returns a list. Use GithubApiHandler.get_resource to retrieve data that is not paginated. The url of {url} returned a {type(data)}.")

        yield from data

        while 'next' in response.links.keys():

            next_page = response.links['next']['url']

            response = self.make_request_with_retries(next_page)
            data = response.json()

            # need to ensure data is a list so yield from works properly
            if not isinstance(data, list):
                raise Exception(f"GithubApiHandler.paginate_resource must be used with url that returns a list. Use GithubApiHandler.get_resource to retrieve data that is not paginated. The url of {url} returned a {type(data)}. ")

            yield from data

        return 
    
    def get_resource_page_count(self, url):

        response = self.make_request_with_retries(url, method="HEAD")

        if 'last' not in response.links.keys():
            self.logger.warning(f"Github response without links. Headers: {response.headers}.")
            return 1
        
        try:
            last_page_url = response.links['last']['url']

            parsed_url = urlparse(last_page_url)
        
            return int(parse_qs(parsed_url.query)['page'][0])
        except (KeyError, ValueError):
            raise Exception(f"Unable to parse 'last' url from response: {response.links['last']}")

    def get_resource(self, url):

        response = self.make_request_with_retries(url)

        return response.json()  
    
    # TODO: Handle timeout exceptions better
    def make_request(self, url, method="GET", timeout=100):

        with httpx.Client() as client:

            if not self.key:
                self.key = self.key_client.request()

            headers = {"Authorization": f"token {self.key}"}

            response = client.request(method=method, url=url, headers=headers, timeout=timeout, follow_redirects=True)

            if response.status_code in [403, 429]:
                self.expired_keys_for_request.append(self.key)
                self.logger.warning(f"Github rate limit exceeded. Key: {mask_key(self.key)}. Response: {response.text}")
                raise RatelimitException(response, self.expired_keys_for_request)

            # There are cases with PR files, PR commits, and messages where the parent object is removed after 
            # It is collected, leading the the associated URL for those objects to return a 404. 
            # This is not an issue that is really an Exception. It is more of a nominal signal. 
            
            if response.status_code == 404:
                raise UrlNotFoundException(f"Could not find {url}")
            
            if response.status_code == 401:
                raise NotAuthorizedException(f"Could not authorize with the github api")
            
            if response.status_code == 410:
                response_msg = response.json().get("message")
                if response_msg is not None:
                    raise ResourceGoneException(response_msg)
                else:
                    raise ResourceGoneException()
                
            response.raise_for_status()

            try:
                if self.feature == "rest" and "X-RateLimit-Remaining" in response.headers and int(response.headers["X-RateLimit-Remaining"]) < GITHUB_RATELIMIT_REMAINING_CAP:
                    self.expired_keys_for_request.append(self.key)
                    raise RatelimitException(response, self.expired_keys_for_request)
            except ValueError:
                self.logger.warning(f"X-RateLimit-Remaining was not an integer. Value: {response.headers['X-RateLimit-Remaining']}")


            return response
        
    def make_request_with_retries(self, url, method="GET", timeout=100):
        """ What method does?
            1. Catches RetryError and rethrows a nicely formatted OutOfRetriesException that includes that last exception thrown
        """

        try:
            return self.__make_request_with_retries(url, method, timeout)
        except RetryError as e:
            raise e.last_attempt.exception()

    def _decide_retry_policy(exception: Exception) -> bool:
        """Defines whether or not to retry a failed request based on the exception thrown

        Returns:
            bool: Boolean describing whether or not the request should be retried
        """
        return not isinstance(exception, (UrlNotFoundException, ResourceGoneException))
        
    @retry(stop=stop_after_attempt(10), wait=wait_fixed(5), retry=retry_if_exception(_decide_retry_policy))
    def __make_request_with_retries(self, url, method="GET", timeout=100):
        """ What method does?
            1. Retires 10 times
            2. Waits 5 seconds between retires
            3. Does not retry any exceptions excluded by _decide_retry_policy
            4. Catches RatelimitException and waits or expires key before raising exception
        """

        try:
            result = self.make_request(url, method, timeout)
            self.expired_keys_for_request = []
            return result
        except RatelimitException as e:
            self.__handle_github_ratelimit_response(e.response)
            raise e
        except NotAuthorizedException as e:
            self.expired_keys_for_request = []
            self.__handle_github_not_authorized_response()
            raise e

    def __handle_github_not_authorized_response(self):

        self.key = self.key_client.invalidate(self.key)

        
    def __handle_github_ratelimit_response(self, response):

        headers = response.headers
        previous_key = self.key

        if "Retry-After" in headers:

            retry_after = int(headers["Retry-After"])
            self.logger.info('\n\n\n\nEncountered secondary rate limit issue.\n\n\n\n')
            self.key = self.key_client.expire(self.key, time.time() + retry_after)

        elif "X-RateLimit-Remaining" in headers and int(headers["X-RateLimit-Remaining"]) < GITHUB_RATELIMIT_REMAINING_CAP:
            current_epoch = int(time.time())
            epoch_when_key_resets = int(headers["X-RateLimit-Reset"])
            key_reset_time =  epoch_when_key_resets - current_epoch
            
            if key_reset_time < 0:
                self.logger.error(f"Key reset time was less than 0 setting it to 0.\nThe current epoch is {current_epoch} and the epoch that the key resets at is {epoch_when_key_resets}")
                key_reset_time = 0
                
            self.logger.info(f"\n\n\nAPI rate limit exceeded. Key resets in {key_reset_time} seconds. Informing key manager that key is expired")
            self.key = self.key_client.expire(self.key, epoch_when_key_resets)

        else:
            self.key = self.key_client.expire(self.key, time.time() + 60)

        if previous_key == self.key:
            self.logger.error(f"The same key was returned after a request to expire it was sent (key: {mask_key(self.key)})")

    def __add_query_params(self, url: str, additional_params: dict) -> str:
        """Add query params to a url.

        Args:
            url: the url that is being modified
            additional_params: key value pairs specififying the paramaters to be added

        Returns:
            The url with the key value pairs in additional_params added as query params
        """
        url_components = urlparse(url)
        original_params = parse_qs(url_components.query)
        # Before Python 3.5 you could update original_params with
        # additional_params, but here all the variables are immutable.
        merged_params = {**original_params, **additional_params}
        updated_query = urlencode(merged_params, doseq=True)
        # _replace() is how you can create a new NamedTuple with a changed field
        return url_components._replace(query=updated_query).geturl()

        








