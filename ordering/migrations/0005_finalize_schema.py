"""
Migration 0005 — Finalise schema.

  • Make the new FKs non-nullable (all rows were populated in migration 0004).
  • Remove the legacy columns that are now derivable from the new relationships:
      TableSession: restaurant, table_number, session_token, is_active, is_paid, closed_at
      Cart:         session
      Order:        restaurant, table_session
"""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ordering', '0004_data_migration'),
    ]

    operations = [
        # ── Make FKs non-nullable ─────────────────────────────────────────────
        migrations.AlterField(
            model_name='tablesession',
            name='table',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='sessions',
                to='ordering.table',
            ),
        ),
        migrations.AlterField(
            model_name='cart',
            name='customer_session',
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='cart',
                to='ordering.customersession',
            ),
        ),
        migrations.AlterField(
            model_name='order',
            name='customer_session',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='orders',
                to='ordering.customersession',
            ),
        ),

        # ── Remove legacy TableSession columns ────────────────────────────────
        migrations.RemoveField(model_name='tablesession', name='restaurant'),
        migrations.RemoveField(model_name='tablesession', name='table_number'),
        migrations.RemoveField(model_name='tablesession', name='session_token'),
        migrations.RemoveField(model_name='tablesession', name='is_active'),
        migrations.RemoveField(model_name='tablesession', name='is_paid'),
        migrations.RemoveField(model_name='tablesession', name='closed_at'),

        # ── Remove legacy Cart.session column ─────────────────────────────────
        migrations.RemoveField(model_name='cart', name='session'),

        # ── Remove legacy Order columns ───────────────────────────────────────
        migrations.RemoveField(model_name='order', name='restaurant'),
        migrations.RemoveField(model_name='order', name='table_session'),
    ]
