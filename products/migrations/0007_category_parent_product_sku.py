from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('products', '0006_rename_update_at_product_updated_at')]
    operations = [
        migrations.AddField(model_name='category', name='parent', field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='subcategories', to='products.category')),
        migrations.AddField(model_name='product', name='sku', field=models.CharField(blank=True, max_length=40, null=True, unique=True)),
    ]
