from django.contrib import admin
from .models import SearchJob, Offer

@admin.register(SearchJob)
class SearchJobAdmin(admin.ModelAdmin):
    list_display = ('id', 'query', 'source', 'status', 'created_at')
    list_filter = ('status', 'source', 'created_at')
    search_fields = ('query',)
    readonly_fields = ('created_at',)

@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'item_price', 'currency', 'job', 'created_at')
    list_filter = ('currency', 'in_stock', 'created_at')
    search_fields = ('title', 'url')
    readonly_fields = ('created_at',)
