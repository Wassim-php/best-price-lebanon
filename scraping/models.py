from django.db import models

class SearchJob(models.Model):
    query = models.CharField(max_length=255)
    source = models.CharField(max_length=50)
    status = models.CharField(max_length=20, default="PENDING")  # PENDING/RUNNING/DONE/FAILED
    created_at = models.DateTimeField(auto_now_add=True)

class Offer(models.Model):
    job = models.ForeignKey(SearchJob, on_delete=models.CASCADE, related_name="offers")

    title = models.CharField(max_length=500)
    url = models.URLField(max_length=1000)
    image_url = models.URLField(max_length=1200, null=True, blank=True)

    item_price = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=10, default="USD")

    in_stock = models.BooleanField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
