from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class IconResult:
    """Represents a single icon search result."""
    title: str
    image_url: str
    thumb_url: str
    source: str
    width: Optional[int] = 256
    height: Optional[int] = 256

class BaseProvider(ABC):
    """Abstract base class for icon search providers."""

    name: str = "base"
    display_name: str = "Base Provider"

    @abstractmethod
    def search(self, query: str, max_results: int = 30, page: int = 1) -> List[IconResult]:
        """Executes a search query with pagination and returns a list of icon results."""
        pass
