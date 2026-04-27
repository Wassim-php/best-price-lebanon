"""
Ishtari Adapter
Handles product search and pricing from ishtari.com

Notes:
- Ishtari search is heavily client-rendered and may change frequently.
- This adapter uses multiple extraction strategies and falls back gracefully.
"""

import json
import logging
import os
import re
from html import unescape
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

from ..base import BaseAdapter, OfferData

logger = logging.getLogger(__name__)


class IshtariAdapter(BaseAdapter):
	"""Adapter for Ishtari e-commerce site."""

	source_name = "Ishtari"
	BASE_URL = "https://www.ishtari.com"
	SEARCH_URL = f"{BASE_URL}/search?keyword={{}}"
	MOBILE_API_BASE_URL = "https://www.ishtari-mobile.com/v2/index.php"
	SEARCH_DISCOVERY_API = MOBILE_API_BASE_URL + "?route=catalog/search&key={}&use_ai_search"
	PRODUCT_DETAILS_API = MOBILE_API_BASE_URL + "?route=catalog/product&product_id={}"
	DEFAULT_API_TOKEN = "3bb3136a33e50eb6cd4f00c08a0e8761aa0d0933"

	# Store metadata for comparisons scoring
	STORE_RATING = 4.1
	DELIVERY_DAYS = 4

	# Shipping assumptions (can be tuned later if better data becomes available)
	SHIPPING_INSIDE_BEIRUT = 3.0
	SHIPPING_OUTSIDE_BEIRUT = 5.0
	DELIVERY_INSIDE_BEIRUT = "2-4 business days"
	DELIVERY_OUTSIDE_BEIRUT = "3-6 business days"

	_PRICE_RE = re.compile(r"(\d+(?:,\d{3})*(?:\.\d+)?)")
	_STOP_WORDS = {
		"for", "with", "and", "the", "from", "into", "over", "under", "in", "on", "at", "to", "air"
	}

	def __init__(self):
		self.session = requests.Session()
		self.session.headers.update({
			"User-Agent": (
				"Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
				"AppleWebKit/537.36 (KHTML, like Gecko) "
				"Chrome/124.0.0.0 Safari/537.36"
			),
			"Accept-Language": "en-US,en;q=0.9",
		})

	def search(self, query: str, limit: int = 10, page: int = 1) -> List[OfferData]:
		"""
		Search for products on Ishtari.

		Strategy order:
		1) Ishtari API flow used by the web app.
		2) Search page JSON extraction from __NEXT_DATA__.
		3) Search page with alternate query parameter (q).
		4) Homepage widgets JSON extraction as fallback.
		"""
		query = (query or "").strip()
		if not query:
			return []

		candidates: List[Dict[str, Any]] = []

		try:
			candidates = self._search_from_api(query=query, page=page, limit=limit)
		except Exception as e:
			logger.warning(f"Ishtari API search strategy failed: {e}")

		try:
			if not candidates:
				candidates = self._search_from_search_page(query=query, page=page)
		except Exception as e:
			logger.warning(f"Ishtari search-page strategy failed: {e}")

		if not candidates:
			try:
				candidates = self._search_from_search_page_alt(query=query, page=page)
			except Exception as e:
				logger.warning(f"Ishtari alt search-page strategy failed: {e}")

		if not candidates:
			try:
				candidates = self._search_from_home_widgets(query=query)
			except Exception as e:
				logger.warning(f"Ishtari home-widget fallback failed: {e}")

		offers = self._build_offers_from_candidates(candidates, query=query)
		return offers[:limit] if limit else offers

	def get_detailed_pricing(self, product_url: str, location: str = "outside beirut") -> Dict[str, Any]:
		"""
		Get detailed pricing for an Ishtari product page.

		Uses Ishtari API where possible and falls back to page parsing.
		"""
		try:
			product_id = self._extract_product_id_from_url(product_url)
			if product_id is not None:
				api_details = self._get_product_details_from_api(product_id=product_id, product_url=product_url, location=location)
				if api_details:
					return api_details

			response = self.session.get(product_url, timeout=20)
			response.raise_for_status()

			soup = BeautifulSoup(response.text, "lxml")
			next_data = self._extract_next_data(soup)

			item_price = 0.0
			title = "Unknown Product"
			in_stock = True

			if isinstance(next_data, dict):
				page_props = (
					next_data.get("props", {})
					.get("pageProps", {})
				)

				# On Ishtari product pages, these are frequently present and reliable.
				item_price = (
					self._to_float(page_props.get("special"))
					or self._to_float(page_props.get("price"))
					or 0.0
				)

				# Attempt title from nested fields first.
				title = (
					self._first_non_empty([
						page_props.get("name"),
						self._extract_nested_name(page_props.get("data")),
						self._extract_nested_name(page_props.get("products_one_data")),
						self._extract_nested_name(page_props.get("products_data")),
					])
					or title
				)

				qty = self._extract_nested_quantity(page_props.get("data"))
				if qty is not None:
					in_stock = qty > 0

			# HTML fallback for title
			if title == "Unknown Product":
				title_tag = soup.find("title")
				if title_tag:
					title = title_tag.get_text(" ", strip=True)

			if item_price <= 0:
				# Last-resort fallback: extract first price-like token from page text.
				text_price = self._extract_price_from_text(soup.get_text(" ", strip=True))
				if text_price is not None:
					item_price = text_price

			location_lower = (location or "outside beirut").strip().lower()
			if "inside" in location_lower or location_lower == "beirut":
				shipping_fee = self.SHIPPING_INSIDE_BEIRUT
				delivery_time = self.DELIVERY_INSIDE_BEIRUT
			else:
				shipping_fee = self.SHIPPING_OUTSIDE_BEIRUT
				delivery_time = self.DELIVERY_OUTSIDE_BEIRUT

			total_price = item_price + shipping_fee

			return {
				"item_price": item_price,
				"shipping_fee": shipping_fee,
				"tax_amount": 0.0,
				"total_price": total_price,
				"currency": "USD",
				"delivery_time": delivery_time,
				"breakdown": {
					"title": title,
					"in_stock": in_stock,
					"url": product_url,
					"note": (
						"Shipping/time are estimated defaults for Ishtari and can be adjusted "
						"when more precise logistics rules are available."
					),
				},
			}

		except Exception as e:
			logger.error(f"Error getting Ishtari product details: {e}")
			return {
				"item_price": 0.0,
				"shipping_fee": self.SHIPPING_OUTSIDE_BEIRUT,
				"tax_amount": 0.0,
				"total_price": self.SHIPPING_OUTSIDE_BEIRUT,
				"currency": "USD",
				"delivery_time": self.DELIVERY_OUTSIDE_BEIRUT,
				"breakdown": {"error": str(e)},
			}

	def get_source_name(self) -> str:
		return self.source_name

	def _search_from_api(self, query: str, page: int = 1, limit: int = 10) -> List[Dict[str, Any]]:
		"""Use Ishtari's own API flow (discovery -> node search)."""
		api_query = quote_plus(query)
		discovery_url = self.SEARCH_DISCOVERY_API.format(api_query)
		discovery_payload = {
			"page": max(1, int(page or 1)),
			"limit": max(50, int(limit or 10)),
			"source_id": 1,
			"user_id": "",
		}

		discovery_data = self._api_request_json(
			method="POST",
			url=discovery_url,
			json_body=discovery_payload,
		)
		if not isinstance(discovery_data, dict):
			return []

		node_url = ((discovery_data.get("data") or {}).get("node_url") or "").strip()
		if not node_url:
			return []

		node_endpoint = f"https://{node_url}{quote_plus(query)}"
		node_payload = {
			"sort": "",
			"source_id": 1,
			"user_id": "",
		}
		node_data = self._api_request_json(
			method="POST",
			url=node_endpoint,
			json_body=node_payload,
		)
		if not isinstance(node_data, dict):
			return []

		products = (node_data.get("data") or {}).get("products") or []
		if not isinstance(products, list):
			return []

		return [p for p in products if isinstance(p, dict)]

	def _get_product_details_from_api(self, product_id: int, product_url: str, location: str) -> Optional[Dict[str, Any]]:
		url = self.PRODUCT_DETAILS_API.format(product_id)
		data = self._api_request_json(method="GET", url=url)
		if not isinstance(data, dict):
			return None

		product_data = data.get("data") or {}
		if not isinstance(product_data, dict):
			return None

		item_price = (
			self._to_float(product_data.get("special"))
			or self._to_float(product_data.get("price"))
			or self._to_float(product_data.get("special_net_value"))
			or self._to_float(product_data.get("price_net_value"))
			or 0.0
		)

		title = self._first_non_empty([
			product_data.get("name"),
			product_data.get("heading_title"),
		]) or "Unknown Product"

		qty = self._to_float(product_data.get("quantity"))
		in_stock = qty is None or qty > 0

		location_lower = (location or "outside beirut").strip().lower()
		if "inside" in location_lower or location_lower == "beirut":
			shipping_fee = self.SHIPPING_INSIDE_BEIRUT
			delivery_time = self.DELIVERY_INSIDE_BEIRUT
		else:
			shipping_fee = self.SHIPPING_OUTSIDE_BEIRUT
			delivery_time = self.DELIVERY_OUTSIDE_BEIRUT

		total_price = item_price + shipping_fee

		canonical_url = (
			self._normalize_url(product_data.get("product_link"))
			or product_url
			or f"{self.BASE_URL}/product/{product_id}"
		)

		return {
			"item_price": item_price,
			"shipping_fee": shipping_fee,
			"tax_amount": 0.0,
			"total_price": total_price,
			"currency": "USD",
			"delivery_time": delivery_time,
			"breakdown": {
				"title": title,
				"in_stock": in_stock,
				"url": canonical_url,
				"source": "ishtari_api",
				"note": "Price data fetched from Ishtari API.",
			},
		}

	def _api_request_json(self, method: str, url: str, json_body: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
		response = self.session.request(
			method=method,
			url=url,
			headers=self._api_headers(),
			json=json_body,
			timeout=20,
		)
		response.raise_for_status()
		try:
			return response.json()
		except ValueError:
			return None

	def _api_headers(self) -> Dict[str, str]:
		token = os.environ.get("ISHTARI_API_TOKEN", self.DEFAULT_API_TOKEN).strip()
		headers = {
			"Accept": "application/json, text/plain, */*",
			"Content-Type": "application/json",
			"Referer": f"{self.BASE_URL}/",
		}
		if token:
			headers["Authorization"] = f"Bearer {token}"
		return headers

	def _extract_product_id_from_url(self, product_url: str) -> Optional[int]:
		if not product_url:
			return None

		patterns = [
			r"/product/(\d+)",
			r"[?&]product_id=(\d+)",
			r"[?&]p=(\d+)",
			r"/p=(\d+)",
		]

		for pattern in patterns:
			m = re.search(pattern, product_url)
			if not m:
				continue
			try:
				return int(m.group(1))
			except (TypeError, ValueError):
				continue

		return None

	def _normalize_url(self, url: Any) -> Optional[str]:
		if not isinstance(url, str):
			return None

		url = url.strip()
		if not url:
			return None

		if url.startswith("http"):
			return url
		if url.startswith("//"):
			return "https:" + url
		if url.startswith("/"):
			return f"{self.BASE_URL}{url}"
		return f"{self.BASE_URL}/{url}"

	def _search_from_search_page(self, query: str, page: int = 1) -> List[Dict[str, Any]]:
		url = self.SEARCH_URL.format(quote_plus(query))
		if page and page > 1:
			url = f"{url}&page={page}"

		response = self.session.get(url, timeout=20)
		response.raise_for_status()
		soup = BeautifulSoup(response.text, "lxml")

		next_data = self._extract_next_data(soup)
		if not next_data:
			return []

		return self._extract_product_dicts(next_data)

	def _search_from_search_page_alt(self, query: str, page: int = 1) -> List[Dict[str, Any]]:
		# Alternate parameter style seen in Ishtari search URLs.
		url = f"{self.BASE_URL}/search?q={quote_plus(query)}"
		if page and page > 1:
			url = f"{url}&page={page}"

		response = self.session.get(url, timeout=20)
		response.raise_for_status()
		soup = BeautifulSoup(response.text, "lxml")

		next_data = self._extract_next_data(soup)
		if not next_data:
			return []

		return self._extract_product_dicts(next_data)

	def _search_from_home_widgets(self, query: str) -> List[Dict[str, Any]]:
		response = self.session.get(self.BASE_URL, timeout=20)
		response.raise_for_status()
		soup = BeautifulSoup(response.text, "lxml")

		next_data = self._extract_next_data(soup)
		if not next_data:
			return []

		# Homepage typically includes many widget items under pageProps.data.
		products = self._extract_product_dicts(next_data)
		return self._filter_candidates_by_query(products, query)

	def _build_offers_from_candidates(self, candidates: List[Dict[str, Any]], query: str) -> List[OfferData]:
		candidates = self._filter_candidates_by_query(candidates, query)

		ranked = sorted(candidates, key=lambda c: self._query_match_score(c, query), reverse=True)

		seen = set()
		offers: List[OfferData] = []
		for item in ranked:
			product_id = item.get("product_id")
			title = self._candidate_title(item)
			if not title:
				continue

			unique_key = str(product_id or title.lower())
			if unique_key in seen:
				continue
			seen.add(unique_key)

			price = self._to_float(item.get("special")) or self._to_float(item.get("price"))
			if price is None:
				continue

			url = self._build_product_url(item)
			if not url:
				continue

			qty = self._to_float(item.get("quantity"))
			in_stock = qty is None or qty > 0

			image_url = item.get("thumb") or item.get("image") or item.get("image_url")
			if isinstance(image_url, str) and image_url.startswith("//"):
				image_url = "https:" + image_url

			offers.append(
				OfferData(
					source=self.source_name,
					title=title,
					url=url,
					item_price=float(price),
					currency="USD",
					in_stock=in_stock,
					image_url=image_url,
				)
			)

		return offers

	def _extract_next_data(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
		script_tag = soup.find("script", id="__NEXT_DATA__", type="application/json")
		if not script_tag:
			return None
		try:
			return json.loads(script_tag.string or "{}")
		except json.JSONDecodeError:
			return None

	def _extract_product_dicts(self, node: Any) -> List[Dict[str, Any]]:
		"""Recursively collect product-like dictionaries from nested JSON."""
		results: List[Dict[str, Any]] = []

		def walk(x: Any):
			if isinstance(x, dict):
				has_product_shape = (
					("product_id" in x or "sku" in x)
					and ("name" in x)
					and ("price" in x or "special" in x)
				)
				if has_product_shape:
					results.append(x)
				for value in x.values():
					walk(value)
			elif isinstance(x, list):
				for item in x:
					walk(item)

		walk(node)
		return results

	def _filter_candidates_by_query(self, candidates: Iterable[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
		raw_query = (query or "").strip().lower()
		terms = re.findall(r"[a-z0-9]+", raw_query)
		if not terms:
			return list(candidates)

		# Keep meaningful non-numeric terms and ignore very common glue words.
		significant_terms = [
			t for t in terms
			if not t.isdigit() and len(t) >= 3 and t not in self._STOP_WORDS
		]
		if not significant_terms:
			significant_terms = [t for t in terms if not t.isdigit()]
		if not significant_terms:
			significant_terms = terms

		# Phase 1: strict-ish matching (phrase or all significant terms as whole words).
		strict: List[Dict[str, Any]] = []
		for item in candidates:
			text = self._candidate_title(item).lower()
			if not text:
				continue
			if raw_query and raw_query in text:
				strict.append(item)
				continue
			if all(self._contains_word(text, term) for term in significant_terms):
				strict.append(item)

		# If strict pass already has enough products, keep precision high.
		if len(strict) >= 3:
			return strict

		# Phase 2: relaxed matching (any significant term as whole word).
		filtered = []
		for item in candidates:
			text = self._candidate_title(item).lower()
			if any(self._contains_word(text, term) for term in significant_terms):
				filtered.append(item)

		return filtered

	def _query_match_score(self, item: Dict[str, Any], query: str) -> int:
		text = self._candidate_title(item).lower()
		raw_query = (query or "").strip().lower()
		terms = [
			t for t in re.findall(r"[a-z0-9]+", raw_query)
			if not t.isdigit() and t not in self._STOP_WORDS
		]
		if not terms:
			return 0

		score = 0
		if raw_query and raw_query in text:
			score += 6

		for term in terms:
			if self._contains_word(text, term):
				score += 3

		if raw_query and text.startswith(raw_query):
			score += 2

		return score

	def _candidate_title(self, item: Dict[str, Any]) -> str:
		"""Prefer full API title over shortened display title."""
		title = self._first_non_empty([
			item.get("full_name"),
			item.get("name"),
			item.get("heading_title"),
		])
		if not title:
			return ""

		title = unescape(title)
		title = re.sub(r"\s+", " ", title).strip()
		return title

	def _contains_word(self, text: str, term: str) -> bool:
		return bool(re.search(rf"\b{re.escape(term)}\b", text))

	def _build_product_url(self, item: Dict[str, Any]) -> Optional[str]:
		# Ishtari product pages reliably resolve with /product/{product_id}
		product_id = item.get("product_id")
		if product_id:
			return f"{self.BASE_URL}/product/{product_id}"

		direct_url = item.get("url") or item.get("href")
		if isinstance(direct_url, str) and direct_url.strip():
			if direct_url.startswith("http"):
				return direct_url
			if direct_url.startswith("/"):
				return f"{self.BASE_URL}{direct_url}"
			return f"{self.BASE_URL}/{direct_url}"

		return None

	def _to_float(self, value: Any) -> Optional[float]:
		if value is None:
			return None
		if isinstance(value, (int, float)):
			return float(value)
		if isinstance(value, str):
			m = self._PRICE_RE.search(value)
			if not m:
				return None
			try:
				return float(m.group(1).replace(",", ""))
			except ValueError:
				return None
		return None

	def _extract_price_from_text(self, text: str) -> Optional[float]:
		if not text:
			return None
		m = self._PRICE_RE.search(text)
		if not m:
			return None
		try:
			return float(m.group(1).replace(",", ""))
		except ValueError:
			return None

	def _extract_nested_name(self, value: Any) -> Optional[str]:
		if isinstance(value, dict):
			name = value.get("name")
			if isinstance(name, str) and name.strip():
				return name.strip()
		if isinstance(value, list) and value:
			for item in value:
				if isinstance(item, dict):
					name = item.get("name")
					if isinstance(name, str) and name.strip():
						return name.strip()
		return None

	def _extract_nested_quantity(self, value: Any) -> Optional[float]:
		if isinstance(value, dict):
			return self._to_float(value.get("quantity"))
		if isinstance(value, list):
			for item in value:
				if isinstance(item, dict):
					qty = self._to_float(item.get("quantity"))
					if qty is not None:
						return qty
		return None

	def _first_non_empty(self, values: List[Optional[str]]) -> Optional[str]:
		for v in values:
			if isinstance(v, str) and v.strip():
				return v.strip()
		return None
