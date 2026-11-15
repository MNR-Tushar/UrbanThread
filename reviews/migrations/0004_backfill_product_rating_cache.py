from django.db import migrations
from django.db.models import Avg, Count


def populate_cached_ratings(apps, schema_editor):
    Review = apps.get_model('reviews', 'Review')
    Product = apps.get_model('products', 'Product')
    OrderItem = apps.get_model('orders', 'OrderItem')
    alias = schema_editor.connection.alias
    for product_id in Review.objects.using(alias).filter(is_approved=True).values_list('product_id', flat=True).distinct():
        data = Review.objects.using(alias).filter(product_id=product_id, is_approved=True).aggregate(avg=Avg('rating'), count=Count('id'))
        Product.objects.using(alias).filter(pk=product_id).update(average_rating=data['avg'] or 0, review_count=data['count'])
    verified_statuses = ['delivered', 'completed']
    for review in Review.objects.using(alias).filter(verified_purchase=False).iterator():
        purchased = OrderItem.objects.using(alias).filter(
            product_id=review.product_id,
            order__user_id=review.user_id,
            order__order_status__in=verified_statuses,
        ).exists()
        if purchased:
            Review.objects.using(alias).filter(pk=review.pk).update(verified_purchase=True)


class Migration(migrations.Migration):
    dependencies = [('reviews', '0003_review_verified_purchase_reviewimage_and_more'), ('products', '0014_product_average_rating_product_review_count'), ('orders', '0008_order_customer_email_order_customer_name_and_more')]
    operations = [migrations.RunPython(populate_cached_ratings, migrations.RunPython.noop)]
