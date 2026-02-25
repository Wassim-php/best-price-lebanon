"""
URL manipulation and normalization helpers.
"""

from typing import Optional
from urllib.parse import urljoin, quote_plus


def normalize_image_url(url: Optional[str], base_url: str = "https:") -> Optional[str]:
    """
    Normalize image URL, handling protocol-relative URLs.
    
    Args:
        url: Image URL (can be relative, protocol-relative, or absolute)
        base_url: Base URL or protocol to use for protocol-relative URLs
    
    Returns:
        Normalized absolute URL, or None if input is None/empty
    """
    if not url:
        return None
    
    url = url.strip()
    
    # Handle protocol-relative URLs (//cdn.example.com/image.jpg)
    if url.startswith("//"):
        return f"{base_url}{url}"
    
    # Handle srcset (take first image)
    if " " in url:
        url = url.split(" ")[0]
    
    # Handle comma-separated URLs
    if "," in url:
        url = url.split(",")[0]
    
    return url


def build_product_url(href: Optional[str], base_url: str) -> Optional[str]:
    """
    Build absolute product URL from relative href.
    
    Args:
        href: Relative or absolute URL
        base_url: Base URL for the website
    
    Returns:
        Absolute URL, or None if href is None
    """
    if not href:
        return None
    return urljoin(base_url, href)


def build_search_url(
    base_url: str,
    query: str,
    page: Optional[int] = None,
    search_path: str = "/search",
    query_param: str = "q",
    page_param: str = "page",
    extra_params: Optional[str] = None
) -> str:
    """
    Build a search URL with query and pagination.
    
    Args:
        base_url: Base website URL
        query: Search query
        page: Page number (optional)
        search_path: Search endpoint path
        query_param: Query parameter name
        page_param: Page parameter name
        extra_params: Additional URL parameters
    
    Returns:
        Complete search URL
    """
    url = f"{base_url}{search_path}?{query_param}={quote_plus(query)}"
    
    if extra_params:
        url += f"&{extra_params}"
    
    if page and page > 1:
        url += f"&{page_param}={page}"
    
    return url
