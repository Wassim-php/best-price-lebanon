from rest_framework import serializers
from .models import ComparisonSearch, ComparisonResult


class ComparisonResultSerializer(serializers.ModelSerializer):
    """Serializer for individual comparison results"""
    
    score_breakdown = serializers.SerializerMethodField()
    
    class Meta:
        model = ComparisonResult
        fields = [
            'id', 'source', 'product_title', 'product_url', 'image_url',
            'in_stock', 'item_price', 'shipping_fee', 'tax_amount', 
            'total_price', 'currency', 'delivery_time', 'delivery_days',
            'store_rating', 'score', 'score_breakdown', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_score_breakdown(self, obj):
        """Return score breakdown if available"""
        return {
            'price_score': float(obj.price_score) if obj.price_score else None,
            'delivery_score': float(obj.delivery_score) if obj.delivery_score else None,
            'trust_score': float(obj.trust_score) if obj.trust_score else None,
        }


class ComparisonSearchSerializer(serializers.ModelSerializer):
    """Serializer for comparison search with results"""
    
    results = ComparisonResultSerializer(many=True, read_only=True)
    sites_failed = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()
    
    class Meta:
        model = ComparisonSearch
        fields = [
            'id', 'query', 'location', 'min_price', 'sites_checked',
            'sites_succeeded', 'sites_failed', 'username', 'created_at', 'results'
        ]
        read_only_fields = ['id', 'created_at', 'min_price', 'sites_checked', 'sites_succeeded']
    
    def get_sites_failed(self, obj):
        """Calculate number of failed sites"""
        return obj.sites_checked - obj.sites_succeeded
    
    def get_username(self, obj):
        """Return username if user exists"""
        return obj.user.username if obj.user else None


class ComparisonSearchListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing comparison searches (without full results)"""
    
    result_count = serializers.SerializerMethodField()
    top_result = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()
    
    class Meta:
        model = ComparisonSearch
        fields = [
            'id', 'query', 'location', 'min_price', 'sites_checked',
            'sites_succeeded', 'result_count', 'top_result', 'username', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_result_count(self, obj):
        """Return number of results"""
        return obj.results.count()
    
    def get_top_result(self, obj):
        """Return the best scoring result"""
        top = obj.results.first()  # Already ordered by -score
        if top:
            return {
                'source': top.source,
                'product_title': top.product_title,
                'total_price': float(top.total_price),
                'score': float(top.score)
            }
        return None
    
    def get_username(self, obj):
        """Return username if user exists"""
        return obj.user.username if obj.user else None
