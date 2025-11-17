"""Middleware for FastAPI application."""

from __future__ import annotations

import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from src.logging_config import logger


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add request ID tracking to all requests."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Add request ID to context and response headers.

        Args:
            request: The incoming request.
            call_next: The next middleware or endpoint handler.

        Returns:
            Response with X-Request-ID header added.
        """
        # Generate unique request ID
        request_id = str(uuid.uuid4())

        # Bind request ID to Loguru context for this request
        with logger.contextualize(request_id=request_id):
            # Log incoming request
            logger.info(f"Incoming request: {request.method} {request.url.path}")

            # Process request
            response = await call_next(request)

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            return response

