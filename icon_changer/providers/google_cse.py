import requests
from urllib.parse import quote_plus
from typing import List

from icon_changer.providers.base import BaseProvider, IconResult
from icon_changer.core.config import config

class GoogleCSEProvider(BaseProvider):
    """Fetches images directly from Google Custom Search JSON API."""

    name = "google_api"
    display_name = "Google Custom Search API"

    def __init__(self, api_key: str = "", cx: str = "") -> None:
        self.api_key = api_key or config.get("google_api_key", "")
        self.cx = cx or config.get("google_cx", "")

    def is_configured(self) -> bool:
        return bool(self.api_key and self.cx)

    def search(self, query: str, max_results: int = 30, page: int = 1) -> List[IconResult]:
        results: List[IconResult] = []
        if not self.is_configured():
            return results

        url = "https://www.googleapis.com/customsearch/v1"
        start_index = max(1, (page - 1) * 10 + 1)
        params = {
            "key": self.api_key,
            "cx": self.cx,
            "q": query,
            "searchType": "image",
            "fileType": "png",
            "start": start_index,
            "num": min(max_results, 10),  # Google API limit per request is 10
        }

        try:
            resp = requests.get(url, params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("items", [])
                for item in items:
                    link = item.get("link")
                    title = item.get("title", query)
                    image_info = item.get("image", {})
                    thumb = image_info.get("thumbnailLink", link)
                    w = image_info.get("width", 256)
                    h = image_info.get("height", 256)
                    if link:
                        results.append(IconResult(
                            title=title,
                            image_url=link,
                            thumb_url=thumb,
                            source="Google API",
                            width=w,
                            height=h
                        ))
        except Exception as e:
            print(f"GoogleCSEProvider error: {e}")

        return results
