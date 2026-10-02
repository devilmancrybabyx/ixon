import io
import os
import hashlib
from pathlib import Path
from typing import List, Tuple, Union, Optional
import requests
from requests.adapters import HTTPAdapter
from PIL import Image

from icon_changer.core.config import CACHE_DIR, ICONS_DIR

# Standard Windows icon sizes for multi-resolution ICO (Windows 10/11)
STANDARD_ICO_SIZES: List[Tuple[int, int]] = [
    (16, 16),
    (24, 24),
    (32, 32),
    (48, 48),
    (64, 64),
    (96, 96),
    (128, 128),
    (256, 256),
]

class IconEngine:
    """Handles image downloading, caching, format conversion, and ICO generation."""
    _session: Optional[requests.Session] = None
    _mem_cache: dict = {}

    @classmethod
    def get_session(cls) -> requests.Session:
        if cls._session is None:
            cls._session = requests.Session()
            adapter = HTTPAdapter(
                pool_connections=40,
                pool_maxsize=40,
                max_retries=0
            )
            cls._session.mount("https://", adapter)
            cls._session.mount("http://", adapter)
        return cls._session

    @staticmethod
    def get_cache_path(url: str) -> Path:
        """Returns local cached path for a URL."""
        url_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()
        return CACHE_DIR / f"{url_hash}.png"

    @classmethod
    def get_cached_image(cls, url: str) -> Optional[bytes]:
        """Returns cached image bytes immediately without network call if present in RAM or disk."""
        if url in cls._mem_cache:
            return cls._mem_cache[url]
        try:
            cache_path = cls.get_cache_path(url)
            if cache_path.exists() and cache_path.stat().st_size > 0:
                with open(cache_path, "rb") as f:
                    data = f.read()
                    if data:
                        cls._mem_cache[url] = data
                        return data
        except Exception:
            pass
        return None

    @classmethod
    def download_image(cls, url: str, timeout: Union[int, float, Tuple[float, float]] = (2.5, 4.0)) -> bytes:
        """Downloads image bytes from URL with RAM/disk caching and connection pooling."""
        # 1. Check RAM and disk cache first
        cached = cls.get_cached_image(url)
        if cached:
            return cached

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        }
        session = cls.get_session()
        resp = session.get(url, headers=headers, timeout=timeout)
        resp.raise_for_status()
        data = resp.content

        # Save to memory and disk cache
        cls._mem_cache[url] = data
        try:
            cache_path = cls.get_cache_path(url)
            with open(cache_path, "wb") as f:
                f.write(data)
        except Exception:
            pass

        return data

    @classmethod
    def extract_file_icon_bytes(cls, path_str: str) -> Optional[bytes]:
        """Extracts high-resolution 256x256 icon from .exe, .dll, or .lnk as PNG bytes."""
        try:
            from PyQt5 import QtWidgets, QtCore
            info = QtCore.QFileInfo(path_str)
            icon = QtWidgets.QFileIconProvider().icon(info)
            pm = icon.pixmap(256, 256)
            if not pm.isNull():
                buf = QtCore.QBuffer()
                buf.open(QtCore.QIODevice.WriteOnly)
                pm.save(buf, "PNG")
                return bytes(buf.data())
        except Exception as e:
            print(f"Error extracting icon from file: {e}")
        return None

    @staticmethod
    def ensure_transparent_background(img: Image.Image, tolerance: int = 40) -> Image.Image:
        """
        Ensures an icon image has a pristine transparent background without ugly white outlines, halos, or fringes.
        - Automatically removes outer white/near-white backgrounds via border floodfills.
        - Vectorized defringing eliminates semi-transparent white anti-aliasing halos and edge fringes.
        - Un-mattes semi-transparent edge pixels against white canvas to restore true crisp edge colors.
        - Preserves white elements inside monochrome glyphs and logos.
        """
        if img.mode != "RGBA":
            img = img.convert("RGBA")
        try:
            from PIL import ImageDraw, ImageFilter
            w, h = img.size
            if w <= 2 or h <= 2:
                return img

            alpha_extrema = img.getextrema()[3]
            corners = [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]
            is_near_white = lambda p: (p[0] >= 225 and p[1] >= 225 and p[2] >= 225)
            had_white_bg = False

            # If image was completely opaque with white corners, floodfill the background from perimeter
            if alpha_extrema[0] >= 240 and any(is_near_white(img.getpixel(pt)) for pt in corners):
                had_white_bg = True
                if w <= 160 and h <= 160:
                    for pt in corners + [(w // 2, 0), (w // 2, h - 1), (0, h // 2), (w - 1, h // 2)]:
                        try:
                            p = img.getpixel(pt)
                            if is_near_white(p):
                                ImageDraw.floodfill(img, pt, (0, 0, 0, 0), thresh=tolerance)
                        except Exception:
                            pass
                else:
                    # Ultra-fast mask method for large images (downscale mask -> floodfill -> resize mask)
                    mw, mh = min(160, w), min(160, h)
                    small = img.resize((mw, mh), Image.Resampling.BOX)
                    for pt in [(0, 0), (mw - 1, 0), (0, mh - 1), (mw - 1, mh - 1), (mw // 2, 0), (mw // 2, mh - 1), (0, mh // 2), (mw - 1, mh // 2)]:
                        try:
                            p = small.getpixel(pt)
                            if is_near_white(p):
                                ImageDraw.floodfill(small, pt, (0, 0, 0, 0), thresh=tolerance)
                        except Exception:
                            pass
                    alpha_small = small.split()[3].filter(ImageFilter.MinFilter(3))
                    alpha_full = alpha_small.resize((w, h), Image.Resampling.BILINEAR)
                    img.putalpha(alpha_full)

            # High-performance edge defringing & un-matting
            try:
                import numpy as np
                arr = np.array(img)
                alpha_chan = arr[:, :, 3]

                # Only proceed if image has transparency
                if alpha_chan.min() < 250:
                    opaque_mask = alpha_chan > 128
                    is_white_glyph = False
                    if np.any(opaque_mask):
                        op_r = arr[:, :, 0][opaque_mask]
                        op_g = arr[:, :, 1][opaque_mask]
                        op_b = arr[:, :, 2][opaque_mask]
                        # If more than 80% of opaque pixels are near-white, it's an intended white silhouette
                        if np.mean((op_r > 210) & (op_g > 210) & (op_b > 210)) > 0.80:
                            is_white_glyph = True

                    # Run 2 passes of defringing on non-white glyphs or floodfilled backgrounds
                    if not is_white_glyph or had_white_bg:
                        for _ in range(2):
                            alpha_pil = Image.fromarray(arr[:, :, 3])
                            # MinFilter(3) expands transparent regions into adjacent edge pixels
                            eroded_alpha = np.array(alpha_pil.filter(ImageFilter.MinFilter(3)))
                            edge_mask = (arr[:, :, 3] > 0) & (eroded_alpha == 0)

                            r = arr[:, :, 0]
                            g = arr[:, :, 1]
                            b = arr[:, :, 2]
                            a = arr[:, :, 3]

                            # Outer white/light halo pixels
                            white_halo = edge_mask & (r > 185) & (g > 185) & (b > 185)
                            arr[white_halo, 3] = 0

                            # Un-matte semi-transparent edge pixels against white canvas
                            semi_edge = edge_mask & (a < 240) & (arr[:, :, 3] > 0)
                            if np.any(semi_edge):
                                af = a[semi_edge].astype(float) / 255.0
                                rf = np.clip((r[semi_edge] - (1.0 - af) * 255.0) / np.maximum(af, 0.05), 0, 255).astype(np.uint8)
                                gf = np.clip((g[semi_edge] - (1.0 - af) * 255.0) / np.maximum(af, 0.05), 0, 255).astype(np.uint8)
                                bf = np.clip((b[semi_edge] - (1.0 - af) * 255.0) / np.maximum(af, 0.05), 0, 255).astype(np.uint8)
                                arr[semi_edge, 0] = rf
                                arr[semi_edge, 1] = gf
                                arr[semi_edge, 2] = bf

                        img = Image.fromarray(arr)

            except ImportError:
                # Pure PIL fallback defringing
                if img.getextrema()[3][0] < 250:
                    raw_pixels = list(img.getdata())
                    cleaned_pixels = [
                        (r, g, b, 0 if (a < 240 and r > 195 and g > 195 and b > 195) else a)
                        for (r, g, b, a) in raw_pixels
                    ]
                    img.putdata(cleaned_pixels)

        except Exception:
            pass
        return img

    @classmethod
    def convert_to_ico(
        cls,
        image_input: Union[bytes, str, Path],
        output_ico_path: Union[str, Path],
        resolution: Union[int, str] = 256
    ) -> Path:
        """
        Converts image bytes or file to Windows ICO format with alpha transparency.
        Always prepares a high-resolution canvas with aspect-ratio preservation
        so that Windows Explorer views (up to Extra Large 256x256) are never downsized.
        Handles .exe, .dll, and .lnk files by extracting their high-res icon resources.
        
        :param image_input: Raw image bytes, or path to local image/exe/lnk file.
        :param output_ico_path: Destination path for .ico file.
        :param resolution: Target size (e.g. 256, 128, 96, 64, 48, 32, 16) or 'multi'.
        :return: Path to generated .ico file.
        """
        output_ico_path = Path(output_ico_path)
        output_ico_path.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(image_input, Image.Image):
            img = image_input
        elif isinstance(image_input, (str, Path)):
            p = Path(image_input)
            if p.suffix.lower() in (".exe", ".dll", ".lnk", ".ocx"):
                extracted = cls.extract_file_icon_bytes(str(p))
                if extracted:
                    img = Image.open(io.BytesIO(extracted))
                else:
                    raise ValueError(f"Could not extract icon from {p.name}")
            else:
                img = Image.open(str(image_input))
        else:
            img = Image.open(io.BytesIO(image_input))

        # Ensure image is in RGBA mode for transparency preservation
        if img.mode != "RGBA":
            img = img.convert("RGBA")

        # Auto-remove outer white box background if present
        img = cls.ensure_transparent_background(img)

        # Determine sizes to include in ICO
        if resolution == "multi" or str(resolution).lower() == "multi":
            sizes = STANDARD_ICO_SIZES
        else:
            try:
                size_int = int(resolution)
                if size_int <= 0:
                    size_int = 256
                # Recommended practice: Include target size plus smaller standard sizes
                # for clean rendering across all Windows Explorer view modes
                sub_sizes = [s for s in STANDARD_ICO_SIZES if s[0] <= size_int]
                if not sub_sizes or (size_int, size_int) not in sub_sizes:
                    sub_sizes.append((size_int, size_int))
                sizes = sorted(sub_sizes, key=lambda s: s[0])
            except (ValueError, TypeError):
                sizes = STANDARD_ICO_SIZES

        # Maximum dimension required for the ICO
        max_dim = max(s[0] for s in sizes)

        # High-quality aspect-ratio preserving fit onto square transparent canvas
        orig_w, orig_h = img.size
        scale = min(max_dim / orig_w, max_dim / orig_h)
        new_w = max(1, int(round(orig_w * scale)))
        new_h = max(1, int(round(orig_h * scale)))

        # Resample with Lanczos for maximum sharpness and clarity
        resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

        canvas = Image.new("RGBA", (max_dim, max_dim), (0, 0, 0, 0))
        offset_x = (max_dim - new_w) // 2
        offset_y = (max_dim - new_h) // 2
        canvas.paste(resized, (offset_x, offset_y))

        # Save as multi-resolution ICO with all requested sizes
        canvas.save(
            str(output_ico_path),
            format="ICO",
            sizes=sizes
        )
        return output_ico_path

    @classmethod
    def create_icon_for_target(
        cls,
        image_data: Union[bytes, str],
        target_name: str,
        resolution: Union[int, str] = 256,
        dest_dir: Optional[Path] = None
    ) -> Path:
        """
        Downloads/converts image and saves .ico with a unique filename for the target.
        """
        clean_name = "".join(c for c in target_name if c.isalnum() or c in (" ", "_", "-")).strip()
        if not clean_name:
            clean_name = "icon"
        
        target_dir = dest_dir if dest_dir else ICONS_DIR
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique hash for this icon
        if isinstance(image_data, bytes):
            data_hash = hashlib.md5(image_data).hexdigest()[:8]
        else:
            data_hash = hashlib.md5(image_data.encode("utf-8")).hexdigest()[:8]

        ico_filename = f"{clean_name}_{data_hash}.ico"
        ico_path = target_dir / ico_filename

        if isinstance(image_data, str) and (image_data.startswith("http://") or image_data.startswith("https://")):
            raw_bytes = cls.download_image(image_data)
            return cls.convert_to_ico(raw_bytes, ico_path, resolution=resolution)
        elif isinstance(image_data, str) and Path(image_data).exists():
            return cls.convert_to_ico(image_data, ico_path, resolution=resolution)
        elif isinstance(image_data, bytes):
            return cls.convert_to_ico(image_data, ico_path, resolution=resolution)
        else:
            raise ValueError("Invalid image data provided")
