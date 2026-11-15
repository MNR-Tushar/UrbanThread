from django.core.cache import cache
from django.db.models import Avg, Count
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver

from .models import Review


def refresh_product_rating(product_id):
    from products.models import Product
    rating = Review.objects.filter(product_id=product_id, is_approved=True).aggregate(avg=Avg('rating'), count=Count('id'))
    Product.objects.filter(pk=product_id).update(average_rating=rating['avg'] or 0, review_count=rating['count'])
    cache.set(f'product_rating:{product_id}', {'average_rating': float(rating['avg'] or 0), 'review_count': rating['count']}, 60 * 60)
    try:
        cache.delete_pattern('*product_list:*')
        cache.delete_pattern('*product_detail:*')
    except AttributeError:
        cache.clear()


@receiver(pre_save, sender=Review)
def remember_previous_product(sender, instance, **kwargs):
    instance._previous_product_id = sender.objects.filter(pk=instance.pk).values_list('product_id', flat=True).first() if instance.pk else None


@receiver(post_save, sender=Review)
def update_rating_on_save(sender, instance, **kwargs):
    refresh_product_rating(instance.product_id)
    if instance._previous_product_id and instance._previous_product_id != instance.product_id:
        refresh_product_rating(instance._previous_product_id)


@receiver(post_delete, sender=Review)
def update_rating_on_delete(sender, instance, **kwargs):
    refresh_product_rating(instance.product_id)
