import io
import os
import hashlib
from pathlib import Path
from typing import List, Tuple, Union, Optional
import requests
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

    @staticmethod
    def get_cache_path(url: str) -> Path:
        """Returns local cached path for a URL."""
        url_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()
        return CACHE_DIR / f"{url_hash}.png"

    @classmethod
    def download_image(cls, url: str, timeout: int = 15) -> bytes:
        """Downloads image bytes from URL with caching."""
        cache_path = cls.get_cache_path(url)
        if cache_path.exists() and cache_path.stat().st_size > 0:
            try:
                with open(cache_path, "rb") as f:
                    return f.read()
            except Exception:
                pass

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        }
        resp = requests.get(url, headers=headers, timeout=timeout)
        resp.raise_for_status()
        data = resp.content

        # Save to cache
        try:
            with open(cache_path, "wb") as f:
                f.write(data)
        except Exception:
            pass

        return data

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
        
        :param image_input: Raw image bytes, or path to local image file.
        :param output_ico_path: Destination path for .ico file.
        :param resolution: Target size (e.g. 256, 128, 96, 64, 48, 32, 16) or 'multi'.
        :return: Path to generated .ico file.
        """
        output_ico_path = Path(output_ico_path)
        output_ico_path.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(image_input, Image.Image):
            img = image_input
        elif isinstance(image_input, (str, Path)):
            img = Image.open(str(image_input))
        else:
            img = Image.open(io.BytesIO(image_input))

        # Ensure image is in RGBA mode for transparency preservation
        if img.mode != "RGBA":
            img = img.convert("RGBA")

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
