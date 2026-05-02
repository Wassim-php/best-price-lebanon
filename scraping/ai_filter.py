"""
AI-powered product filtering using Google Gemini.
This service intelligently filters products to match user query intent.
"""
from typing import List, Dict
import json
from django.conf import settings
import google.generativeai as genai

class AIQuotaExceededError(Exception):
    """Raised when Gemini API quota is exceeded"""
    pass

class AIProductFilter:
    """
    Uses Gemini AI to filter products based on semantic understanding of user intent.
    For example, if query is "iPhone 15", it will filter out:
    - Cases, covers, and accessories
    - iPhone 15 Pro/Pro Max variants
    - Other iPhone models
    """
    
    def __init__(self):
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY not set. Please set it in your environment variables."
            )
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
    
    def filter_products(self, query: str, products: List[Dict]) -> List[int]:
        """
        Filter products using AI to match query intent.
        
        Args:
            query: User's search query (e.g., "iPhone 15")
            products: List of product dictionaries with 'title' and 'item_price'
        
        Returns:
            List of indices (0-based) of products that match the intent
        """
        if not products:
            return []
        
        # Build the product list for the AI prompt
        product_list = []
        for i, product in enumerate(products):
            title = product.get('title', 'Unknown')
            price = product.get('item_price', 0)
            product_list.append(f"{i + 1}. {title} - ${price}")
        
        products_text = "\n".join(product_list)
        
        # Create the AI prompt
        prompt = f"""You are a product matching assistant for an ecommerce price comparison app.

Your job is to select the products from the list that match the user's search intent.

User Query: "{query}"

Available Products:
{products_text}

Rules:
- Use only the provided product list. Do not reject a product because you are unsure whether it exists in the real world.
- Select only products that represent the same product type, model, generation, and requested variant as the query.
- If the query asks for a base product, exclude upgraded/different variants unless the query includes that variant.
- If the query includes a variant word, require that variant and exclude different variants.
- Exclude accessories, parts, cases, covers, chargers, cables, screen protectors, sleeves, keyboards, adapters, and bundles when the query is for the main device/product.
- If the query itself asks for an accessory, part, case, cover, charger, cable, screen protector, sleeve, keyboard, adapter, or bundle, then match that accessory type and exclude the main device/product.
- Exclude unrelated brands, incompatible models, different generations, and different storage/capacity/color variants only when the query explicitly specifies those details.
- If multiple products match the query intent, return all matching products.
- If no product matches the query intent, return an empty list.

Examples:
- Query "playstation 5" matches "Sony PS5 Slim Console", "PS5 Console", "PlayStation 5 Console" (naming variations).
- Query "playstation 5" does not match "PlayStation 5 EA Sports FC 26", "PS5 Controller", or "PS5 Disc Drive".
- Query "iphone 17" matches "Apple iPhone 17".
- Query "iphone 17" does not match "Apple iPhone 17 Pro", "Apple iPhone 17 Pro Max", or "Apple iPhone 17 Silicone Case".
- Query "iphone 17 pro" matches "Apple iPhone 17 Pro", but not "Apple iPhone 17", "Apple iPhone 17 Pro Max", or a case.
- Query "iphone 17 pro max" matches "Apple iPhone 17 Pro Max", but not "Apple iPhone 17 Pro".
- Query "iphone 17 case" matches "Apple iPhone 17 Silicone Case", but not "Apple iPhone 17".
- Query "macbook charger" matches a MacBook charger, but not a MacBook laptop.
- Query "ps5 controller" matches a PS5 controller, but not a PS5 console or controller case.

Return only a JSON object with this shape:
{{"selected_indices": [1, 3, 5]}}

The indices must be 1-based product numbers from the list. If nothing matches, return:
{{"selected_indices": []}}"""

        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=1024,
                )
            )
            
            # Extract the response text
            response_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.startswith('```'):
                response_text = response_text[3:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            # Parse the JSON response
            response_data = json.loads(response_text)
            selected_indices_1based = response_data.get("selected_indices", [])
            
            # Convert to 0-based indices and validate
            selected_indices = []
            for idx in selected_indices_1based:
                zero_based_idx = idx - 1
                if 0 <= zero_based_idx < len(products):
                    selected_indices.append(zero_based_idx)
            
            return selected_indices
            
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}. Response: {response_text}")
            return []
            
        except Exception as e:
            error_message = str(e)
            print(f"Error in AI filtering: {error_message}")
            
            # Check if it's a quota error (429 status or quota exceeded message)
            if '429' in error_message or 'quota' in error_message.lower() or 'exceeded' in error_message.lower():
                raise AIQuotaExceededError(
                    f"Gemini API quota exceeded. Please wait and try again later. Error: {error_message}"
                )
            
            return []


def filter_offers_with_ai(query: str, offers: List) -> List:
    """
    Filter a list of Offer objects using AI.
    
    Args:
        query: User's search query
        offers: List of Offer model instances or OfferData objects
    
    Returns:
        Filtered list of offers that match the query intent
    """
    if not offers:
        return offers
    
    # Convert offers to dictionaries for AI processing
    products_data = []
    for offer in offers:
        if hasattr(offer, 'title'):
            products_data.append({
                'title': offer.title,
                'item_price': float(offer.item_price) if hasattr(offer, 'item_price') else 0
            })
    
    # Get AI filter
    ai_filter = AIProductFilter()
    selected_indices = ai_filter.filter_products(query, products_data)
    
    # Return filtered offers
    return [offers[i] for i in selected_indices]
