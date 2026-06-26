import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Extend StaffProfile.role choices to include 'kitchen'
        # (CharField; no DB-level change needed — choices are purely cosmetic in Django)
        migrations.AlterField(
            model_name='staffprofile',
            name='role',
            field=models.CharField(
                choices=[
                    ('owner',   'Owner'),
                    ('manager', 'Manager'),
                    ('cashier', 'Cashier'),
                    ('kitchen', 'Kitchen Staff'),
                ],
                default='cashier',
                max_length=20,
            ),
        ),

        # New StaffAuditLog model
        migrations.CreateModel(
            name='StaffAuditLog',
            fields=[
                ('id',                 models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action',             models.CharField(choices=[('login','Login'),('logout','Logout'),('login_failed','Login Failed')], max_length=20)),
                ('username_attempted', models.CharField(blank=True, max_length=150)),
                ('ip_address',         models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent',         models.TextField(blank=True)),
                ('timestamp',          models.DateTimeField(auto_now_add=True)),
                ('staff_profile',      models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='audit_logs', to='billing.staffprofile')),
            ],
            options={'ordering': ['-timestamp']},
        ),
    ]
