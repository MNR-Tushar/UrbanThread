import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def trust_existing_accounts(apps, schema_editor):
    # Keep existing customers able to sign in; new accounts must verify first.
    User = apps.get_model('accounts', 'CustomUser')
    User.objects.using(schema_editor.connection.alias).update(email_verified=True)


class Migration(migrations.Migration):
    dependencies = [('accounts', '0003_passwordresetotp')]

    operations = [
        migrations.AddField(
            model_name='customuser', name='email_verified',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='customuser', name='google_sub',
            field=models.CharField(blank=True, max_length=255, null=True, unique=True),
        ),
        migrations.RunPython(trust_existing_accounts, migrations.RunPython.noop),
        migrations.CreateModel(
            name='EmailVerificationOTP',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code_hash', models.CharField(max_length=128)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField()),
                ('attempts', models.PositiveSmallIntegerField(default=0)),
                ('consumed_at', models.DateTimeField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='email_verification_otps', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddIndex(
            model_name='emailverificationotp',
            index=models.Index(fields=['user', 'created_at'], name='accounts_ev_user_id_412b80_idx'),
        ),
    ]
