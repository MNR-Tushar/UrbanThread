from django.db import models
import uuid
from django.utils.text import slugify


class Category(models.Model):
    category_name = models.CharField(max_length=100)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='subcategories')
    description = models.TextField(blank=True, null=True)
    slug = models.SlugField(max_length=150, blank=True, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.category_name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.category_name}-{uuid.uuid4().hex[:6]}")
        super().save(*args, **kwargs)


class Brand(models.Model):
    brand_name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    slug = models.SlugField(max_length=150, blank=True, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.brand_name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.brand_name}-{uuid.uuid4().hex[:6]}")
        super().save(*args, **kwargs)


class Product(models.Model):
    product_name = models.CharField(max_length=100)
    sku = models.CharField(max_length=40, unique=True, null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    # FIX: allow null/blank so a product can have no discount; default=0 keeps
    # the existing > 0 checks in cart/order logic working correctly.
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=0)
    is_available = models.BooleanField(default=True)
    slug = models.SlugField(max_length=150, blank=True, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)

    def __str__(self):
        return self.product_name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.product_name}-{uuid.uuid4().hex[:6]}")
        super().save(*args, **kwargs)


class ProductImage(models.Model):
    productimg = models.ForeignKey(Product, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='product_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # FIX: was using self.product which does not exist; field is named productimg
    def __str__(self):
        return f"Image for {self.productimg.product_name}"


class StoreBanner(models.Model):
    title = models.CharField(max_length=120)
    subtitle = models.CharField(max_length=240, blank=True)
    image = models.ImageField(upload_to='store_banners/')
    link = models.CharField(max_length=300, blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'id']

    def __str__(self):
        return self.title


class StoreSettings(models.Model):
    store_name = models.CharField(max_length=120, default='UrbanThread')
    store_logo = models.ImageField(upload_to='store_settings/', blank=True, null=True)
    help_phone = models.CharField(max_length=30, blank=True)
    social_facebook = models.URLField(blank=True)
    social_instagram = models.URLField(blank=True)
    social_youtube = models.URLField(blank=True)
    dhaka_delivery_fee = models.DecimalField(max_digits=8, decimal_places=2, default=70)
    outside_delivery_fee = models.DecimalField(max_digits=8, decimal_places=2, default=130)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.store_name


class Size(models.Model):
    S = "Small"
    M = "Medium"
    L = "Large"
    XL = "Extra Large"
    XXL = "Extra Extra Large"
    size_choices = (
        (S, "Small"),
        (M, "Medium"),
        (L, "Large"),
        (XL, "Extra Large"),
        (XXL, "Extra Extra Large"),
    )
    size_type = models.CharField(max_length=100, choices=size_choices)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.size_type


class Color(models.Model):
    color = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.color
