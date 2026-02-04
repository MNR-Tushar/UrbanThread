# Generated migration for Payment model updates

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0001_initial'),
        ('orders', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Remove old Payment model fields and recreate
        migrations.RemoveField(
            model_name='payment',
            name='tranction_id',
        ),
        
        # Add new fields
        migrations.AddField(
            model_name='payment',
            name='transaction_id',
            field=models.CharField(max_length=100, unique=True, default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='payment',
            name='amount',
            field=models.DecimalField(decimal_places=2, max_digits=10, default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='payment',
            name='currency',
            field=models.CharField(default='BDT', max_length=3),
        ),
        migrations.AddField(
            model_name='payment',
            name='val_id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='payment',
            name='card_type',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='payment',
            name='card_no',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='payment',
            name='bank_tran_id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='payment',
            name='card_issuer',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='payment',
            name='card_brand',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='payment',
            name='card_issuer_country',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='payment',
            name='risk_level',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='payment',
            name='risk_title',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='payment',
            name='response_data',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='payment',
            name='error_message',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='payment',
            name='completed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        
        # Modify existing fields
        migrations.AlterField(
            model_name='payment',
            name='status',
            field=models.CharField(
                choices=[
                    ('pending', 'Pending'),
                    ('processing', 'Processing'),
                    ('completed', 'Completed'),
                    ('failed', 'Failed'),
                    ('refunded', 'Refunded'),
                    ('cancelled', 'Cancelled'),
                ],
                default='pending',
                max_length=20
            ),
        ),
        migrations.AlterField(
            model_name='payment',
            name='payment_method',
            field=models.CharField(
                choices=[
                    ('cash_on_delivery', 'Cash on Delivery'),
                    ('sslcommerz', 'SSL Commerce'),
                    ('card', 'Credit/Debit Card'),
                    ('mobile_banking', 'Mobile Banking'),
                    ('internet_banking', 'Internet Banking'),
                ],
                max_length=100
            ),
        ),
        migrations.AlterField(
            model_name='payment',
            name='order',
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='payment',
                to='orders.order'
            ),
        ),
        migrations.AlterField(
            model_name='payment',
            name='user',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='payments',
                to=settings.AUTH_USER_MODEL
            ),
        ),
        
        # Create PaymentLog model
        migrations.CreateModel(
            name='PaymentLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_type', models.CharField(max_length=50)),
                ('event_data', models.JSONField()),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('payment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='logs', to='payments.payment')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        
        # Add indexes
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['transaction_id'], name='payments_pa_transac_idx'),
        ),
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['status'], name='payments_pa_status_idx'),
        ),
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['user', 'created_at'], name='payments_pa_user_cr_idx'),
        ),
    ]