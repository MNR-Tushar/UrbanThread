from django.db import models
from django.conf import settings
import uuid
from django.utils.text import slugify
from django.utils import timezone
from io import BytesIO
from pathlib import Path
from PIL import Image, ImageOps
from django.core.files.base import ContentFile


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
    compare_at_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    sale_starts_at = models.DateTimeField(null=True, blank=True)
    sale_ends_at = models.DateTimeField(null=True, blank=True)
    is_featured = models.BooleanField(default=False)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    review_count = models.PositiveIntegerField(default=0)
    is_available = models.BooleanField(default=True)
    slug = models.SlugField(max_length=150, blank=True, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)

    def __str__(self):
        return self.product_name

    @property
    def current_price(self):
        now = timezone.now()
        sale_active = (self.discount_price and self.discount_price > 0 and
                       (not self.sale_starts_at or self.sale_starts_at <= now) and
                       (not self.sale_ends_at or self.sale_ends_at >= now))
        return self.discount_price if sale_active else self.price

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.product_name}-{uuid.uuid4().hex[:6]}")
        super().save(*args, **kwargs)


class ProductImage(models.Model):
    productimg = models.ForeignKey(Product, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='product_images/', blank=True, null=True)
    image_small = models.ImageField(upload_to='product_images/optimized/', blank=True, null=True, editable=False)
    image_medium = models.ImageField(upload_to='product_images/optimized/', blank=True, null=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_image_name = self.image.name if self.image else ''

    def save(self, *args, **kwargs):
        image_changed = bool(self.image and self.image.name != self._original_image_name)
        super().save(*args, **kwargs)
        if image_changed:
            self._generate_responsive_images()
            type(self).objects.filter(pk=self.pk).update(
                image_small=self.image_small.name if self.image_small else '',
                image_medium=self.image_medium.name if self.image_medium else '',
            )
            self._original_image_name = self.image.name

    def _generate_responsive_images(self):
        if not self.image:
            return
        try:
            with self.image.open('rb') as source:
                original = ImageOps.exif_transpose(Image.open(source))
                if original.mode not in ('RGB', 'RGBA'):
                    original = original.convert('RGBA' if 'transparency' in original.info else 'RGB')
                stem = Path(self.image.name).stem
                for field_name, max_size in (('image_small', (480, 480)), ('image_medium', (960, 960))):
                    variant = original.copy()
                    variant.thumbnail(max_size, Image.Resampling.LANCZOS)
                    output = BytesIO()
                    variant.save(output, format='WEBP', quality=82, method=6)
                    getattr(self, field_name).save(
                        f'{stem}_{max_size[0]}.webp',
                        ContentFile(output.getvalue()),
                        save=False,
                    )
        except (OSError, ValueError):
            # Keep the original usable when an uploaded file is not a supported raster image.
            self.image_small = None
            self.image_medium = None

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
    free_shipping_threshold = models.DecimalField(max_digits=10, decimal_places=2, default=2500)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.store_name


class WishlistItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wishlist_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='wishlisted_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [models.UniqueConstraint(fields=['user', 'product'], name='unique_user_wishlist_product')]


class DeliveryZone(models.Model):
    name = models.CharField(max_length=100)
    areas = models.TextField(help_text='Comma-separated city/district/area names matched against delivery address')
    delivery_fee = models.DecimalField(max_digits=8, decimal_places=2, default=100)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.name} (৳{self.delivery_fee})'


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
