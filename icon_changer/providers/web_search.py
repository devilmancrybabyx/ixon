import re
import requests
from urllib.parse import quote_plus, unquote
from typing import List, Set

from icon_changer.providers.base import BaseProvider, IconResult

class WebImageProvider(BaseProvider):
    """Fetches transparent PNG icons directly from web search engines."""

    name = "web"
    display_name = "Google & Web Images"

    def __init__(self) -> None:
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

    def search(self, query: str, max_results: int = 30, page: int = 1) -> List[IconResult]:
        results: List[IconResult] = []
        seen_urls: Set[str] = set()

        p_idx = max(0, page - 1)
        # Format query for transparent icon search with pagination
        url = f"https://yandex.com/images/search?text={quote_plus(query)}&itype=png&p={p_idx}"

        try:
            resp = requests.get(url, headers=self.headers, timeout=12)
            if resp.status_code != 200:
                return results

            html_text = resp.text

            # 1. Primary high-res direct image links (img_href)
            img_hrefs = re.findall(r'&quot;img_href&quot;:&quot;([^&]+)&quot;', html_text)
            for raw in img_hrefs:
                clean_url = unquote(raw)
                # Verify it looks like an image link
                if clean_url not in seen_urls and any(ext in clean_url.lower() for ext in [".png", ".ico", ".webp", ".jpg"]):
                    seen_urls.add(clean_url)
                    results.append(IconResult(
                        title=query,
                        image_url=clean_url,
                        thumb_url=clean_url,
                        source="Web",
                        width=256,
                        height=256
                    ))
                    if len(results) >= max_results:
                        return results

            # 2. Secondary previews / dups
            if len(results) < max_results:
                preview_urls = re.findall(r'&quot;preview&quot;:\[\{&quot;url&quot;:&quot;([^&]+)&quot;', html_text)
                for raw in preview_urls:
                    clean_url = unquote(raw)
                    if clean_url not in seen_urls:
                        seen_urls.add(clean_url)
                        results.append(IconResult(
                            title=query,
                            image_url=clean_url,
                            thumb_url=clean_url,
                            source="Web",
                            width=256,
                            height=256
                        ))
                        if len(results) >= max_results:
                            return results

            # 3. Fallback direct PNG match in text
            if len(results) < 5:
                raw_pngs = re.findall(r'https?://[^\s"\'<>]+\.png', html_text)
                for p in raw_pngs:
                    if p not in seen_urls and not any(skip in p.lower() for skip in ["yastatic", "icon_share", "logo_black"]):
                        seen_urls.add(p)
                        results.append(IconResult(
                            title=query,
                            image_url=p,
                            thumb_url=p,
                            source="Web",
                            width=256,
                            height=256
                        ))
                        if len(results) >= max_results:
                            return results

        except Exception as e:
            print(f"WebImageProvider error: {e}")

        return results
