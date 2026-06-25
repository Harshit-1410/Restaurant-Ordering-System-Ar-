import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('ordering', '0005_finalize_schema'),
        ('restaurants', '0004_alter_menuitem_ar_model_file_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # ── StaffProfile ──────────────────────────────────────────────────────
        migrations.CreateModel(
            name='StaffProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role',       models.CharField(choices=[('owner','Owner'),('manager','Manager'),('cashier','Cashier')], default='cashier', max_length=20)),
                ('is_active',  models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('restaurant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='staff', to='restaurants.restaurant')),
                ('user',       models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='staff_profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),

        # ── Bill ──────────────────────────────────────────────────────────────
        migrations.CreateModel(
            name='Bill',
            fields=[
                ('id',             models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bill_number',    models.CharField(editable=False, max_length=30, unique=True)),
                ('subtotal',       models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('tax_percentage', models.DecimalField(decimal_places=2, default=5, max_digits=5)),
                ('tax_amount',     models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('service_charge', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('discount_type',  models.CharField(blank=True, choices=[('percent','Percentage (%)'),('flat','Flat Amount (₹)')], default='', max_length=10)),
                ('discount_value',  models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('discount_amount', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('discount_reason', models.TextField(blank=True)),
                ('discount_at',     models.DateTimeField(blank=True, null=True)),
                ('round_off',       models.DecimalField(decimal_places=2, default=0, max_digits=6)),
                ('grand_total',     models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('status',          models.CharField(choices=[('draft','Draft'),('paid','Paid'),('void','Void')], default='draft', max_length=10)),
                ('customer_count',  models.PositiveIntegerField(default=0)),
                ('notes',           models.TextField(blank=True)),
                ('created_at',      models.DateTimeField(auto_now_add=True)),
                ('paid_at',         models.DateTimeField(blank=True, null=True)),
                ('cashier',         models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='bills_processed', to=settings.AUTH_USER_MODEL)),
                ('discount_by',     models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='discounts_applied', to=settings.AUTH_USER_MODEL)),
                ('restaurant',      models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='bills', to='restaurants.restaurant')),
                ('table_session',   models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='bill', to='ordering.tablesession')),
            ],
            options={'ordering': ['-created_at']},
        ),

        # ── Payment ───────────────────────────────────────────────────────────
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id',              models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('payment_method',  models.CharField(choices=[('cash','Cash'),('upi','UPI'),('credit_card','Credit Card'),('debit_card','Debit Card')], max_length=20)),
                ('amount',          models.DecimalField(decimal_places=2, max_digits=10)),
                ('transaction_ref', models.CharField(blank=True, max_length=100)),
                ('paid_at',         models.DateTimeField(auto_now_add=True)),
                ('bill',            models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='payments', to='billing.bill')),
                ('received_by',     models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='payments_received', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
