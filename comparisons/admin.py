from django.contrib import admin
from .models import ComparisonSearch, ComparisonResult

@admin.register(ComparisonSearch)
class ComparisonSearchAdmin(admin.ModelAdmin):
    list_display = ['id', 'query', 'location', 'user', 'created_at']
    list_filter = ['created_at', 'location']
    search_fields = ['query', 'user__username']
    ordering = ['-created_at']

@admin.register(ComparisonResult)
class ComparisonResultAdmin(admin.ModelAdmin):
    list_display = ['id', 'search', 'source', 'score', 'total_price', 'created_at']
    list_filter = ['source', 'created_at']
    search_fields = ['product_title']
    ordering = ['-score']
