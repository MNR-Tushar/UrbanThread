from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('reviews', '0001_initial')]
    operations = [
        migrations.AddField(model_name='review', name='is_approved', field=models.BooleanField(default=True)),
        migrations.AlterField(model_name='review', name='is_approved', field=models.BooleanField(default=False)),
    ]
