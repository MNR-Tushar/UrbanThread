from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('orders', '0003_order_fulfillment_statuses')]
    operations = [migrations.AddField(model_name='order', name='shipping_address', field=models.JSONField(blank=True, null=True))]
