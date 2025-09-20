"""HTTP Client Protocol for Git Service Integrations."""

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any
import time

from httpx import AsyncClient, HTTPError, HTTPStatusError
from pydantic import SecretStr

from openhands.core.logger import openhands_logger as logger
from openhands.integrations.service_types import (
    AuthenticationError,
    RateLimitError,
    RequestMethod,
    ResourceNotFoundError,
    UnknownException,
)


class HTTPClient(ABC):
    """Abstract base class defining the HTTP client interface for Git service integrations.

    This class abstracts the common HTTP client functionality needed by all
    Git service providers (GitHub, GitLab, BitBucket) while keeping inheritance in place.
    """

    # Default attributes (subclasses may override)
    token: SecretStr = SecretStr('')
    refresh: bool = False
    external_auth_id: str | None = None
    external_auth_token: SecretStr | None = None
    external_token_manager: bool = False
    base_domain: str | None = None

    # Provider identification must be implemented by subclasses
    @property
    @abstractmethod
    def provider(self) -> str: ...

    # Abstract methods that concrete classes must implement
    @abstractmethod
    async def get_latest_token(self) -> SecretStr | None:
        """Get the latest working token for the service."""
        ...

    @abstractmethod
    async def _get_headers(self) -> dict[str, Any]:
        """Get HTTP headers for API requests."""
        ...

    @abstractmethod
    async def _make_request(
        self,
        url: str,
        params: dict | None = None,
        method: RequestMethod = RequestMethod.GET,
    ) -> tuple[Any, dict]:
        """Make an HTTP request to the Git service API."""
        ...

    def _has_token_expired(self, status_code: int) -> bool:
        """Check if the token has expired based on HTTP status code."""
        return status_code == 401

    async def execute_request(
        self,
        client: AsyncClient,
        url: str,
        headers: dict,
        params: dict | None,
        method: RequestMethod = RequestMethod.GET,
    ):
        """Execute an HTTP request using the provided client."""
        sanitized_headers = self._redact_headers(headers)
        sanitized_params = (
            self._sanitize_for_logging(params) if params is not None else None
        )
        logger.debug(
            '[%s] Preparing %s request to %s headers=%s params=%s',
            self.provider,
            method.value,
            url,
            sanitized_headers,
            sanitized_params,
        )

        start_time = time.perf_counter()
        try:
            if method == RequestMethod.POST:
                response = await client.post(url, headers=headers, json=params)
            else:
                response = await client.get(url, headers=headers, params=params)
        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.debug(
                '[%s] HTTP %s %s failed after %.2fms error=%s',
                self.provider,
                method.value,
                url,
                duration_ms,
                exc,
            )
            raise

        duration_ms = (time.perf_counter() - start_time) * 1000
        response_headers: dict[str, Any] = {}
        raw_headers = getattr(response, 'headers', None)
        if isinstance(raw_headers, Mapping):
            response_headers = dict(raw_headers)
        elif raw_headers is not None:
            logger.debug(
                '[%s] Response headers not logged due to unsupported type=%s',
                self.provider,
                type(raw_headers),
            )
        redacted_response_headers = self._redact_headers(response_headers)
        response_preview = self._get_response_preview(response)
        logger.debug(
            '[%s] HTTP %s %s completed status=%s duration_ms=%.2f response_headers=%s response_preview=%s',
            self.provider,
            method.value,
            url,
            response.status_code,
            duration_ms,
            redacted_response_headers,
            response_preview,
        )

        return response

    def handle_http_status_error(
        self, e: HTTPStatusError
    ) -> (
        AuthenticationError | RateLimitError | ResourceNotFoundError | UnknownException
    ):
        """Handle HTTP status errors and convert them to appropriate exceptions."""
        if e.response.status_code == 401:
            return AuthenticationError(f'Invalid {self.provider} token')
        elif e.response.status_code == 404:
            return ResourceNotFoundError(
                f'Resource not found on {self.provider} API: {e}'
            )
        elif e.response.status_code == 429:
            logger.warning(f'Rate limit exceeded on {self.provider} API: {e}')
            return RateLimitError(f'{self.provider} API rate limit exceeded')

        logger.warning(f'Status error on {self.provider} API: {e}')
        return UnknownException(f'Unknown error: {e}')

    def handle_http_error(self, e: HTTPError) -> UnknownException:
        """Handle general HTTP errors."""
        logger.warning(f'HTTP error on {self.provider} API: {type(e).__name__} : {e}')
        return UnknownException(f'HTTP error {type(e).__name__} : {e}')

    def _sanitize_for_logging(self, data: Any) -> Any:
        """Redact sensitive values while keeping structure for debug logs."""
        if isinstance(data, SecretStr):
            return '***'
        if isinstance(data, Mapping):
            return {k: self._sanitize_for_logging(v) for k, v in data.items()}
        if isinstance(data, list):
            return [self._sanitize_for_logging(item) for item in data]
        if isinstance(data, tuple):
            return tuple(self._sanitize_for_logging(item) for item in data)
        if isinstance(data, set):
            return [self._sanitize_for_logging(item) for item in data]
        return data

    def _redact_headers(self, headers: Mapping[str, Any]) -> dict[str, Any]:
        """Mask sensitive header values such as authorization tokens."""
        sensitive_keywords = ('authorization', 'token', 'secret', 'cookie')
        redacted: dict[str, Any] = {}
        for key, value in headers.items():
            if isinstance(key, str) and any(
                keyword in key.lower() for keyword in sensitive_keywords
            ):
                redacted[key] = '***'
            else:
                redacted[key] = self._sanitize_for_logging(value)
        return redacted

    def _get_response_preview(self, response: Any) -> str:
        """Return a truncated, log-safe preview of the HTTP response body."""
        try:
            text = response.text  # type: ignore[assignment]
        except Exception:
            return '<unavailable>'

        if text is None:
            return '<empty>'

        if not isinstance(text, str):
            return '<unavailable>'

        sanitized = text.replace('\n', '\\n')
        limit = 500
        if len(sanitized) > limit:
            return f"{sanitized[:limit]}... [truncated]"
        return sanitized
