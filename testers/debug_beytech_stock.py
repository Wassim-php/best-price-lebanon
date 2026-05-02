"""
Debug script to check Beytech stock detection
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

# Search for PlayStation 5
query = "PlayStation 5"
search_url = f"https://www.beytech.com.lb/?s={quote_plus(query)}"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}

print(f"Fetching: {search_url}\n")
r = requests.get(search_url, headers=headers, timeout=25)
soup = BeautifulSoup(r.text, "html.parser")

# Get all product cards
product_cards = soup.select("article.product")
print(f"Found {len(product_cards)} product cards\n")

for i, card in enumerate(product_cards, 1):
    print(f"\n{'='*80}")
    print(f"CARD {i}")
    print(f"{'='*80}")
    
    # Extract title
    title_link = card.select_one("h2 a") or card.select_one("a")
    title = title_link.get_text(strip=True) if title_link else "No title"
    print(f"Title: {title}\n")
    
    # Check for out-of-stock-label
    out_of_stock_label = card.select_one(".out-of-stock-label")
    if out_of_stock_label:
        print(f"✗ OUT OF STOCK - Found .out-of-stock-label: {out_of_stock_label.get_text(strip=True)}\n")
    else:
        print(f"✓ IN STOCK - No .out-of-stock-label found\n")
    
    # Print the full card HTML for inspection
    print("Card HTML snippet:")
    card_html = str(card)[:1500]  # First 1500 chars
    print(card_html)
    print("\n")
