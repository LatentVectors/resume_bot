"""Base HTTP client for API calls with typed responses."""

from typing import Any, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from src.config import settings
from src.logging_config import logger

T = TypeVar("T", bound=BaseModel)


class APIClient:
    """Base HTTP client for API calls with typed responses."""

    def __init__(self, base_url: str | None = None):
        """Initialize API client.

        Args:
            base_url: Base URL for API. Defaults to http://localhost:{api_port}.
        """
        if base_url is None:
            base_url = f"http://localhost:{settings.api_port}"
        self.base_url = base_url
        self.timeout = 30.0

    async def _request(
        self,
        method: str,
        path: str,
        response_model: type[T] | None = None,
        **kwargs: Any,
    ) -> T | list[T] | dict[str, Any] | list[Any] | bytes:
        """Make HTTP request to API with optional response model validation.

        Args:
            method: HTTP method (GET, POST, PATCH, DELETE, etc.)
            path: API path (e.g., "/api/v1/jobs")
            response_model: Optional Pydantic model to validate response
            **kwargs: Additional arguments passed to httpx request

        Returns:
            Validated Pydantic model(s) if response_model provided, bytes for PDFs, otherwise raw JSON data

        Raises:
            ValidationError: If response validation fails
            httpx.HTTPStatusError: If HTTP request fails
            httpx.RequestError: If request error occurs
        """
        url = f"{self.base_url}{path}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(method, url, **kwargs)
                response.raise_for_status()

                # Handle PDF/binary responses
                content_type = response.headers.get("content-type", "")
                if "application/pdf" in content_type or response_model is None and "pdf" in path.lower():
                    return response.content

                data = response.json()

                # Validate response with Pydantic model if provided
                if response_model:
                    if isinstance(data, list):
                        return [response_model.model_validate(item) for item in data]
                    return response_model.model_validate(data)

                return data
        except ValidationError as e:
            logger.error(f"Response validation failed: {e}")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(
                f"API request failed: {e.response.status_code} {e.response.text}"
            )
            raise
        except httpx.RequestError as e:
            logger.error(f"API request error: {e}")
            raise

    async def get(
        self,
        path: str,
        response_model: type[T] | None = None,
        **kwargs: Any,
    ) -> T | list[T] | dict[str, Any] | list[Any] | bytes:
        """GET request with optional response model.

        Args:
            path: API path
            response_model: Optional Pydantic model to validate response
            **kwargs: Additional arguments passed to httpx request

        Returns:
            Validated Pydantic model(s) if response_model provided, bytes for PDFs, otherwise raw JSON data
        """
        return await self._request("GET", path, response_model=response_model, **kwargs)

    async def post(
        self,
        path: str,
        response_model: type[T] | None = None,
        **kwargs: Any,
    ) -> T | dict[str, Any] | bytes:
        """POST request with optional response model.

        Args:
            path: API path
            response_model: Optional Pydantic model to validate response
            **kwargs: Additional arguments passed to httpx request

        Returns:
            Validated Pydantic model if response_model provided, bytes for PDFs, otherwise raw JSON data
        """
        return await self._request("POST", path, response_model=response_model, **kwargs)

    async def patch(
        self,
        path: str,
        response_model: type[T] | None = None,
        **kwargs: Any,
    ) -> T | dict[str, Any]:
        """PATCH request with optional response model.

        Args:
            path: API path
            response_model: Optional Pydantic model to validate response
            **kwargs: Additional arguments passed to httpx request

        Returns:
            Validated Pydantic model if response_model provided, otherwise raw JSON data
        """
        return await self._request("PATCH", path, response_model=response_model, **kwargs)

    async def delete(self, path: str, **kwargs: Any) -> None:
        """DELETE request.

        Args:
            path: API path
            **kwargs: Additional arguments passed to httpx request
        """
        await self._request("DELETE", path, **kwargs)


# Global client instance
api_client = APIClient()

