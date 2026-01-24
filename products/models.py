from django.db import models
import uuid
from django.utils.text import slugify
class Category(models.Model):
    category_name=models.CharField(max_length=100)
    description=models.TextField(blank=True,null=True)
    slug=models.SlugField(max_length=150,blank=True,unique=True)
    created_at=models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.category_name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.category_name}-{uuid.uuid4().hex[:6]}")
        super().save(*args, **kwargs)
    
class Brand(models.Model):
    band_name=models.CharField(max_length=100)
    description=models.TextField(blank=True,null=True)
    slug=models.SlugField(max_length=150,blank=True,unique=True)
    created_at=models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.band_name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.band_name}-{uuid.uuid4().hex[:6]}")
        super().save(*args, **kwargs)
    
class Product(models.Model):
    product_name=models.CharField(max_length=100)
    description=models.TextField(blank=True,null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2)
    is_available = models.BooleanField(default=True)
    slug=models.SlugField(max_length=150,blank=True,unique=True)
    created_at=models.DateTimeField(auto_now_add=True)
    
    category=models.ForeignKey(Category, on_delete=models.CASCADE)
    brand=models.ForeignKey(Brand, on_delete=models.CASCADE)

    def __str__(self):
        return self.product_name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.product_name}-{uuid.uuid4().hex[:6]}")
        super().save(*args, **kwargs)

class ProductImage(models.Model):
    productimg=models.ForeignKey(Product, on_delete=models.CASCADE)
    image=models.ImageField(upload_to='product_images/', blank=True, null=True)
    created_at=models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Image for {self.product.product_name}"

class Size(models.Model):
    S="Small"
    M="Medium"
    L="Large"
    XL="Extra Large"
    XXL="Extra Extra Large"
    size_choices=(
        (S,"Small"),
        (M,"Medium"),
        (L,"Large"),
        (XL,"Extra Large"),
        (XXL,"Extra Extra Large"),
    )
    size_type=models.CharField(max_length=100,choices=size_choices)
    created_at=models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.size_type
    
class Color(models.Model):
    color=models.CharField(max_length=100)
    created_at=models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.color