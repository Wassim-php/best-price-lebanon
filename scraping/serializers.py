from rest_framework import serializers
from .models import SearchJob, Offer


class OfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = Offer
        fields = ['id', 'title', 'url', 'image_url', 'item_price', 'currency', 'in_stock', 'created_at']
        read_only_fields = ['id', 'created_at']


class SearchJobSerializer(serializers.ModelSerializer):
    offers = OfferSerializer(many=True, read_only=True)
    
    class Meta:
        model = SearchJob
        fields = ['id', 'query', 'source', 'status', 'created_at', 'offers']
        read_only_fields = ['id', 'status', 'created_at']
