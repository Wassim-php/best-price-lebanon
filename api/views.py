from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from scraping.registry import ADAPTERS
from scraping.services import run_search
from scraping.serializers import SearchJobSerializer, OfferSerializer

@api_view(["POST"])
@permission_classes([IsAuthenticated])
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
@permission_classes([IsAuthenticated])
def get_product_details(request, source_key: str):
    """
    Get detailed pricing for a specific product including shipping and taxes.
    
    POST body:
        - product_url (required): Full URL to the product page
        - location (optional): Delivery location - "inside beirut" or "outside beirut" 
          (default: "outside beirut")
        
    Returns:
        Detailed pricing information including:
        - item_price: Base product price
        - shipping_fee: Shipping cost (if applicable)
        - tax_amount: Tax amount (if applicable)
        - total_price: Final total price
        - currency: Currency code
        - delivery_time: Estimated delivery time (if available)
        - breakdown: Detailed pricing breakdown
    """
    if source_key not in ADAPTERS:
        return Response({"error": "Unknown source"}, status=status.HTTP_404_NOT_FOUND)
    
    product_url = (request.data.get("product_url") or "").strip()
    if not product_url:
        return Response({"error": "product_url is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    location = (request.data.get("location") or "outside beirut").strip()
    
    try:
        adapter = ADAPTERS[source_key]
        
        # Check if adapter supports detailed pricing
        if not hasattr(adapter, 'get_detailed_pricing'):
            return Response(
                {"error": f"Source {source_key} does not support detailed pricing"},
                status=status.HTTP_501_NOT_IMPLEMENTED
            )
        
        pricing_details = adapter.get_detailed_pricing(product_url, location=location)
        return Response(pricing_details)
        
    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def search_and_get_details(request, source_key: str):
    """
    Search for the cheapest product matching the query and get its complete details.
    
    This endpoint combines AI-filtered search with detailed pricing to provide
    a complete product recommendation with final pricing.
    
    POST body:
        - query (required): Search query string
        - location (optional): Delivery location - "inside beirut" or "outside beirut" 
          (default: "outside beirut")
        
    Returns:
        Complete product information including:
        - product: Basic product info (title, url, image_url, etc.)
        - pricing: Detailed pricing breakdown
            - item_price: Base product price
            - shipping_fee: Shipping cost
            - tax_amount: Tax amount
            - total_price: Final total price
            - currency: Currency code
            - delivery_time: Estimated delivery time
            - breakdown: Detailed pricing breakdown
        - source: Source name
        - query: Original search query
    """
    if source_key not in ADAPTERS:
        return Response({"error": "Unknown source"}, status=status.HTTP_404_NOT_FOUND)

    query = (request.data.get("query") or "").strip()
    if not query:
        return Response({"error": "query is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    location = (request.data.get("location") or "outside beirut").strip()
    
    try:
        # Step 1: Search with AI filter and cheapest only
        job = run_search(
            query=query, 
            source_key=source_key, 
            limit=10, 
            use_ai_filter=True,
            cheapest_only=True
        )
        
        # Step 2: Get the offers from the job
        offers = job.offers.all()
        
        if not offers:
            return Response({
                "error": "No products found matching your query",
                "query": query,
                "source": source_key
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Should have exactly 1 offer due to cheapest_only=True
        offer = offers[0]
        
        # Step 3: Get detailed pricing for the product
        adapter = ADAPTERS[source_key]
        
        # Check if adapter supports detailed pricing
        if not hasattr(adapter, 'get_detailed_pricing'):
            # If detailed pricing not supported, return basic info
            return Response({
                "product": {
                    "title": offer.title,
                    "url": offer.url,
                    "image_url": offer.image_url,
                    "item_price": float(offer.item_price),
                    "currency": offer.currency,
                    "in_stock": offer.in_stock,
                },
                "pricing": {
                    "item_price": float(offer.item_price),
                    "shipping_fee": None,
                    "tax_amount": None,
                    "total_price": float(offer.item_price),
                    "currency": offer.currency,
                    "delivery_time": None,
                    "breakdown": {
                        "note": f"Source {source_key} does not support detailed pricing"
                    }
                },
                "source": source_key,
                "query": query
            })
        
        pricing_details = adapter.get_detailed_pricing(offer.url, location=location)
        
        # Step 4: Combine everything into final response
        return Response({
            "product": {
                "title": offer.title,
                "url": offer.url,
                "image_url": offer.image_url,
                "in_stock": offer.in_stock,
            },
            "pricing": pricing_details,
            "source": source_key,
            "query": query
        })
        
    except Exception as e:
        return Response({"error": str(e)}, status=500)
