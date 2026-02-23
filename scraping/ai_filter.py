"""
AI-powered product filtering using Google Gemini.
This service intelligently filters products to match user query intent.
"""
from typing import List, Dict
import json
from django.conf import settings
import google.generativeai as genai


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
        prompt = f"""You are a product filtering assistant. Your job is to identify which products from a list EXACTLY match the user's search intent.

User Query: "{query}"

Available Products:
{products_text}

Instructions:
- Return ONLY products that match the EXACT intent of the query
- If the query is "iPhone 15", return ONLY standard iPhone 15 models
- Exclude accessories (cases, covers, chargers, screen protectors, etc.)
- Exclude variant models (Pro, Pro Max, Plus) unless explicitly in the query
- Exclude other model numbers or generations
- Be strict: when in doubt, exclude the product

Return your response as a JSON object with a "selected_indices" array containing the 1-based product numbers that match.
Example: {{"selected_indices": [1, 3, 5]}}

If no products match exactly, return {{"selected_indices": []}}"""

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
            # Fallback: try to extract numbers from response
            print(f"JSON decode error: {e}. Response: {response_text}")
            import re
            numbers = re.findall(r'\b\d+\b', response_text)
            selected_indices = []
            for num_str in numbers:
                idx = int(num_str) - 1
                if 0 <= idx < len(products):
                    selected_indices.append(idx)
            return selected_indices
            
        except Exception as e:
            print(f"Error in AI filtering: {e}")
            # Fallback: return all products if AI fails
            return list(range(len(products)))


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