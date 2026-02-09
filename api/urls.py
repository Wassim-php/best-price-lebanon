from django.urls import path
from .views import search_by_source, get_product_details

urlpatterns = [
    path("search/<str:source_key>", search_by_source),
    path("product-details/<str:source_key>", get_product_details),
]
