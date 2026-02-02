from django.urls import path
from .views import search_by_source

urlpatterns = [
    path("search/<str:source_key>", search_by_source),
]
