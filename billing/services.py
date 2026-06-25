"""
billing/services.py
-------------------
Stateless service functions for the billing lifecycle.
All business logic lives here — views are thin wrappers.

Functions:
  calculate_totals(bill)          → dict of computed amounts
  generate_bill(table_session, cashier) → Bill
  recalculate_bill(bill)          → Bill (saved)
  apply_discount(bill, ...)       → Bill
  add_payment(bill, ...)          → Payment
  close_bill(bill)                → Bill
"""

from decimal import Decimal, ROUND_HALF_UP

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction
from django.db.models import Avg, Sum
from django.utils import timezone

from ordering.models import Order, TableSession

from .models import Bill, Payment


# ─────────────────────────────────────────────────────────────────────────────
# Amount calculation
# ─────────────────────────────────────────────────────────────────────────────

def calculate_totals(bill: Bill) -> dict:
    """
    Compute all billing totals from the current state of *bill*.
    Does NOT save.  Returns a dict ready to be applied to the bill instance.
    """
    ts = bill.table_session

    subtotal = (
        Order.objects
        .filter(customer_session__table_session=ts)
        .exclude(status='cancelled')
        .aggregate(total=Sum('total_amount'))
    )['total'] or Decimal('0')

    # ── Discount ──
    if bill.discount_type == Bill.DISCOUNT_PERCENT:
        discount = (subtotal * bill.discount_value / Decimal('100')).quantize(Decimal('0.01'))
    elif bill.discount_type == Bill.DISCOUNT_FLAT:
        discount = min(bill.discount_value, subtotal)
    else:
        discount = Decimal('0')

    after_discount = subtotal - discount

    # ── Tax ──
    tax = (after_discount * bill.tax_percentage / Decimal('100')).quantize(Decimal('0.01'))

    # ── Service charge ──
    svc = bill.service_charge

    pre_round   = after_discount + tax + svc
    rounded     = pre_round.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    round_off   = rounded - pre_round

    return {
        'subtotal':        subtotal,
        'discount_amount': discount,
        'tax_amount':      tax,
        'round_off':       round_off,
        'grand_total':     rounded,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Bill lifecycle
# ─────────────────────────────────────────────────────────────────────────────

@transaction.atomic
def generate_bill(table_session: TableSession, cashier, tax_pct: Decimal = Decimal('5')) -> Bill:
    """
    Create a Draft Bill for *table_session*.
    Idempotent — returns the existing Bill if one already exists.
    """
    try:
        return table_session.bill
    except Bill.DoesNotExist:
        pass

    bill = Bill(
        table_session  = table_session,
        restaurant     = table_session.restaurant,
        cashier        = cashier,
        tax_percentage = tax_pct,
        customer_count = table_session.customer_sessions.count(),
    )
    _apply_totals(bill, calculate_totals(bill))
    bill.save()
    return bill


@transaction.atomic
def recalculate_bill(bill: Bill) -> Bill:
    """Recompute totals and save (e.g. after orders are added while bill is open)."""
    _guard_paid(bill)
    _apply_totals(bill, calculate_totals(bill))
    bill.save()
    return bill


@transaction.atomic
def apply_discount(
    bill: Bill,
    discount_type: str,
    discount_value: Decimal,
    reason: str,
    applied_by,
) -> Bill:
    """Apply (or replace) a discount on a draft bill."""
    _guard_paid(bill)
    bill.discount_type   = discount_type
    bill.discount_value  = discount_value
    bill.discount_reason = reason
    bill.discount_by     = applied_by
    bill.discount_at     = timezone.now()
    _apply_totals(bill, calculate_totals(bill))
    bill.save()
    return bill


@transaction.atomic
def remove_discount(bill: Bill) -> Bill:
    """Remove any existing discount."""
    _guard_paid(bill)
    bill.discount_type   = ''
    bill.discount_value  = Decimal('0')
    bill.discount_amount = Decimal('0')
    bill.discount_reason = ''
    bill.discount_by     = None
    bill.discount_at     = None
    _apply_totals(bill, calculate_totals(bill))
    bill.save()
    return bill


@transaction.atomic
def add_payment(
    bill: Bill,
    method: str,
    amount: Decimal,
    ref: str,
    received_by,
) -> Payment:
    """Record a payment against a draft bill."""
    _guard_paid(bill)
    if amount <= 0:
        raise ValueError("Payment amount must be positive.")
    return Payment.objects.create(
        bill=bill,
        payment_method=method,
        amount=amount,
        transaction_ref=ref,
        received_by=received_by,
    )


@transaction.atomic
def delete_payment(payment: Payment) -> None:
    """Remove a payment (only allowed while bill is draft)."""
    _guard_paid(payment.bill)
    payment.delete()


@transaction.atomic
def close_bill(bill: Bill) -> Bill:
    """
    Mark the bill as PAID and close the underlying TableSession.
    Raises ValueError if the bill is already paid or payment is incomplete.
    """
    _guard_paid(bill)
    if bill.amount_due > Decimal('0.50'):   # allow 50 paise rounding tolerance
        raise ValueError(f"Payment incomplete — ₹{bill.amount_due} still due.")

    bill.status  = Bill.STATUS_PAID
    bill.paid_at = timezone.now()
    bill.save(update_fields=['status', 'paid_at'])

    # Close the ordering TableSession if still open
    ts = bill.table_session
    if ts.status == TableSession.STATUS_OPEN:
        ts.close(paid=True)

    # Notify kitchen / billing WebSocket
    try:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'kitchen_{ts.restaurant.id}',
            {
                'type':       'table_closed',
                'session_id': ts.id,
                'table':      ts.table_number,
            }
        )
    except Exception:
        pass  # non-critical

    return bill


# ─────────────────────────────────────────────────────────────────────────────
# Analytics helpers
# ─────────────────────────────────────────────────────────────────────────────

def today_stats(restaurant) -> dict:
    today = timezone.localdate()
    paid_today = Bill.objects.filter(
        restaurant=restaurant, status=Bill.STATUS_PAID, paid_at__date=today
    )
    revenue = paid_today.aggregate(total=Sum('grand_total'))['total'] or Decimal('0')
    bills   = paid_today.count()
    avg     = paid_today.aggregate(avg=Avg('grand_total'))['avg'] or Decimal('0')

    open_sessions = TableSession.objects.filter(
        table__restaurant=restaurant, status=TableSession.STATUS_OPEN
    )
    open_bills         = Bill.objects.filter(restaurant=restaurant, status=Bill.STATUS_DRAFT).count()
    waiting_payment    = open_sessions.filter(bill_requested_at__isnull=False).count()
    tables_occupied    = open_sessions.count()
    customers_served   = (
        Bill.objects.filter(restaurant=restaurant, status=Bill.STATUS_PAID, paid_at__date=today)
        .aggregate(total=Sum('customer_count'))['total'] or 0
    )

    return {
        'today_revenue':      revenue,
        'today_bills':        bills,
        'avg_bill_value':     avg,
        'open_bills':         open_bills,
        'waiting_payment':    waiting_payment,
        'tables_occupied':    tables_occupied,
        'customers_served':   customers_served,
    }


def revenue_last_n_days(restaurant, n: int = 7) -> list:
    """Returns list of (date_str, revenue) for charting."""
    import datetime

    today = timezone.localdate()
    rows  = []
    for i in range(n - 1, -1, -1):
        d   = today - datetime.timedelta(days=i)
        rev = (
            Bill.objects
            .filter(restaurant=restaurant, status=Bill.STATUS_PAID, paid_at__date=d)
            .aggregate(total=Sum('grand_total'))['total'] or 0
        )
        rows.append({'date': d.strftime('%d %b'), 'revenue': float(rev)})
    return rows


def payment_method_breakdown(restaurant, period_days: int = 30) -> dict:
    import datetime

    since = timezone.now() - datetime.timedelta(days=period_days)
    qs    = (
        Payment.objects
        .filter(bill__restaurant=restaurant, bill__status=Bill.STATUS_PAID, paid_at__gte=since)
        .values('payment_method')
        .annotate(total=Sum('amount'))
    )
    labels = []
    values = []
    for row in qs:
        labels.append(dict(Payment.METHODS).get(row['payment_method'], row['payment_method']))
        values.append(float(row['total']))
    return {'labels': labels, 'values': values}


def top_items(restaurant, limit: int = 10, period_days: int = 30) -> list:
    import datetime
    from ordering.models import OrderItem

    since = timezone.now() - datetime.timedelta(days=period_days)
    qs = (
        OrderItem.objects
        .filter(
            order__customer_session__table_session__table__restaurant=restaurant,
            order__customer_session__table_session__status=TableSession.STATUS_PAID,
            order__customer_session__table_session__ended_at__gte=since,
        )
        .values('menu_item__name')
        .annotate(total_qty=Sum('quantity'), total_rev=Sum('unit_price'))
        .order_by('-total_qty')[:limit]
    )
    return list(qs)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _guard_paid(bill: Bill) -> None:
    if bill.is_paid:
        raise ValueError("Cannot modify a paid bill.")


def _apply_totals(bill: Bill, totals: dict) -> None:
    for key, value in totals.items():
        setattr(bill, key, value)
