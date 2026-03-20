"""Defines the GithubRandomKeyAuth class"""

from augur.tasks.util.random_key_auth import RandomKeyAuth
from augur.tasks.github.util.github_api_key_handler import GithubApiKeyHandler
from sqlalchemy.orm import Session
from typing_extensions import deprecated

@deprecated("This class is deprecated. Use the KeyClient interface to the Keymanager process instead.")
class GithubRandomKeyAuth(RandomKeyAuth):
    """Defines a github specific RandomKeyAuth class so 
    github collections can have a class randomly selects an api key for each request    
    """

    def __init__(self, logger):
        """Creates a GithubRandomKeyAuth object and initializes the RandomKeyAuth parent class"""

    
        # gets the github api keys from the database via the GithubApiKeyHandler
        github_api_keys = GithubApiKeyHandler(logger).keys
        #github_api_keys = random.sample(github_api_keys, len(github_api_keys))

        if not github_api_keys:
            print("Failed to find github api keys. This is usually because your key has expired")

        # defines the structure of the github api key
        header_name = "Authorization"
        key_format = "token {0}"

        super().__init__(github_api_keys, header_name, logger, key_format)
        
    # It needs to be this at some point, however not all the method calls are sending 3 arguments
    
    # def __init__(self, session: Session, logger):
    #     """Creates a GithubRandomKeyAuth object and initializes the RandomKeyAuth parent class"""

    
    #     # gets the github api keys from the database via the GithubApiKeyHandler
    #     github_api_keys = GithubApiKeyHandler(session, logger).keys
    #     #github_api_keys = random.sample(github_api_keys, len(github_api_keys))

    #     if not github_api_keys:
    #         print("Failed to find github api keys. This is usually because your key has expired")

    #     # defines the structure of the github api key
    #     header_name = "Authorization"
    #     key_format = "token {0}"

    #     super().__init__(github_api_keys, header_name, logger, key_format)