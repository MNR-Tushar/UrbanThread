from django.db import migrations


def backfill_verified_reviews(apps, schema_editor):
    Review = apps.get_model('reviews', 'Review')
    OrderItem = apps.get_model('orders', 'OrderItem')
    alias = schema_editor.connection.alias
    for review in Review.objects.using(alias).filter(verified_purchase=False).iterator():
        purchased = OrderItem.objects.using(alias).filter(
            product_id=review.product_id,
            order__user_id=review.user_id,
            order__order_status__in=['delivered', 'completed'],
        ).exists()
        if purchased:
            Review.objects.using(alias).filter(pk=review.pk).update(verified_purchase=True)


class Migration(migrations.Migration):
    dependencies = [('reviews', '0004_backfill_product_rating_cache')]
    operations = [migrations.RunPython(backfill_verified_reviews, migrations.RunPython.noop)]
