from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('products', '0009_storesettings')]
    operations = [migrations.AddField(model_name='storesettings', name='store_logo', field=models.ImageField(blank=True, null=True, upload_to='store_settings/'))]
