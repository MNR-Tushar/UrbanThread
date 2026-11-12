from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('orders', '0005_order_shipping_fee')]
    operations = [
        migrations.CreateModel(
            name='OrderStatusHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('confirmed', 'Confirmed'), ('packaging', 'Packaging'), ('shipped', 'Shipped'), ('delivered', 'Delivered'), ('processing', 'Processing'), ('completed', 'Completed'), ('cancelled', 'Cancelled')], max_length=20)),
                ('note', models.CharField(blank=True, max_length=240)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='status_history', to='orders.order')),
            ],
            options={'ordering': ['created_at', 'id']},
        ),
    ]
