from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class OfferData:
    """Represents a single product offer from a source."""
    source: str
    title: str
    url: str
    item_price: float
    currency: str = "USD"
    in_stock: bool = True
    image_url: Optional[str] = None


class BaseAdapter(ABC):
    """Base class for all scraping adapters."""
    source_name: str
    base_url: str

    @abstractmethod
    def search(self, query: str, limit: int = 10, page: int = 1) -> List[OfferData]:
        """Search for products and return offers."""
        pass
