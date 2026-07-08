import asyncio
import json
import os
from typing import Callable, Dict, Optional, Union
from urllib.parse import ParseResultBytes, quote_plus, urlencode, urlparse

from grader_service.errors import APIError
from tornado.httpclient import AsyncHTTPClient, HTTPError, HTTPRequest, HTTPResponse
from traitlets import TraitError, Unicode, validate
from traitlets.config import SingletonConfigurable


class RequestServiceError(Exception):
    def __init__(self, code: int, status_text: str, message: str):
        self.code = code
        self.status_text = status_text
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"[{self.code} {self.status_text}] {self.message}"


class RequestService(SingletonConfigurable):
    url = Unicode(config=True)

    def __init__(
        self,
        default_request_timeout: float = 20.0,
        default_connect_timeout: float = 20.0,
        max_retries: int = 3,  # Max retry attempts for transient errors
        **kwargs,
    ):
        # Set url from environment if not provided
        if "url" not in kwargs:
            kwargs["url"] = os.environ.get("GRADER_HOST_URL", "http://127.0.0.1:4010")
        super().__init__(**kwargs)
        self.log.info(f"RequestService initialized with URL: {self.url}")
        self._http_client = None  # Lazy initialization
        self._service_cookie = None
        self.default_request_timeout = default_request_timeout
        self.default_connect_timeout = default_connect_timeout
        self.max_retries = max_retries

    @property
    def http_client(self):
        """Lazily create HTTP client to ensure DNS is ready"""
        if self._http_client is None:
            self._http_client = AsyncHTTPClient(max_clients=10, force_instance=True)
            self.log.info("Created new HTTP client instance")
        return self._http_client

    def get_authorization_header(self):
        auth_token = os.environ.get("GRADER_API_TOKEN")
        if auth_token is None:
            raise RequestServiceError(401, "Unauthorized", "No Grader API token found.")
        return {"Authorization": f"Token {auth_token}"}

    async def request_with_retries(
        self,
        method: str,
        endpoint: str,
        body: Union[dict, str] = None,
        header: Dict[str, str] = None,
        decode_response: bool = True,
        request_timeout: float = None,
        connect_timeout: float = None,
        max_retries: int = None,
        retry_delay: float = 1.0,  # Initial retry delay in seconds
        backoff_factor: float = 2.0,  # Factor to increase delay between retries
        response_callback: Optional[Callable[[HTTPResponse], None]] = None,
    ) -> Union[dict, list, HTTPResponse]:
        """
        Make an HTTP request with retry logic for transient errors.
        """
        attempt = 0
        retries = max_retries or self.max_retries

        while attempt < retries:
            try:
                return await self.request(
                    method=method,
                    endpoint=endpoint,
                    body=body,
                    header=self.get_authorization_header(),
                    decode_response=decode_response,
                    request_timeout=request_timeout,
                    connect_timeout=connect_timeout,
                    response_callback=response_callback,
                )
            except (HTTPError, ConnectionRefusedError) as e:
                if isinstance(e, HTTPError) and e.code not in {502, 503, 504}:
                    raise  # Re-raise if it's not a retryable HTTP error
                attempt += 1
                if attempt < retries:
                    retry_delay_seconds = retry_delay * (backoff_factor ** (attempt - 1))
                    self.log.warning(
                        f"Retry {attempt}/{retries} after {retry_delay_seconds}s due to error: {e}"
                    )
                    await asyncio.sleep(retry_delay_seconds)
                else:
                    raise RequestServiceError(
                        503,
                        "Service Unavailable",
                        "Max retries reached. Upstream service unavailable.",
                    )

    async def request(
        self,
        method: str,
        endpoint: str,
        body: Union[dict, str] = None,
        header: Dict[str, str] = None,
        decode_response: bool = True,
        request_timeout: float = None,
        connect_timeout: float = None,
        response_callback: Optional[Callable[[HTTPResponse], None]] = None,
    ) -> Union[dict, list, HTTPResponse]:
        """
        Core request function that handles the HTTP call.
        """
        if header is None:
            header = self.get_authorization_header()

        self.log.info(f"Requesting {method} {self.url + endpoint}")
        request_timeout = request_timeout or self.default_request_timeout
        connect_timeout = connect_timeout or self.default_connect_timeout

        header = self.prepare_headers(header)

        if isinstance(body, dict):
            body = json.dumps(body)

        request = HTTPRequest(
            url=self.url + endpoint,
            method=method,
            headers=header,
            body=body if body else None,
            request_timeout=request_timeout,
            connect_timeout=connect_timeout,
        )

        try:
            response: HTTPResponse = await self.http_client.fetch(request=request)
            self.log.info(
                f"Received response with status {response.code} from {response.effective_url}"
            )

            if decode_response:
                # Check the Content-Type of the response
                content_type = response.headers.get("Content-Type", "")
                if "application/json" in content_type:
                    response_data = json.loads(response.body)
                elif "text/csv" in content_type or "text/plain" in content_type:
                    response_data = response.body.decode("utf-8")
                else:
                    # Fallback: return as plain text
                    response_data = response.body.decode("utf-8")
            else:
                response_data = response

            if response_callback:
                response_callback(response)

            return response_data
        except HTTPError as http_error:
            self.log.error(f"HTTP error occurred: {http_error.response.reason}")
            raise RequestServiceError(
                http_error.code,
                "Service Error",
                http_error.response.reason or "An error occurred in the upstream service.",
            )

        except ConnectionRefusedError:
            self.log.error(f"Connection refused for {self.url + endpoint}")
            raise RequestServiceError(
                502, "Bad Gateway", "Unable to connect to the upstream service."
            )

        except APIError as e:
            self.log.error(f"API error occurred: {e.message}")
            raise RequestServiceError(
                e.status_code,
                "API Error",
                e.message or "An API error occurred in the upstream service.",
            )

        except Exception as e:
            self.log.error(f"Unexpected error: {e}")
            raise RequestServiceError(
                500, "Internal Server Error", f"An unexpected error occurred: {str(e)}"
            )

    def prepare_headers(self, header: Dict[str, str] = None) -> Dict[str, str]:
        """
        Prepares headers by adding service cookie or authorization if available.
        """
        if header is None:
            header = {}
        if self._service_cookie:
            header["Cookie"] = self._service_cookie
        if "Authorization" not in header and os.getenv("SERVICE_TOKEN"):
            header["Authorization"] = f"Bearer {os.getenv('SERVICE_TOKEN')}"
        return header

    @validate("url")
    def _validate_url(self, proposal):
        url = proposal["value"]
        result: ParseResultBytes = urlparse(url)
        if not all([result.scheme, result.hostname]):
            raise TraitError("Invalid URL: must contain both scheme and hostname")
        return url

    @staticmethod
    def get_query_string(params: dict) -> str:
        """
        Helper to build query strings from a dictionary of parameters.
        """
        d = {k: v for k, v in params.items() if v is not None}
        query_params: str = urlencode(d, quote_via=quote_plus)
        return "?" + query_params if query_params else ""
