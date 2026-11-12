from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('products', '0008_storebanner')]
    operations = [
        migrations.CreateModel(
            name='StoreSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('store_name', models.CharField(default='UrbanThread', max_length=120)),
                ('help_phone', models.CharField(blank=True, max_length=30)),
                ('social_facebook', models.URLField(blank=True)),
                ('social_instagram', models.URLField(blank=True)),
                ('dhaka_delivery_fee', models.DecimalField(decimal_places=2, default=70, max_digits=8)),
                ('outside_delivery_fee', models.DecimalField(decimal_places=2, default=130, max_digits=8)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
