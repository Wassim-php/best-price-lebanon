"""
Views for product comparison across multiple sources
"""
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from decimal import Decimal
from typing import Dict, List, Optional, Any

from django.db.models import Count, Max
from django.db.models.functions import Lower, Trim
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from scraping.registry import ADAPTERS
from scraping.services import run_search
from scraping.ai_filter import AIQuotaExceededError
from .models import ComparisonSearch, ComparisonResult
from .serializers import ComparisonSearchSerializer, ComparisonSearchListSerializer
from .scoring import parse_delivery_days, calculate_product_rating

logger = logging.getLogger(__name__)


def _parse_bool(value: Any, default: bool = False) -> bool:
    """Accept booleans from JSON or form-style string payloads."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {'true', '1', 'yes', 'y', 'on'}
    if value is None:
        return default
    return bool(value)


def _can_view_comparison(user, search: ComparisonSearch) -> bool:
    """Restrict saved comparison details to the owner, except for staff users."""
    if not user.is_authenticated:
        return False
    if user.is_staff:
        return True
    return search.user_id is not None and search.user_id == user.id


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
    logger.info(f"[{source_key}] Starting search for '{query}'")
    try:
        # Search each site independently; failures are returned per-source.
        job = run_search(
            query=query,
            source_key=source_key,
            limit=10,
            use_ai_filter=True,  # Re-enabled with proper error handling
            cheapest_only=True
        )
        
        # run_search stores normalized offers on the SearchJob.
        offers = job.offers.all()
        
        if not offers:
            logger.info(f"[{source_key}] No products found")
            return {
                'success': False,
                'source': source_key,
                'error': 'No products found'
            }
        
        offer = offers[0]
        adapter = ADAPTERS[source_key]
        
        # Detailed pricing adds shipping, delivery, and final total when available.
        pricing_details = None
        if hasattr(adapter, 'get_detailed_pricing'):
            try:
                pricing_details = adapter.get_detailed_pricing(offer.url, location=location)
            except Exception as e:
                logger.warning(f"[{source_key}] Detailed pricing failed: {e}")
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
        
        # Store metadata is adapter-owned so ranking can stay source-neutral.
        store_rating = getattr(adapter, 'STORE_RATING', 4.0)
        delivery_days = getattr(adapter, 'DELIVERY_DAYS', 7)
        
        # Parse delivery time if available
        if pricing_details.get('delivery_time'):
            delivery_days = parse_delivery_days(pricing_details['delivery_time'], default=delivery_days)
        
        logger.info(
            f"[{source_key}] Found result: title='{offer.title}' price={pricing_details.get('total_price')}"
        )
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
        logger.warning(f"[{source_key}] AI quota exceeded: {str(e)}")
        return {
            'success': False,
            'source': source_key,
            'error': 'AI_QUOTA_EXCEEDED',
            'error_detail': 'Gemini API quota exceeded. Please try again later.'
        }
    except Exception as e:
        logger.error(f"[{source_key}] Error fetching: {str(e)}", exc_info=True)
        return {
            'success': False,
            'source': source_key,
            'error': str(e)
        }


@api_view(['POST'])
@permission_classes([IsAuthenticated])
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
    should_save = _parse_bool(request.data.get('save', True), default=True)

    user = request.user
    
    # Fetch from all sources in parallel to keep compare-all responsive.
    results = []
    failed_sources = []
    
    logger.info(f"Starting parallel search for '{query}' across {len(ADAPTERS)} sources")
    logger.info(f"Sources: {', '.join(sorted(ADAPTERS.keys()))}")
    
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
                    logger.info(
                        f"[{source_key}] Failed: {result.get('error', 'Unknown error')}"
                    )
            except Exception as e:
                logger.error(f"Exception for {source_key}: {str(e)}")
                failed_sources.append({
                    'source': source_key,
                    'error': str(e)
                })
                logger.info(f"[{source_key}] Failed: {str(e)}")
    
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
    
    # The cheapest total price anchors the price score for all results.
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
    
    # Save the search and all scored results for history/trending endpoints.
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
    
    # Return both ranked results and operational metadata for the frontend.
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
    
    # Frontend uses search_id to open saved comparison details.
    if comparison_search:
        response_data['search_id'] = comparison_search.id
    
    return Response(response_data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_comparison_history(request):
    """
    Get comparison search history for the authenticated user.
    
    Query params:
        - limit (optional): Number of results to return (default: 20)
    """
    try:
        limit = int(request.GET.get('limit', 20))
    except ValueError:
        return Response(
            {'error': 'limit must be an integer'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if limit < 1:
        return Response(
            {'error': 'limit must be greater than 0'},
            status=status.HTTP_400_BAD_REQUEST
        )

    queryset = ComparisonSearch.objects.prefetch_related('results')
    if not request.user.is_staff:
        queryset = queryset.filter(user=request.user)

    total_count = queryset.count()
    searches = queryset[:limit]
    
    serializer = ComparisonSearchListSerializer(searches, many=True)
    return Response({
        'count': total_count,
        'searches': serializer.data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_trending_searches(request):
    """
    Get the most searched comparison queries.

    Query params:
        - limit (optional): Number of queries to return (default: 3, max: 3)
    """
    try:
        limit = int(request.GET.get('limit', 3))
    except ValueError:
        return Response(
            {'error': 'limit must be an integer'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if limit < 1:
        return Response(
            {'error': 'limit must be greater than 0'},
            status=status.HTTP_400_BAD_REQUEST
        )

    limit = min(limit, 3)
    # Count normalized queries so "Samsung" and "samsung" rank together.
    trending = (
        ComparisonSearch.objects.annotate(normalized_query=Lower(Trim('query')))
        .exclude(normalized_query='')
        .values('normalized_query')
        .annotate(search_count=Count('id'), latest_searched_at=Max('created_at'))
        .order_by('-search_count', '-latest_searched_at')[:limit]
    )

    searches = [
        {
            'query': item['normalized_query'],
            'latest_searched_at': item['latest_searched_at'],
        }
        for item in trending
    ]

    return Response({
        'searches': searches,
    })


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def clear_comparison_history(request):
    """
    Clear comparison history.

    Rules:
    - Regular users can clear only their own history.
    - Admin users can clear their own history by default, or another user's
      history by providing user_id in query params or request body.
    """
    raw_user_id = request.query_params.get('user_id')
    if raw_user_id is None:
        raw_user_id = request.data.get('user_id') if isinstance(request.data, dict) else None

    # Non-admin users can only clear their own history.
    if not request.user.is_staff:
        if raw_user_id is not None:
            try:
                requested_user_id = int(raw_user_id)
            except (TypeError, ValueError):
                return Response(
                    {'error': 'user_id must be an integer'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if requested_user_id != request.user.id:
                return Response(
                    {'error': 'Access denied'},
                    status=status.HTTP_403_FORBIDDEN
                )
        target_user_id = request.user.id
    else:
        # Admin can target any user; default to own history if user_id omitted.
        if raw_user_id is None:
            target_user_id = request.user.id
        else:
            try:
                target_user_id = int(raw_user_id)
            except (TypeError, ValueError):
                return Response(
                    {'error': 'user_id must be an integer'},
                    status=status.HTTP_400_BAD_REQUEST
                )

    searches_qs = ComparisonSearch.objects.filter(user_id=target_user_id)
    search_ids = list(searches_qs.values_list('id', flat=True))

    searches_deleted = len(search_ids)
    results_deleted = 0
    if search_ids:
        results_deleted = ComparisonResult.objects.filter(search_id__in=search_ids).count()
        searches_qs.delete()

    return Response({
        'message': 'Comparison history cleared',
        'user_id': target_user_id,
        'searches_deleted': searches_deleted,
        'results_deleted': results_deleted,
    })


@api_view(['GET', 'DELETE'])
@permission_classes([IsAuthenticated])
def get_comparison_details(request, search_id: int):
    """
    Get detailed results for a specific comparison search.
    
    Args:
        search_id: ID of the comparison search
    """
    try:
        search = ComparisonSearch.objects.prefetch_related('results').get(id=search_id)

        if not _can_view_comparison(request.user, search):
            return Response(
                {'error': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        if request.method == 'DELETE':
            deleted_results = search.results.count()
            search.delete()
            return Response({
                'message': 'Comparison deleted',
                'search_id': search_id,
                'results_deleted': deleted_results,
            })
        
        serializer = ComparisonSearchSerializer(search)
        return Response(serializer.data)
        
    except ComparisonSearch.DoesNotExist:
        return Response(
            {'error': 'Comparison search not found'},
            status=status.HTTP_404_NOT_FOUND
        )
