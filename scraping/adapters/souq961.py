import re
from typing import List, Optional
from urllib.parse import quote_plus, urljoin

import requests
from bs4 import BeautifulSoup

from .base import BaseAdapter, OfferData


_PRICE_RE = re.compile(r"(\d+(?:\.\d+)?)")


class Souq961Adapter(BaseAdapter):
    source_name = "961souq"
    base_url = "https://961souq.com"

    def search(self, query: str, limit: int = 10, page: int = 1) -> List[OfferData]:
        # Example: https://961souq.com/search?q=hp+victus&page=2
        search_url = f"{self.base_url}/search?q={quote_plus(query)}"
        if page and page > 1:
            search_url += f"&page={page}"

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept-Language": "en-US,en;q=0.9",
        }

        r = requests.get(search_url, headers=headers, timeout=25)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "lxml")

        offers: List[OfferData] = []

        cards = soup.select("a.search-result-card")
        for card in cards:
            title_el = card.select_one("h3.search-result-title")
            price_el = card.select_one("p.search-result-price")
            img_el = card.select_one("img.search-result-image")

            href = card.get("href")

            if not title_el or not price_el or not href:
                continue

            title = title_el.get_text(" ", strip=True)

            raw_price = price_el.get_text(" ", strip=True).replace(",", "")
            m = _PRICE_RE.search(raw_price)
            if not m:
                continue
            item_price = float(m.group(1))

            url = urljoin(self.base_url, href)

            image_url: Optional[str] = None
            if img_el and img_el.get("src"):
                image_url = img_el["src"]

            offers.append(
                OfferData(
                    source=self.source_name,
                    title=title,
                    url=url,
                    item_price=item_price,
                    currency="USD",
                    image_url=image_url,
                    in_stock=True,  # Search page doesn't show stock; default True for now
                )
            )

            if len(offers) >= limit:
                break

        return offers
