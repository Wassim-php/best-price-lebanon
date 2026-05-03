from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict, Any


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
    # Additional pricing details (populated by get_detailed_pricing)
    shipping_fee: Optional[float] = None
    tax_amount: Optional[float] = None
    total_price: Optional[float] = None
    pricing_details: Optional[Dict[str, Any]] = None


class BaseAdapter(ABC):
    """Base class for all scraping adapters.

    Each website adapter must normalize its search results into OfferData.
    Detailed pricing is optional and implemented per adapter when supported.
    """
    source_name: str
    base_url: str

    @abstractmethod
    def search(self, query: str, limit: int = 10, page: int = 1) -> List[OfferData]:
        """Search for products and return offers."""
        pass
