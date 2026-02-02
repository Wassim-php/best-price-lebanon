from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from scraping.registry import ADAPTERS
from scraping.services import run_search

@api_view(["POST"])
def search_by_source(request, source_key: str):
    if source_key not in ADAPTERS:
        return Response({"error": "Unknown source"}, status=status.HTTP_404_NOT_FOUND)

    query = (request.data.get("query") or "").strip()
    if not query:
        return Response({"error": "query is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        job = run_search(query=query, source_key=source_key, limit=10)
    except Exception as e:
        return Response({"error": str(e)}, status=500)

    return Response({
        "job_id": job.id,
        "status": job.status,
        "source": source_key,
        "offers": list(job.offers.values("title", "item_price", "currency", "url", "image_url"))
    })
