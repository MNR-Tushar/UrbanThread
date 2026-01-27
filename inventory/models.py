from django.db import models
import uuid
from django.utils.text import slugify
from products.models import *

class Inventory(models.Model):
    product=models.ForeignKey(Product, on_delete=models.CASCADE)
    color=models.ForeignKey(Color, on_delete=models.CASCADE)
    size=models.ForeignKey(Size, on_delete=models.CASCADE)
    quantity=models.PositiveIntegerField(default=0)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['product', 'color', 'size']
        verbose_name_plural = 'Inventories'
    
    def __str__(self):
        return f"{self.product.product_name} - {self.product.product_name} - {self.color.color} - {self.size.size_type} ({self.quantity})"

