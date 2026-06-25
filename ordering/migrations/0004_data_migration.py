"""
Migration 0004 — Data migration.

For each existing TableSession:
  1. Create one Table per (restaurant, table_number) pair, generating a fresh QR token.
  2. Link the TableSession to its Table and sync status from the old boolean fields.
  3. Create one legacy CustomerSession for the TableSession.
  4. Re-link the existing Cart (if any) to the new CustomerSession.
  5. Re-link all existing Orders to the new CustomerSession.
"""

import secrets

from django.db import migrations


def forwards(apps, schema_editor):
    Table           = apps.get_model('ordering', 'Table')
    TableSession    = apps.get_model('ordering', 'TableSession')
    CustomerSession = apps.get_model('ordering', 'CustomerSession')
    Cart            = apps.get_model('ordering', 'Cart')
    Order           = apps.get_model('ordering', 'Order')

    # (restaurant_id, table_number) → Table instance
    table_map: dict = {}

    for ts in TableSession.objects.select_related('restaurant').all():
        key = (ts.restaurant_id, ts.table_number)

        if key not in table_map:
            table = Table.objects.create(
                restaurant_id=ts.restaurant_id,
                table_number=ts.table_number,
                qr_token=secrets.token_urlsafe(24),
                is_active=True,
            )
            table_map[key] = table
        else:
            table = table_map[key]

        # Sync status from old boolean fields
        if ts.is_paid:
            new_status = 'paid'
        elif not ts.is_active:
            new_status = 'closed'
        else:
            new_status = 'open'

        ts.table    = table
        ts.status   = new_status
        ts.ended_at = ts.closed_at  # may be None
        ts.save(update_fields=['table', 'status', 'ended_at'])

        # One legacy CustomerSession represents the pre-migration "anonymous" customer
        cs = CustomerSession.objects.create(
            table_session=ts,
            browser_uuid=f'legacy_{ts.id}',
        )

        # Re-link Cart
        try:
            cart = Cart.objects.get(session=ts)
            cart.customer_session = cs
            cart.save(update_fields=['customer_session'])
        except Cart.DoesNotExist:
            pass

        # Re-link Orders (bulk update for efficiency)
        Order.objects.filter(table_session=ts).update(customer_session=cs)


def backwards(apps, schema_editor):
    # Not reversible — the new Table and CustomerSession rows
    # would need to be deleted and old FKs restored.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('ordering', '0003_add_table_and_customersession'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
