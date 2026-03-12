"""
Views for product comparison across multiple sources
"""
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from decimal import Decimal
from typing import Dict, List, Optional, Any

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny
from rest_framework.response import Response
from rest_framework import status

from scraping.registry import ADAPTERS
from scraping.services import run_search
from scraping.ai_filter import AIQuotaExceededError
from .models import ComparisonSearch, ComparisonResult
from .serializers import ComparisonSearchSerializer, ComparisonSearchListSerializer
from .scoring import parse_delivery_days, calculate_product_rating

logger = logging.getLogger(__name__)


def fetch_product_from_source(source_key: str, query: str, location: str) -> Dict[str, Any]:
    """
    Fetch product details from a single source (used in parallel execution).
    
    Args:
        source_key: Identifier for the adapter (e.g., "mobileleb")
        query: Search query
        location: Delivery location
        
    Returns:
        Dictionary with result or error information
    """
    try:
        # Step 1: Search with AI filter and get cheapest
        job = run_search(
            query=query,
            source_key=source_key,
            limit=10,
            use_ai_filter=True,  # Re-enabled with proper error handling
            cheapest_only=True
        )
        
        # Step 2: Get the offers from the job
        offers = job.offers.all()
        
        if not offers:
            return {
                'success': False,
                'source': source_key,
                'error': 'No products found'
            }
        
        offer = offers[0]
        adapter = ADAPTERS[source_key]
        
        # Step 3: Get detailed pricing if supported
        pricing_details = None
        if hasattr(adapter, 'get_detailed_pricing'):
            try:
                pricing_details = adapter.get_detailed_pricing(offer.url, location=location)
            except Exception as e:
                logger.warning(f"Failed to get detailed pricing for {source_key}: {e}")
                # Fall back to basic pricing
                pricing_details = {
                    'item_price': float(offer.item_price),
                    'shipping_fee': None,
                    'tax_amount': None,
                    'total_price': float(offer.item_price),
                    'currency': offer.currency,
                    'delivery_time': None
                }
        else:
            # Use basic pricing from offer
            pricing_details = {
                'item_price': float(offer.item_price),
                'shipping_fee': None,
                'tax_amount': None,
                'total_price': float(offer.item_price),
                'currency': offer.currency,
                'delivery_time': None
            }
        
        # Get store metadata
        store_rating = getattr(adapter, 'STORE_RATING', 4.0)
        delivery_days = getattr(adapter, 'DELIVERY_DAYS', 7)
        
        # Parse delivery time if available
        if pricing_details.get('delivery_time'):
            delivery_days = parse_delivery_days(pricing_details['delivery_time'], default=delivery_days)
        
        return {
            'success': True,
            'source': source_key,
            'product': {
                'title': offer.title,
                'url': offer.url,
                'image_url': offer.image_url,
                'in_stock': offer.in_stock,
            },
            'pricing': pricing_details,
            'store_rating': store_rating,
            'delivery_days': delivery_days
        }
        
    except AIQuotaExceededError as e:
        logger.warning(f"AI quota exceeded for {source_key}: {str(e)}")
        return {
            'success': False,
            'source': source_key,
            'error': 'AI_QUOTA_EXCEEDED',
            'error_detail': 'Gemini API quota exceeded. Please try again later.'
        }
    except Exception as e:
        logger.error(f"Error fetching from {source_key}: {str(e)}", exc_info=True)
        return {
            'success': False,
            'source': source_key,
            'error': str(e)
        }


@api_view(['POST'])
@permission_classes([AllowAny])
def compare_all_sources(request):
    """
    Compare product prices across all available sources.
    
    POST body:
        - query (required): Search query string
        - location (optional): Delivery location (default: "outside beirut")
        - save (optional): Whether to save to database (default: True)
        
    Returns:
        Comprehensive comparison with scores for each product
    """
    query = (request.data.get('query') or '').strip()
    if not query:
        return Response(
            {'error': 'query is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    location = (request.data.get('location') or 'outside beirut').strip()
    should_save = request.data.get('save', True)
    
    # Get user if authenticated
    user = request.user if request.user.is_authenticated else None
    
    # Fetch from all sources in parallel
    results = []
    failed_sources = []
    
    logger.info(f"Starting parallel search for '{query}' across {len(ADAPTERS)} sources")
    
    with ThreadPoolExecutor(max_workers=7) as executor:
        # Submit all tasks
        future_to_source = {
            executor.submit(fetch_product_from_source, source_key, query, location): source_key
            for source_key in ADAPTERS.keys()
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_source):
            source_key = future_to_source[future]
            try:
                result = future.result(timeout=30)  # 30 second timeout per source
                if result['success']:
                    results.append(result)
                else:
                    failed_sources.append({
                        'source': source_key,
                        'error': result.get('error', 'Unknown error'),
                        'error_detail': result.get('error_detail')
                    })
            except Exception as e:
                logger.error(f"Exception for {source_key}: {str(e)}")
                failed_sources.append({
                    'source': source_key,
                    'error': str(e)
                })
    
    # Check if most failures are due to AI quota
    quota_errors = [f for f in failed_sources if f.get('error') == 'AI_QUOTA_EXCEEDED']
    if len(quota_errors) >= len(ADAPTERS) - 1:  # If almost all failed due to quota
        return Response({
            'error': 'AI_QUOTA_EXCEEDED',
            'message': 'Gemini API quota exceeded. The AI filtering service is temporarily unavailable. Please try again in a few minutes.',
            'query': query,
            'sites_affected': len(quota_errors),
            'total_sites': len(ADAPTERS)
        }, status=status.HTTP_429_TOO_MANY_REQUESTS)
    
    if not results:
        return Response({
            'error': 'No products found from any source',
            'query': query,
            'failed_sources': failed_sources
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Calculate minimum price across all results
    min_price = min(float(r['pricing']['total_price']) for r in results)
    
    # Calculate scores for each result
    scored_results = []
    for result in results:
        price = float(result['pricing']['total_price'])
        delivery_days = result['delivery_days']
        store_rating = result['store_rating']
        
        scores = calculate_product_rating(
            price=price,
            min_price=min_price,
            delivery_days=delivery_days,
            store_stars=store_rating
        )
        
        result['score'] = scores['final_score']
        result['score_breakdown'] = {
            'price_score': scores['price_score'],
            'delivery_score': scores['delivery_score'],
            'trust_score': scores['trust_score']
        }
        scored_results.append(result)
    
    # Sort by score (highest first)
    scored_results.sort(key=lambda x: x['score'], reverse=True)
    
    # Save to database if requested
    comparison_search = None
    if should_save:
        try:
            comparison_search = ComparisonSearch.objects.create(
                user=user,
                query=query,
                location=location,
                min_price=Decimal(str(min_price)),
                sites_checked=len(ADAPTERS),
                sites_succeeded=len(results)
            )
            
            # Create ComparisonResult entries
            for result in scored_results:
                # Safely extract pricing values with fallbacks
                pricing = result.get('pricing', {})
                item_price = pricing.get('item_price', pricing.get('total_price', 0))
                shipping_fee = pricing.get('shipping_fee')
                tax_amount = pricing.get('tax_amount')
                total_price = pricing.get('total_price', item_price)
                currency = pricing.get('currency', 'USD')
                
                ComparisonResult.objects.create(
                    search=comparison_search,
                    source=result['source'],
                    product_title=result['product']['title'],
                    product_url=result['product']['url'],
                    image_url=result['product'].get('image_url'),
                    in_stock=result['product'].get('in_stock'),
                    item_price=Decimal(str(item_price)),
                    shipping_fee=Decimal(str(shipping_fee)) if shipping_fee is not None else None,
                    tax_amount=Decimal(str(tax_amount)) if tax_amount is not None else None,
                    total_price=Decimal(str(total_price)),
                    currency=currency,
                    delivery_time=pricing.get('delivery_time'),
                    delivery_days=result.get('delivery_days'),
                    store_rating=Decimal(str(result.get('store_rating', 4.0))),
                    score=Decimal(str(result['score'])),
                    price_score=Decimal(str(result['score_breakdown']['price_score'])),
                    delivery_score=Decimal(str(result['score_breakdown']['delivery_score'])),
                    trust_score=Decimal(str(result['score_breakdown']['trust_score'])),
                    pricing_breakdown=pricing
                )
            
            logger.info(f"Saved comparison search {comparison_search.id} for user {user}")
            
        except Exception as e:
            logger.error(f"Failed to save comparison to database: {str(e)}", exc_info=True)
    
    # Prepare response
    response_data = {
        'query': query,
        'location': location,
        'results': [
            {
                'product': r['product'],
                'pricing': r['pricing'],
                'source': r['source'],
                'store_rating': r['store_rating'],
                'delivery_days': r['delivery_days'],
                'score': r['score'],
                'score_breakdown': r['score_breakdown']
            }
            for r in scored_results
        ],
        'metadata': {
            'min_price': min_price,
            'sites_checked': len(ADAPTERS),
            'sites_succeeded': len(results),
            'sites_failed': len(failed_sources),
            'failed_sources': failed_sources
        }
    }
    
    # Add search ID if saved
    if comparison_search:
        response_data['search_id'] = comparison_search.id
    
    return Response(response_data)


@api_view(['GET'])
def get_comparison_history(request):
    """
    Get comparison search history for the authenticated user.
    
    Query params:
        - limit (optional): Number of results to return (default: 20)
    """
    if not request.user.is_authenticated:
        return Response(
            {'error': 'Authentication required'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    limit = int(request.GET.get('limit', 20))
    
    searches = ComparisonSearch.objects.filter(
        user=request.user
    ).prefetch_related('results')[:limit]
    
    serializer = ComparisonSearchListSerializer(searches, many=True)
    return Response({
        'count': searches.count(),
        'searches': serializer.data
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def get_comparison_details(request, search_id: int):
    """
    Get detailed results for a specific comparison search.
    
    Args:
        search_id: ID of the comparison search
    """
    try:
        search = ComparisonSearch.objects.prefetch_related('results').get(id=search_id)
        
        # Check if user owns this search (if authenticated)
        if request.user.is_authenticated and search.user and search.user != request.user:
            return Response(
                {'error': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = ComparisonSearchSerializer(search)
        return Response(serializer.data)
        
    except ComparisonSearch.DoesNotExist:
        return Response(
            {'error': 'Comparison search not found'},
            status=status.HTTP_404_NOT_FOUND
        )
