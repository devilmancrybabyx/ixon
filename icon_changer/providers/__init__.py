from typing import Dict, List, Optional
from icon_changer.providers.base import BaseProvider, IconResult
from icon_changer.providers.web_search import WebImageProvider
from icon_changer.providers.icons8_search import Icons8Provider
from icon_changer.providers.google_cse import GoogleCSEProvider

PROVIDERS: Dict[str, BaseProvider] = {
    "web": WebImageProvider(),
    "icons8": Icons8Provider(),
    "google_api": GoogleCSEProvider(),
}

def get_provider(name: str) -> BaseProvider:
    """Returns the provider by name, defaulting to WebImageProvider."""
    return PROVIDERS.get(name, PROVIDERS["web"])

def search_icons(query: str, provider_name: str = "web", max_results: int = 30, page: int = 1) -> List[IconResult]:
    """Searches icons using specified provider or falls back to next available provider if empty."""
    provider = get_provider(provider_name)
    results = provider.search(query, max_results=max_results, page=page)

    # If provider returned 0 results and wasn't web, try web
    if not results and provider_name != "web":
        results = PROVIDERS["web"].search(query, max_results=max_results, page=page)
    # If still empty, try icons8
    if not results and provider_name != "icons8":
        results = PROVIDERS["icons8"].search(query, max_results=max_results, page=page)

    return results

__all__ = ["BaseProvider", "IconResult", "PROVIDERS", "get_provider", "search_icons"]
