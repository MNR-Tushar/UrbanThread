from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("coupons", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="coupon",
            name="start_date",
            field=models.DateField(blank=True, null=True),
        ),
    ]
