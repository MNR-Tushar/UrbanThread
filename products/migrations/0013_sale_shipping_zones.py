from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('products', '0012_wishlistitem')]
    operations = [
        migrations.AddField('product', 'compare_at_price', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
        migrations.AddField('product', 'sale_starts_at', models.DateTimeField(blank=True, null=True)),
        migrations.AddField('product', 'sale_ends_at', models.DateTimeField(blank=True, null=True)),
        migrations.AddField('product', 'is_featured', models.BooleanField(default=False)),
        migrations.AddField('storesettings', 'free_shipping_threshold', models.DecimalField(decimal_places=2, default=2500, max_digits=10)),
        migrations.CreateModel(name='DeliveryZone', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('name', models.CharField(max_length=100)),
            ('areas', models.TextField(help_text='Comma-separated city/district/area names matched against delivery address')),
            ('delivery_fee', models.DecimalField(decimal_places=2, default=100, max_digits=8)),
            ('is_active', models.BooleanField(default=True)),
        ]),
    ]
