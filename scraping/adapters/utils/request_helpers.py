"""
HTTP request helpers and utilities.
"""

from typing import Dict, Optional


def get_default_headers(
    user_agent: Optional[str] = None,
    accept_language: str = "en-US,en;q=0.9",
    extra_headers: Optional[Dict[str, str]] = None
) -> Dict[str, str]:
    """
    Get default HTTP headers for requests.
    
    Args:
        user_agent: Custom user agent (uses default if None)
        accept_language: Accept-Language header value
        extra_headers: Additional headers to include
    
    Returns:
        Dictionary of HTTP headers
    """
    if user_agent is None:
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    headers = {
        "User-Agent": user_agent,
        "Accept-Language": accept_language,
    }
    
    if extra_headers:
        headers.update(extra_headers)
    
    return headers


def get_graphql_headers(
    token: str,
    user_agent: Optional[str] = None,
    accept_language: str = "en-US,en;q=0.9"
) -> Dict[str, str]:
    """
    Get headers for GraphQL requests.
    
    Args:
        token: Authorization token
        user_agent: Custom user agent
        accept_language: Accept-Language header value
    
    Returns:
        Dictionary of HTTP headers with auth token
    """
    headers = get_default_headers(user_agent, accept_language)
    headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    })
    return headers
