from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('orders', '0002_alter_order_order_status_alter_order_payment_status_and_more')]
    operations = [
        migrations.AlterField(
            model_name='order', name='order_status',
            field=models.CharField(choices=[('pending', 'Pending'), ('confirmed', 'Confirmed'), ('packaging', 'Packaging'), ('shipped', 'Shipped'), ('delivered', 'Delivered'), ('processing', 'Processing'), ('completed', 'Completed'), ('cancelled', 'Cancelled')], default='pending', max_length=20),
        ),
    ]
