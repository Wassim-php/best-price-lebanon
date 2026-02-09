from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from scraping.registry import ADAPTERS
from scraping.services import run_search
from scraping.serializers import SearchJobSerializer

@api_view(["POST"])
def search_by_source(request, source_key: str):
    """
    Search for products from a specific source.
    
    POST body:
        - query (required): Search query string
        - use_ai_filter (optional): Boolean, default False. 
          If True, uses AI to filter results to match exact query intent.
          For example, "iPhone 15" will exclude cases, covers, and Pro variants.
        - cheapest_only (optional): Boolean, default False.
          If True, returns only the cheapest product from the AI-filtered results.
          Recommended to use with use_ai_filter=True for best results.
    """
    if source_key not in ADAPTERS:
        return Response({"error": "Unknown source"}, status=status.HTTP_404_NOT_FOUND)

    query = (request.data.get("query") or "").strip()
    if not query:
        return Response({"error": "query is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    # Get AI filter preference from request (default: False)
    use_ai_filter = request.data.get("use_ai_filter", False)
    if isinstance(use_ai_filter, str):
        use_ai_filter = use_ai_filter.lower() in ['true', '1', 'yes']
    
    # Get cheapest_only preference from request (default: False)
    cheapest_only = request.data.get("cheapest_only", False)
    if isinstance(cheapest_only, str):
        cheapest_only = cheapest_only.lower() in ['true', '1', 'yes']

    try:
        job = run_search(
            query=query, 
            source_key=source_key, 
            limit=10, 
            use_ai_filter=use_ai_filter,
            cheapest_only=cheapest_only
        )
    except Exception as e:
        return Response({"error": str(e)}, status=500)

    serializer = SearchJobSerializer(job)
    return Response(serializer.data)


@api_view(["POST"])
def get_product_details(request, source_key: str):
    """
    Get detailed pricing for a specific product including shipping and taxes.
    
    POST body:
        - product_url (required): Full URL to the product page
        
    Returns:
        Detailed pricing information including:
        - item_price: Base product price
        - shipping_fee: Shipping cost (if applicable)
        - tax_amount: Tax amount (if applicable)
        - total_price: Final total price
        - currency: Currency code
        - breakdown: Detailed pricing breakdown
    """
    if source_key not in ADAPTERS:
        return Response({"error": "Unknown source"}, status=status.HTTP_404_NOT_FOUND)
    
    product_url = (request.data.get("product_url") or "").strip()
    if not product_url:
        return Response({"error": "product_url is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        adapter = ADAPTERS[source_key]
        
        # Check if adapter supports detailed pricing
        if not hasattr(adapter, 'get_detailed_pricing'):
            return Response(
                {"error": f"Source {source_key} does not support detailed pricing"},
                status=status.HTTP_501_NOT_IMPLEMENTED
            )
        
        pricing_details = adapter.get_detailed_pricing(product_url)
        return Response(pricing_details)
        
    except Exception as e:
        return Response({"error": str(e)}, status=500)
