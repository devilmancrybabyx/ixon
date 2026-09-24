import os
import json
from pathlib import Path
from typing import Any, Dict

APP_NAME = "IconChanger"
APPDATA_DIR = Path(os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))) / APP_NAME
CONFIG_FILE = APPDATA_DIR / "config.json"
ICONS_DIR = APPDATA_DIR / "icons"
CACHE_DIR = APPDATA_DIR / "cache"
HISTORY_FILE = APPDATA_DIR / "history.json"

DEFAULT_CONFIG: Dict[str, Any] = {
    "search_suffix": "icon png",
    "search_template": "{name} {suffix}",
    "default_provider": "web",  # 'web', 'icons8', 'google_api'
    "google_api_key": "",
    "google_cx": "",
    "icon_resolution": 256,  # 16, 32, 48, 64, 128, 256, 'multi'
    "context_menu_label": "Change Icon",
    "theme": "dark",
    "max_results": 30,
    "store_in_folder": False,  # If true, save icon inside target folder instead of %LOCALAPPDATA%
    "run_as_admin": False,  # If true, run app and context menu with administrator permissions
}

class ConfigManager:
    """Manages application settings persisted in JSON."""
    
    def __init__(self) -> None:
        self._ensure_directories()
        self.config: Dict[str, Any] = self.load()

    def _ensure_directories(self) -> None:
        APPDATA_DIR.mkdir(parents=True, exist_ok=True)
        ICONS_DIR.mkdir(parents=True, exist_ok=True)
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def load(self) -> Dict[str, Any]:
        if not CONFIG_FILE.exists():
            self.save(DEFAULT_CONFIG)
            return dict(DEFAULT_CONFIG)
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Merge with defaults for any missing keys
                merged = dict(DEFAULT_CONFIG)
                merged.update(data)
                return merged
        except Exception:
            return dict(DEFAULT_CONFIG)

    def save(self, config_dict: Dict[str, Any]) -> None:
        self.config = config_dict
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config_dict, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, DEFAULT_CONFIG.get(key, default))

    def set(self, key: str, value: Any) -> None:
        self.config[key] = value
        self.save(self.config)

    def build_search_query(self, target_name: str, custom_suffix: str = "") -> str:
        """Builds search query based on template and suffix."""
        suffix = custom_suffix if custom_suffix else self.get("search_suffix", "icon png")
        template = self.get("search_template", "{name} {suffix}")
        return template.format(name=target_name, suffix=suffix).strip()

# Global singleton
config = ConfigManager()
