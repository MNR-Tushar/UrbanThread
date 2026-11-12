from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('products', '0007_category_parent_product_sku')]
    operations = [
        migrations.CreateModel(
            name='StoreBanner',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=120)),
                ('subtitle', models.CharField(blank=True, max_length=240)),
                ('image', models.ImageField(upload_to='store_banners/')),
                ('link', models.CharField(blank=True, max_length=300)),
                ('is_active', models.BooleanField(default=True)),
                ('sort_order', models.PositiveIntegerField(default=0)),
            ],
            options={'ordering': ['sort_order', 'id']},
        ),
    ]
