from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('orders', '0004_order_shipping_address')]
    operations = [migrations.AddField(model_name='order', name='shipping_fee', field=models.DecimalField(decimal_places=2, default=0, max_digits=8))]
