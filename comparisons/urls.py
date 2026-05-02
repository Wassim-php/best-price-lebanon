from django.urls import path
from .views import (
    compare_all_sources,
    get_comparison_history,
    get_trending_searches,
    clear_comparison_history,
    get_comparison_details,
)

urlpatterns = [
    path('compare', compare_all_sources, name='compare_all_sources'),
    path('history', get_comparison_history, name='comparison_history'),
    path('trending', get_trending_searches, name='trending_searches'),
    path('history/clear', clear_comparison_history, name='clear_comparison_history'),
    path('<int:search_id>', get_comparison_details, name='comparison_details'),
]
