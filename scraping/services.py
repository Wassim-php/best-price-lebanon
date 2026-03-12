from scraping.models import SearchJob, Offer
from scraping.registry import ADAPTERS
from scraping.ai_filter import filter_offers_with_ai, AIQuotaExceededError

def run_search(query: str, source_key: str, limit: int = 10, use_ai_filter: bool = False, cheapest_only: bool = False) -> SearchJob:
    """
    Run a product search, optionally filtering results with AI.
    
    Args:
        query: Search query string
        source_key: Source adapter key (e.g., '961souq')
        limit: Maximum number of initial results to fetch
        use_ai_filter: If True, uses AI to filter results to match exact query intent
        cheapest_only: If True, returns only the cheapest product after AI filtering
    
    Returns:
        SearchJob instance with offers
    """
    job = SearchJob.objects.create(query=query, source=source_key, status="RUNNING")

    adapter = ADAPTERS[source_key]
    results = adapter.search(query=query, limit=limit)
    
    # Apply AI filtering if requested
    if use_ai_filter and results:
        try:
            results = filter_offers_with_ai(query, results)
        except AIQuotaExceededError:
            # Re-raise quota errors to be handled by the caller
            raise
        except Exception as e:
            # If AI filtering fails for other reasons, log error but continue with unfiltered results
            print(f"AI filtering failed: {e}. Using unfiltered results.")
    
    # If cheapest_only is enabled, select only the cheapest product
    if cheapest_only and results:
        cheapest = min(results, key=lambda x: float(x.item_price))
        results = [cheapest]

    Offer.objects.bulk_create([
        Offer(
            job=job,
            title=o.title,
            url=o.url,
            image_url=o.image_url,
            item_price=o.item_price,
            currency=o.currency,
            in_stock=o.in_stock,
        )
        for o in results
    ])

    job.status = "DONE"
    job.save(update_fields=["status"])
    return job
