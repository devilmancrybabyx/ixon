import html
import re
from urllib.parse import quote_plus, unquote
from typing import List, Set
import requests
from requests.adapters import HTTPAdapter

from icon_changer.providers.base import BaseProvider, IconResult

class WebImageProvider(BaseProvider):
    """Fetches high-quality transparent PNG/WebP icons directly from web search engines."""

    name = "web"
    display_name = "Google & Web Images"

    # Known high-quality transparent icon domains to prioritize
    PRIORITY_DOMAINS = (
        "flaticon.com",
        "icons8.com",
        "steamgriddb.com",
        "iconfinder.com",
        "vecteezy.com",
        "shareicon.net",
        "icon-icons.com",
        "wikimedia.org",
        "freepnglogos.com",
        "pngimg.com",
        "pngall.com",
        "iconbolt.com",
        "cleanpng.com",
        "toppng.com",
        "brandlogos.net",
        "emoji.gg",
        "pngrepo.com",
        "pngaaa.com",
    )

    # Blacklist domains that block hotlinking (403), require auth, or return opaque/tracking pixels
    BLACKLIST_DOMAINS = (
        "pngwing.com",
        "pngegg.com",
        "deviantart.net",
        "wixmp.com",
        "yastatic.net",
        "yandex.net",
        "avatars.mds",
        "gstatic.com",
        "doubleclick.net",
        "adsystem.com",
    )

    def __init__(self) -> None:
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        self.session = requests.Session()
        adapter = HTTPAdapter(pool_connections=20, pool_maxsize=20, max_retries=0)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def search(self, query: str, max_results: int = 30, page: int = 1) -> List[IconResult]:
        results: List[IconResult] = []
        seen_urls: Set[str] = set()

        p_idx = max(0, page - 1)
        # Ensure search query contains icon/png for transparent results if not present
        search_term = query.strip()
        lower_term = search_term.lower()
        if "png" not in lower_term and "icon" not in lower_term:
            search_term = f"{search_term} icon png"

        url = f"https://yandex.com/images/search?text={quote_plus(search_term)}&itype=png&p={p_idx}"

        try:
            resp = self.session.get(url, headers=self.headers, timeout=(3.5, 9.0))
            if resp.status_code != 200:
                return results

            unescaped = html.unescape(resp.text)

            # 1. Primary extraction: Fast edge CDN thumbnail + high-res direct image links
            pattern = re.compile(
                r'"thumb":\{"url":"([^"]+)"[^}]*\}.*?'
                r'(?:"snippet":\{[^{}]*?"title":"([^"]*)"[^}]*\},.*?)?'
                r'"img_href":"([^"]+)"',
                re.DOTALL
            )

            raw_matches = []
            for m in pattern.finditer(unescaped):
                raw_thumb = m.group(1)
                thumb = ("https:" + raw_thumb) if raw_thumb.startswith("//") else raw_thumb
                title = m.group(2) or query
                raw_img = unquote(m.group(3))
                clean_path = raw_img.split("?")[0].lower()

                # Strictly require transparent formats (.png, .webp, .ico) — NEVER .jpg or .jpeg
                if not any(clean_path.endswith(ext) for ext in (".png", ".webp", ".ico")):
                    continue

                # Check blacklist
                if any(bad in raw_img.lower() for bad in self.BLACKLIST_DOMAINS):
                    continue

                if clean_path in seen_urls:
                    continue
                seen_urls.add(clean_path)
                raw_matches.append((title, raw_img, thumb))

            # Prioritize top icon CDNs (Flaticon, Icons8, SteamGridDB, etc.)
            def sort_priority(item):
                _, img_url, _ = item
                lower_u = img_url.lower()
                for rank, dom in enumerate(self.PRIORITY_DOMAINS):
                    if dom in lower_u:
                        return rank
                return len(self.PRIORITY_DOMAINS) + 1

            sorted_matches = sorted(raw_matches, key=sort_priority)

            for title, img, thumb in sorted_matches:
                results.append(IconResult(
                    title=title,
                    image_url=img,     # Full-resolution original for ICO generation
                    thumb_url=thumb,   # Ultra-fast edge CDN thumbnail (50ms)
                    source="Web",
                    width=256,
                    height=256
                ))
                if len(results) >= max_results:
                    return results

            # 2. Secondary fallback: direct img_href without matched thumb
            if len(results) < max_results:
                raw_hrefs = re.findall(r'"img_href":"([^"]+)"', unescaped)
                for raw in raw_hrefs:
                    clean_url = unquote(raw)
                    clean_path = clean_url.split("?")[0].lower()
                    if not any(clean_path.endswith(ext) for ext in (".png", ".webp", ".ico")):
                        continue
                    if any(bad in clean_url.lower() for bad in self.BLACKLIST_DOMAINS):
                        continue
                    if clean_path not in seen_urls:
                        seen_urls.add(clean_path)
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

            # 3. Tertiary fallback: direct PNG URLs in text
            if len(results) < 5:
                raw_pngs = re.findall(r'https?://[^\s"\'<>]+\.png', unescaped)
                for p in raw_pngs:
                    clean_p = p.split("?")[0].lower()
                    if clean_p not in seen_urls and not any(skip in p.lower() for skip in self.BLACKLIST_DOMAINS):
                        seen_urls.add(clean_p)
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

