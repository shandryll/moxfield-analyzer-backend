"""
Shared HTTP client for the application.
Ensures proper resource management and connection pooling.
"""
import os
import httpx
from typing import Optional

_client: Optional[httpx.AsyncClient] = None


def get_http_client(timeout: float | None = None) -> httpx.AsyncClient:
    """
    Get or create a shared HTTP client instance.
    
    Args:
        timeout: Request timeout in seconds (uses env var if not specified)
        
    Returns:
        Configured httpx.AsyncClient instance
    """
    global _client
    
    if timeout is None:
        timeout = float(os.getenv("HTTP_CLIENT_TIMEOUT", "30"))
    
    if _client is None or _client.is_closed:
        max_keepalive = int(os.getenv("HTTP_CLIENT_MAX_KEEPALIVE", "20"))
        max_connections = int(os.getenv("HTTP_CLIENT_MAX_CONNECTIONS", "100"))
        
        _client = httpx.AsyncClient(
            timeout=timeout,
            limits=httpx.Limits(
                max_keepalive_connections=max_keepalive,
                max_connections=max_connections,
            ),
            follow_redirects=True,
        )
    return _client


async def close_http_client() -> None:
    """Close the shared HTTP client and release resources."""
    global _client
    if _client is not None and not _client.is_closed:
        await _client.aclose()
        _client = None
