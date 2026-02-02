from scraping.models import SearchJob, Offer
from scraping.registry import ADAPTERS

def run_search(query: str, source_key: str, limit: int = 10) -> SearchJob:
    job = SearchJob.objects.create(query=query, source=source_key, status="RUNNING")

    adapter = ADAPTERS[source_key]
    results = adapter.search(query=query, limit=limit)

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
