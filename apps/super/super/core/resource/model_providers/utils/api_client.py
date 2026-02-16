from abc import ABC, abstractmethod
import requests
from .token_counter import count_string_tokens


class BaseAPIClient(ABC):
    def __init__(self, base_url, auth=None):
        """
        Initialize the APIClient.

        :param base_url: The base URL for the API.
        :param auth: Optional authentication details. Can be a tuple (username, password) for basic authentication,
                     or a dictionary with 'token' key for Bearer token authentication.
        """
        self.base_url = base_url
        self.session = requests.Session()
        self.stream = False

        if auth:
            if isinstance(auth, tuple):
                self.session.auth = auth
            elif isinstance(auth, dict) and "token" in auth:
                self.session.headers.update(
                    {"Authorization": f"Bearer {auth['token']}"}
                )

    def _request(
        self, method, endpoint, params=None, data=None, json=None, headers=None
    ):
        """
        Make a request to the API.

        :param method: HTTP method (GET, POST, PUT, DELETE, etc.)
        :param endpoint: API endpoint (path after the base URL).
        :param params: Optional dictionary of query parameters.
        :param data: Optional dictionary, list of tuples or bytes to send in the body.
        :param json: Optional JSON-serializable Python object to send in the body.
        :param headers: Optional dictionary of HTTP Headers to send with the request.

        :return: Response object.
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        response = self.session.request(
            method, url, params=params, data=data, json=json, headers=headers
        )
        response.raise_for_status()  # Raises an exception for HTTP errors.

        # # Check for rate limiting (many APIs use headers like 'X-RateLimit-Remaining' to indicate this)
        # rate_limit_remaining = response.headers.get('X-RateLimit-Remaining')
        # if rate_limit_remaining is not None and int(rate_limit_remaining) <= 0:
        #     print("You've hit the rate limit!")
        return response

    @abstractmethod
    def count_tokens(self, string, model_name):
        pass


class APIClient(BaseAPIClient, ABC):
    def __init__(self, base_url="super-ollama.co", auth=None):
        """
        Initialize the APIClient.

        :param base_url: The base URL for the API.
        :param auth: Optional authentication details. Can be a tuple (username, password) for basic authentication,
                     or a dictionary with 'token' key for Bearer token authentication.
        """
        super().__init__(base_url, auth)

    def completion(
        self, json=None, params=None, headers=None, endpoint="api/generate/", **kwargs
    ):
        if headers is None:
            headers = {}
        return self._request(
            "POST", endpoint, json=json, params=params, headers=headers
        )

    def count_tokens(self, string, model_name):
        return count_string_tokens(string, model_name)
