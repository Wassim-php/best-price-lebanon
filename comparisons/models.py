from django.db import models
from django.contrib.auth.models import User


class ComparisonSearch(models.Model):
    """Stores a user's comparison search query"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comparison_searches", null=True, blank=True)
    query = models.CharField(max_length=255)
    location = models.CharField(max_length=50, default="outside beirut")
    
    # Metadata
    min_price = models.DecimalField(max_digits=12, decimal_places=2, null=True)
    sites_checked = models.IntegerField(default=0)
    sites_succeeded = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['user', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.query} by {self.user.username if self.user else 'Anonymous'} at {self.created_at}"


class ComparisonResult(models.Model):
    """Stores individual product results from a comparison search"""
    search = models.ForeignKey(ComparisonSearch, on_delete=models.CASCADE, related_name="results")
    
    # Source info
    source = models.CharField(max_length=50)
    
    # Product info
    product_title = models.CharField(max_length=500)
    product_url = models.URLField(max_length=1000)
    image_url = models.URLField(max_length=1200, null=True, blank=True)
    in_stock = models.BooleanField(null=True)
    
    # Pricing details
    item_price = models.DecimalField(max_digits=12, decimal_places=2)
    shipping_fee = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=10, default="USD")
    
    # Delivery info
    delivery_time = models.CharField(max_length=100, null=True, blank=True)  # e.g., "3 days"
    delivery_days = models.IntegerField(null=True, blank=True)  # Parsed numeric value
    
    # Store rating
    store_rating = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)  # 0.0 to 5.0
    
    # Calculated scores
    score = models.DecimalField(max_digits=4, decimal_places=1)  # Overall score out of 10
    price_score = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    delivery_score = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    trust_score = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    
    # Raw pricing breakdown (JSON field for flexibility)
    pricing_breakdown = models.JSONField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-score']
        indexes = [
            models.Index(fields=['search', '-score']),
        ]
    
    def __str__(self):
        return f"{self.product_title} - {self.source} (Score: {self.score})"
