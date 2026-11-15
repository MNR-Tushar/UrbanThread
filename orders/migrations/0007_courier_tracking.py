from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('orders', '0006_orderstatushistory')]
    operations = [
        migrations.AddField('order', 'courier_name', models.CharField(blank=True, max_length=80)),
        migrations.AddField('order', 'courier_tracking_id', models.CharField(blank=True, max_length=120)),
        migrations.AddField('order', 'courier_tracking_url', models.URLField(blank=True)),
    ]
