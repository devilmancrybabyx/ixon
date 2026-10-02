import re
import requests
from urllib.parse import quote_plus
from typing import List

from icon_changer.providers.base import BaseProvider, IconResult
from requests.adapters import HTTPAdapter

class Icons8Provider(BaseProvider):
    """Fetches high-quality transparent icons from Icons8."""

    name = "icons8"
    display_name = "Icons8 Library"

    def __init__(self) -> None:
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "application/json",
        }
        self.session = requests.Session()
        adapter = HTTPAdapter(pool_connections=20, pool_maxsize=20, max_retries=0)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def search(self, query: str, max_results: int = 30, page: int = 1) -> List[IconResult]:
        results: List[IconResult] = []
        # Strip generic words like 'icon', 'png', etc. with whole-word boundary
        cleaned_term = re.sub(r'\b(icon|png|transparent|ico)\b', '', query, flags=re.IGNORECASE)
        cleaned_term = " ".join(cleaned_term.split()).strip()
        if not cleaned_term:
            cleaned_term = query

        offset = max(0, page - 1) * max_results
        url = f"https://search.icons8.com/api/iconsets/v5/search?term={quote_plus(cleaned_term)}&amount={max_results}&offset={offset}"

        try:
            resp = self.session.get(url, headers=self.headers, timeout=(2.5, 5.0))
            if resp.status_code == 200:
                data = resp.json()
                icons = data.get("icons", [])
                for item in icons:
                    icon_id = item.get("id")
                    name = item.get("name", query)
                    if icon_id:
                        # Full-res 256px transparent PNG
                        img_url = f"https://img.icons8.com/?size=256&id={icon_id}&format=png"
                        thumb_url = f"https://img.icons8.com/?size=96&id={icon_id}&format=png"
                        results.append(IconResult(
                            title=name,
                            image_url=img_url,
                            thumb_url=thumb_url,
                            source="Icons8",
                            width=256,
                            height=256
                        ))
        except Exception as e:
            print(f"Icons8Provider error: {e}")

        return results
