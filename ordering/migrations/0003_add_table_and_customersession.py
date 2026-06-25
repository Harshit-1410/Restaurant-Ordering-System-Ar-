"""
Migration 0003 — Add Table and CustomerSession; prepare TableSession/Cart/Order for
the new schema without removing any existing columns yet (backward-safe).

Steps:
  1. Create Table model.
  2. Rename TableSession.created_at → started_at.
  3. Add TableSession.{table, status, ended_at}.
  4. Create CustomerSession model.
  5. Add nullable Cart.customer_session.
  6. Add nullable Order.customer_session.
"""

import django.db.models.deletion
import ordering.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ordering', '0002_tablesession_bill_requested_at_and_more'),
        ('restaurants', '0004_alter_menuitem_ar_model_file_and_more'),
    ]

    operations = [
        # ── 1. Table model ────────────────────────────────────────────────────
        migrations.CreateModel(
            name='Table',
            fields=[
                ('id', models.BigAutoField(
                    auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
                )),
                ('table_number', models.CharField(max_length=20)),
                ('qr_token', models.CharField(
                    default=ordering.models._generate_qr_token, max_length=64, unique=True
                )),
                ('is_active', models.BooleanField(default=True)),
                ('restaurant', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='tables',
                    to='restaurants.restaurant',
                )),
            ],
            options={
                'ordering': ['table_number'],
                'unique_together': {('restaurant', 'table_number')},
            },
        ),

        # ── 2. Rename created_at → started_at on TableSession ─────────────────
        migrations.RenameField(
            model_name='tablesession',
            old_name='created_at',
            new_name='started_at',
        ),

        # ── 3. New fields on TableSession ─────────────────────────────────────
        migrations.AddField(
            model_name='tablesession',
            name='table',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='sessions',
                to='ordering.table',
            ),
        ),
        migrations.AddField(
            model_name='tablesession',
            name='status',
            field=models.CharField(
                choices=[('open', 'Open'), ('paid', 'Paid'), ('closed', 'Closed')],
                default='open',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='tablesession',
            name='ended_at',
            field=models.DateTimeField(blank=True, null=True),
        ),

        # ── 4. CustomerSession model ──────────────────────────────────────────
        migrations.CreateModel(
            name='CustomerSession',
            fields=[
                ('id', models.BigAutoField(
                    auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
                )),
                ('browser_uuid', models.CharField(max_length=64)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('last_seen', models.DateTimeField(auto_now=True)),
                ('table_session', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='customer_sessions',
                    to='ordering.tablesession',
                )),
            ],
            options={
                'ordering': ['created_at'],
                'unique_together': {('table_session', 'browser_uuid')},
            },
        ),

        # ── 5. Nullable customer_session on Cart ──────────────────────────────
        migrations.AddField(
            model_name='cart',
            name='customer_session',
            field=models.OneToOneField(
                blank=True, null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='cart',
                to='ordering.customersession',
            ),
        ),

        # ── 6. Nullable customer_session on Order ─────────────────────────────
        migrations.AddField(
            model_name='order',
            name='customer_session',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='orders',
                to='ordering.customersession',
            ),
        ),
    ]
