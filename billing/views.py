"""
billing/views.py
----------------
All views for the authenticated Billing Dashboard.

URL layout:
  /billing/login/                     — login
  /billing/logout/                    — logout
  /billing/                           — dashboard (KPIs)
  /billing/open/                      — open bills (active table sessions)
  /billing/bills/<id>/                — bill detail + discount + payment
  /billing/bills/<id>/recalc/         — POST: refresh totals
  /billing/bills/<id>/discount/       — POST: apply discount
  /billing/bills/<id>/discount/remove/— POST: remove discount
  /billing/bills/<id>/payment/        — POST: add a payment
  /billing/bills/<id>/payment/<pid>/delete/ — POST: delete a payment
  /billing/bills/<id>/close/          — POST: close bill
  /billing/history/                   — bill history + filters
  /billing/bills/<id>/receipt/        — printable receipt
  /billing/reports/                   — analytics + charts
"""

import json
from decimal import Decimal, InvalidOperation

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.utils import timezone

from ordering.models import TableSession

from .decorators import billing_required, role_required
from .models import Bill, Payment, StaffProfile
from .services import (
    add_payment, apply_discount, close_bill, delete_payment,
    generate_bill, payment_method_breakdown, recalculate_bill,
    remove_discount, revenue_last_n_days, today_stats, top_items,
)


# ─────────────────────────────────────────────────────────────────────────────
# Auth
# ─────────────────────────────────────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        try:
            if request.user.staff_profile.is_active:
                return redirect('billing:dashboard')
        except AttributeError:
            pass

    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user     = authenticate(request, username=username, password=password)
        if user is None:
            error = 'Invalid username or password.'
        else:
            try:
                profile = user.staff_profile
                if not profile.is_active:
                    error = 'Your account is inactive. Contact the owner.'
                else:
                    login(request, user)
                    next_url = request.GET.get('next', '')
                    return redirect(next_url if next_url.startswith('/billing/') else 'billing:dashboard')
            except StaffProfile.DoesNotExist:
                error = 'You are not registered as billing staff.'

    return render(request, 'billing/login.html', {'error': error})


@require_POST
def logout_view(request):
    logout(request)
    return redirect('billing:login')


# ─────────────────────────────────────────────────────────────────────────────
# Dashboard
# ─────────────────────────────────────────────────────────────────────────────

@billing_required
def dashboard(request):
    profile    = request.user.staff_profile
    restaurant = profile.restaurant
    stats      = today_stats(restaurant)

    # Recent closed bills today
    today = timezone.localdate()
    recent_bills = (
        Bill.objects
        .filter(restaurant=restaurant, status=Bill.STATUS_PAID, paid_at__date=today)
        .order_by('-paid_at')[:8]
    )

    # Active sessions with bill requests
    bill_requests = (
        TableSession.objects
        .filter(table__restaurant=restaurant, status=TableSession.STATUS_OPEN,
                bill_requested_at__isnull=False)
        .select_related('table')
        .order_by('bill_requested_at')
    )

    return render(request, 'billing/dashboard.html', {
        'stats':         stats,
        'recent_bills':  recent_bills,
        'bill_requests': bill_requests,
        'restaurant':    restaurant,
        'profile':       profile,
    })


# ─────────────────────────────────────────────────────────────────────────────
# Open Bills (active table sessions)
# ─────────────────────────────────────────────────────────────────────────────

@billing_required
def open_bills(request):
    profile    = request.user.staff_profile
    restaurant = profile.restaurant

    active_sessions = (
        TableSession.objects
        .filter(table__restaurant=restaurant, status=TableSession.STATUS_OPEN)
        .select_related('table')
        .prefetch_related('customer_sessions', 'bill')
        .order_by('-bill_requested_at', '-started_at')
    )

    # Build context for each session
    rows = []
    for ts in active_sessions:
        bill = None
        try:
            bill = ts.bill
        except Bill.DoesNotExist:
            pass

        elapsed_secs = int((timezone.now() - ts.started_at).total_seconds())
        h, r         = divmod(elapsed_secs, 3600)
        m            = r // 60
        elapsed      = f"{h}h {m}m" if h else f"{m}m"

        rows.append({
            'session':        ts,
            'bill':           bill,
            'elapsed':        elapsed,
            'elapsed_secs':   elapsed_secs,
            'customer_count': ts.customer_sessions.count(),
            'order_total':    ts.session_total,
            'bill_requested': bool(ts.bill_requested_at),
        })

    return render(request, 'billing/open_bills.html', {
        'rows':       rows,
        'restaurant': restaurant,
        'profile':    profile,
    })


# ─────────────────────────────────────────────────────────────────────────────
# Bill Detail
# ─────────────────────────────────────────────────────────────────────────────

@billing_required
def bill_detail(request, session_id):
    profile    = request.user.staff_profile
    restaurant = profile.restaurant

    ts = get_object_or_404(
        TableSession,
        id=session_id,
        table__restaurant=restaurant,
    )

    # Auto-generate bill on first open (idempotent)
    bill = generate_bill(ts, request.user)

    # Build orders grouped by customer session
    customer_groups = []
    for idx, cs in enumerate(ts.customer_sessions.prefetch_related('orders__items__menu_item').all(), 1):
        orders = cs.orders.exclude(status='cancelled').prefetch_related('items__menu_item')
        customer_groups.append({'label': f'Guest {idx}', 'orders': orders})

    payments = bill.payments.select_related('received_by').order_by('paid_at')

    return render(request, 'billing/bill_detail.html', {
        'bill':             bill,
        'ts':               ts,
        'customer_groups':  customer_groups,
        'payments':         payments,
        'payment_methods':  Payment.METHODS,
        'discount_types':   Bill.DISCOUNT_TYPES,
        'restaurant':       restaurant,
        'profile':          profile,
    })


@billing_required
@require_POST
def recalc_bill(request, bill_id):
    profile = request.user.staff_profile
    bill    = get_object_or_404(Bill, id=bill_id, restaurant=profile.restaurant)
    try:
        bill = recalculate_bill(bill)
        return JsonResponse({'status': 'ok', 'grand_total': str(bill.grand_total)})
    except Exception as exc:
        return JsonResponse({'status': 'error', 'message': str(exc)}, status=400)


@billing_required
@require_POST
def apply_discount_view(request, bill_id):
    profile = request.user.staff_profile
    bill    = get_object_or_404(Bill, id=bill_id, restaurant=profile.restaurant)
    try:
        dtype  = request.POST.get('discount_type', '')
        dval   = Decimal(request.POST.get('discount_value', '0'))
        reason = request.POST.get('discount_reason', '').strip()
        if not reason:
            return JsonResponse({'status': 'error', 'message': 'Discount reason is required.'}, status=400)
        bill = apply_discount(bill, dtype, dval, reason, request.user)
        return JsonResponse({
            'status':          'ok',
            'discount_amount': str(bill.discount_amount),
            'tax_amount':      str(bill.tax_amount),
            'grand_total':     str(bill.grand_total),
            'round_off':       str(bill.round_off),
        })
    except (ValueError, InvalidOperation) as exc:
        return JsonResponse({'status': 'error', 'message': str(exc)}, status=400)


@billing_required
@require_POST
def remove_discount_view(request, bill_id):
    profile = request.user.staff_profile
    bill    = get_object_or_404(Bill, id=bill_id, restaurant=profile.restaurant)
    try:
        bill = remove_discount(bill)
        return JsonResponse({'status': 'ok', 'grand_total': str(bill.grand_total)})
    except ValueError as exc:
        return JsonResponse({'status': 'error', 'message': str(exc)}, status=400)


@billing_required
@require_POST
def add_payment_view(request, bill_id):
    profile = request.user.staff_profile
    bill    = get_object_or_404(Bill, id=bill_id, restaurant=profile.restaurant)
    try:
        method = request.POST.get('payment_method', '')
        amount = Decimal(request.POST.get('amount', '0'))
        ref    = request.POST.get('transaction_ref', '').strip()
        pmt    = add_payment(bill, method, amount, ref, request.user)
        bill.refresh_from_db()
        return JsonResponse({
            'status':      'ok',
            'payment_id':  pmt.id,
            'method':      pmt.get_payment_method_display(),
            'amount':      str(pmt.amount),
            'amount_paid': str(bill.amount_paid),
            'amount_due':  str(bill.amount_due),
        })
    except (ValueError, InvalidOperation) as exc:
        return JsonResponse({'status': 'error', 'message': str(exc)}, status=400)


@billing_required
@require_POST
def delete_payment_view(request, bill_id, payment_id):
    profile = request.user.staff_profile
    bill    = get_object_or_404(Bill, id=bill_id, restaurant=profile.restaurant)
    pmt     = get_object_or_404(Payment, id=payment_id, bill=bill)
    try:
        delete_payment(pmt)
        bill.refresh_from_db()
        return JsonResponse({'status': 'ok', 'amount_due': str(bill.amount_due)})
    except ValueError as exc:
        return JsonResponse({'status': 'error', 'message': str(exc)}, status=400)


@billing_required
@require_POST
def close_bill_view(request, bill_id):
    profile = request.user.staff_profile
    bill    = get_object_or_404(Bill, id=bill_id, restaurant=profile.restaurant)
    try:
        close_bill(bill)
        return JsonResponse({'status': 'ok', 'bill_number': bill.bill_number})
    except ValueError as exc:
        return JsonResponse({'status': 'error', 'message': str(exc)}, status=400)


# ─────────────────────────────────────────────────────────────────────────────
# Receipt
# ─────────────────────────────────────────────────────────────────────────────

@billing_required
def receipt_view(request, bill_id):
    profile = request.user.staff_profile
    bill    = get_object_or_404(Bill, id=bill_id, restaurant=profile.restaurant)

    customer_groups = []
    for idx, cs in enumerate(
        bill.table_session.customer_sessions
        .prefetch_related('orders__items__menu_item').all(), 1
    ):
        orders = cs.orders.exclude(status='cancelled').prefetch_related('items__menu_item')
        customer_groups.append({'label': f'Guest {idx}', 'orders': orders})

    payments = bill.payments.all()

    return render(request, 'billing/receipt.html', {
        'bill':            bill,
        'customer_groups': customer_groups,
        'payments':        payments,
        'restaurant':      profile.restaurant,
    })


# ─────────────────────────────────────────────────────────────────────────────
# Bill History
# ─────────────────────────────────────────────────────────────────────────────

@billing_required
def history_view(request):
    profile    = request.user.staff_profile
    restaurant = profile.restaurant

    qs = Bill.objects.filter(restaurant=restaurant).select_related('cashier', 'table_session__table')

    # ── Filters ──
    date_filter   = request.GET.get('date', 'today')
    method_filter = request.GET.get('method', '')
    search        = request.GET.get('q', '').strip()
    table_filter  = request.GET.get('table', '').strip()

    today = timezone.localdate()
    import datetime
    if date_filter == 'today':
        qs = qs.filter(created_at__date=today)
    elif date_filter == 'yesterday':
        qs = qs.filter(created_at__date=today - datetime.timedelta(days=1))
    elif date_filter == 'week':
        qs = qs.filter(created_at__date__gte=today - datetime.timedelta(days=7))
    elif date_filter == 'month':
        qs = qs.filter(created_at__date__gte=today - datetime.timedelta(days=30))
    elif date_filter == 'custom':
        from_date = request.GET.get('from', '')
        to_date   = request.GET.get('to', '')
        if from_date:
            qs = qs.filter(created_at__date__gte=from_date)
        if to_date:
            qs = qs.filter(created_at__date__lte=to_date)

    if method_filter:
        qs = qs.filter(payments__payment_method=method_filter).distinct()

    if search:
        qs = qs.filter(bill_number__icontains=search)

    if table_filter:
        qs = qs.filter(table_session__table__table_number__icontains=table_filter)

    bills = qs.order_by('-created_at')[:200]

    date_tabs = [
        ('today',     'Today'),
        ('yesterday', 'Yesterday'),
        ('week',      'This Week'),
        ('month',     'This Month'),
        ('custom',    'Custom'),
    ]

    return render(request, 'billing/history.html', {
        'bills':          bills,
        'restaurant':     restaurant,
        'profile':        profile,
        'date_filter':    date_filter,
        'method_filter':  method_filter,
        'search':         search,
        'table_filter':   table_filter,
        'payment_methods': Payment.METHODS,
        'from_date':      request.GET.get('from', ''),
        'to_date':        request.GET.get('to', ''),
        'date_tabs':      date_tabs,
    })


# ─────────────────────────────────────────────────────────────────────────────
# Reports & Analytics
# ─────────────────────────────────────────────────────────────────────────────

@billing_required
@role_required(['owner', 'manager'])
def reports_view(request):
    profile    = request.user.staff_profile
    restaurant = profile.restaurant

    stats      = today_stats(restaurant)
    rev_7days  = revenue_last_n_days(restaurant, 7)
    rev_30days = revenue_last_n_days(restaurant, 30)
    pay_split  = payment_method_breakdown(restaurant, 30)
    items      = top_items(restaurant, limit=10, period_days=30)

    return render(request, 'billing/reports.html', {
        'stats':          stats,
        'rev_7days':      json.dumps(rev_7days),
        'rev_30days':     json.dumps(rev_30days),
        'pay_labels':     json.dumps(pay_split['labels']),
        'pay_values':     json.dumps(pay_split['values']),
        'top_items':      items,
        'restaurant':     restaurant,
        'profile':        profile,
    })
