import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

from icon_changer.core.config import HISTORY_FILE

class HistoryManager:
    """Tracks previously customized folders, files, and shortcuts."""

    def __init__(self) -> None:
        self.history: List[Dict[str, Any]] = self.load()

    def load(self) -> List[Dict[str, Any]]:
        if not HISTORY_FILE.exists():
            return []
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def save(self) -> None:
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self.history, f, indent=2)
        except Exception as e:
            print(f"Error saving history: {e}")

    def add_entry(self, target_path: str, ico_path: str, title: str = "") -> None:
        """Adds or updates an entry in the history."""
        # Remove existing if present
        self.history = [h for h in self.history if h.get("target_path") != target_path]
        
        entry = {
            "target_path": target_path,
            "target_name": Path(target_path).name,
            "ico_path": ico_path,
            "title": title or Path(target_path).stem,
            "is_dir": Path(target_path).is_dir(),
            "timestamp": int(time.time()),
        }
        self.history.insert(0, entry)
        # Keep maximum 50 history entries
        self.history = self.history[:50]
        self.save()

    def remove_entry(self, target_path: str) -> None:
        self.history = [h for h in self.history if h.get("target_path") != target_path]
        self.save()

    def get_all(self) -> List[Dict[str, Any]]:
        return self.history

# Global singleton
history = HistoryManager()
