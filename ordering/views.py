"""
ordering/views.py
-----------------
All HTTP endpoints for the ordering flow.

Session model (new):
  request.session['customer_session_id'] → CustomerSession.id

  Never trust ?table= from the URL.
  Always look up the active CustomerSession from the Django server-side session.
"""

import json
from decimal import Decimal

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from billing.decorators import KITCHEN_LOGIN_URL, KITCHEN_ROLES, kitchen_required
from restaurants.models import MenuItem, Restaurant

from .models import Cart, CartItem, CustomerSession, Order, OrderItem, TableSession
from .session import get_active_customer_session


# ─────────────────────────────────────────────────────────────────────────────
# Auth helpers (shared by kitchen login / logout + audit logging)
# ─────────────────────────────────────────────────────────────────────────────

def _get_client_ip(request):
    """Return the real client IP, respecting X-Forwarded-For from proxies."""
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def _log_audit(profile, action, username, request):
    """Write a StaffAuditLog entry. Import is lazy to avoid circular imports."""
    try:
        from billing.models import StaffAuditLog
        StaffAuditLog.objects.create(
            staff_profile=profile,
            action=action,
            username_attempted=username,
            ip_address=_get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
        )
    except Exception:
        pass  # audit logging must never break the request


# ─────────────────────────────────────────────────────────────────────────────
# Kitchen authentication views
# ─────────────────────────────────────────────────────────────────────────────

def kitchen_login_view(request):
    """
    GET  /ordering/kitchen/login/ — render the kitchen login page.
    POST /ordering/kitchen/login/ — authenticate and redirect.
    """
    # Redirect already-authenticated kitchen staff to their dashboard
    if request.user.is_authenticated:
        try:
            profile = request.user.staff_profile
            if profile.is_active and profile.role in KITCHEN_ROLES:
                return redirect('ordering:kitchen', restaurant_id=profile.restaurant.id)
        except Exception:
            pass

    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        remember  = request.POST.get('remember_me')

        user = authenticate(request, username=username, password=password)
        if user is None:
            _log_audit(None, 'login_failed', username, request)
            error = 'Invalid username or password.'
        else:
            profile = getattr(user, 'staff_profile', None)
            if profile is None or not profile.is_active:
                _log_audit(None, 'login_failed', username, request)
                error = 'Account not found or inactive. Contact your manager.'
            elif profile.role not in KITCHEN_ROLES:
                _log_audit(None, 'login_failed', username, request)
                error = 'You do not have access to the Kitchen Dashboard.'
            else:
                login(request, user)
                _log_audit(profile, 'login', username, request)
                if not remember:
                    request.session.set_expiry(0)  # expires on browser close
                else:
                    request.session.set_expiry(60 * 60 * 24 * 30)  # 30 days
                next_url = request.GET.get('next', '')
                if next_url.startswith('/ordering/kitchen/') and 'login' not in next_url:
                    return redirect(next_url)
                return redirect('ordering:kitchen', restaurant_id=profile.restaurant.id)

    return render(request, 'ordering/kitchen_login.html', {'error': error})


def kitchen_logout_view(request):
    """POST /ordering/kitchen/logout/ — log the user out and redirect to kitchen login."""
    if request.user.is_authenticated:
        try:
            profile = request.user.staff_profile
            _log_audit(profile, 'logout', request.user.username, request)
        except Exception:
            pass
    logout(request)
    return redirect(KITCHEN_LOGIN_URL)


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _get_or_create_cart(customer_session: CustomerSession) -> Cart:
    cart, _ = Cart.objects.get_or_create(customer_session=customer_session)
    return cart


def _no_session_error():
    return JsonResponse(
        {
            'status': 'error',
            'message': 'No active table session. Please scan the QR code at your table.',
        },
        status=400,
    )


def _bill_locked_error():
    return JsonResponse(
        {'status': 'error', 'message': 'Cannot make changes after requesting the bill.'},
        status=400,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Cart endpoints
# ─────────────────────────────────────────────────────────────────────────────

def cart_data(request):
    """GET /ordering/cart/data/ — lightweight badge totals."""
    cs = get_active_customer_session(request)
    if not cs:
        return JsonResponse({'total_items': 0, 'total_price': '0.00'})
    try:
        items       = cs.cart.items.select_related('menu_item').all()
        total_items = sum(i.quantity for i in items)
        total_price = sum(i.subtotal for i in items)
        return JsonResponse({'total_items': total_items, 'total_price': str(total_price)})
    except Cart.DoesNotExist:
        return JsonResponse({'total_items': 0, 'total_price': '0.00'})


@require_POST
def cart_add(request):
    """POST /ordering/cart/add/ — add or increment a CartItem."""
    try:
        data     = json.loads(request.body)
        item_id  = data.get('item_id')
        quantity = int(data.get('quantity', 1))

        menu_item = get_object_or_404(MenuItem, id=item_id, is_available=True)

        cs = get_active_customer_session(request)
        if not cs:
            return _no_session_error()
        if cs.table_session.bill_requested_at:
            return _bill_locked_error()

        cart = _get_or_create_cart(cs)
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart, menu_item=menu_item, defaults={'quantity': quantity}
        )
        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        items       = cart.items.select_related('menu_item').all()
        total_items = sum(i.quantity for i in items)
        total_price = sum(i.subtotal for i in items)
        return JsonResponse({'status': 'ok', 'total_items': total_items, 'total_price': str(total_price)})

    except Exception as exc:
        return JsonResponse({'status': 'error', 'message': str(exc)}, status=400)


def cart_detail(request):
    """GET /ordering/cart/ — render the cart page."""
    cs = get_active_customer_session(request)
    if not cs:
        return render(request, 'ordering/cart.html', {
            'cart_items': [], 'total': 0, 'restaurant': None,
        })
    try:
        cart_items = cs.cart.items.select_related('menu_item').all()
        total      = sum(i.subtotal for i in cart_items)
    except Cart.DoesNotExist:
        cart_items = []
        total      = 0

    return render(request, 'ordering/cart.html', {
        'cart_items':    cart_items,
        'total':         total,
        'restaurant':    cs.table_session.table.restaurant,
        'customer_name': cs.customer_name,
    })


@require_POST
def save_customer_name(request):
    """POST /ordering/session/name/ — persist customer_name on the CustomerSession."""
    cs = get_active_customer_session(request)
    if not cs:
        return JsonResponse({'status': 'error', 'message': 'No active session.'}, status=400)
    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()
    except (json.JSONDecodeError, AttributeError):
        name = request.POST.get('name', '').strip()

    if not name:
        return JsonResponse({'status': 'error', 'message': 'Name is required.'}, status=400)

    cs.customer_name = name[:100]
    cs.save(update_fields=['customer_name'])
    return JsonResponse({'status': 'ok', 'name': cs.customer_name})


@require_POST
def cart_remove(request, item_id):
    """POST /ordering/cart/remove/<cart_item_id>/ — decrement or delete a CartItem."""
    try:
        cs = get_active_customer_session(request)
        if not cs:
            return _no_session_error()
        if cs.table_session.bill_requested_at:
            return _bill_locked_error()

        # Verify ownership — the item must belong to THIS customer's cart
        cart_item = get_object_or_404(CartItem, id=item_id, cart__customer_session=cs)

        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()

        return JsonResponse({'status': 'ok'})
    except Exception as exc:
        return JsonResponse({'status': 'error', 'message': str(exc)}, status=400)


# ─────────────────────────────────────────────────────────────────────────────
# Order endpoints
# ─────────────────────────────────────────────────────────────────────────────

@require_POST
def place_order(request):
    """POST /ordering/place/ — convert the cart to an Order and notify kitchen."""
    try:
        cs = get_active_customer_session(request)
        if not cs:
            return _no_session_error()
        if cs.table_session.bill_requested_at:
            return _bill_locked_error()

        cart       = _get_or_create_cart(cs)
        cart_items = cart.items.select_related('menu_item').all()
        if not cart_items.exists():
            return JsonResponse({'status': 'error', 'message': 'Cart is empty.'}, status=400)

        total = sum(i.subtotal for i in cart_items)
        order = Order.objects.create(
            customer_session=cs,
            total_amount=total,
            status='pending',
        )
        for ci in cart_items:
            OrderItem.objects.create(
                order=order,
                menu_item=ci.menu_item,
                quantity=ci.quantity,
                unit_price=ci.menu_item.price,
                notes=ci.notes,
            )
        cart_items.delete()

        ts         = cs.table_session
        restaurant = ts.table.restaurant

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'kitchen_{restaurant.id}',
            {
                'type':                'new_order',
                'order_id':            order.id,
                'table':               ts.table_number,
                'session_id':          ts.id,
                'customer_session_id': cs.id,
                'customer_name':       cs.customer_name,
                'items': [
                    {'name': oi.menu_item.name, 'quantity': oi.quantity, 'notes': oi.notes}
                    for oi in order.items.select_related('menu_item').all()
                ],
                'total':  str(order.total_amount),
                'status': order.status,
            }
        )

        return JsonResponse({'status': 'ok', 'order_id': order.id})

    except Exception as exc:
        return JsonResponse({'status': 'error', 'message': str(exc)}, status=400)


def order_confirmation(request, order_id):
    """GET /ordering/confirmation/<order_id>/ — live order-status page."""
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'ordering/confirmation.html', {'order': order})


def session_orders(request):
    """GET /ordering/session/orders/ — all orders placed by this browser."""
    cs = get_active_customer_session(request)
    if not cs:
        return JsonResponse({'orders': []})

    orders_data = []
    for order in cs.orders.prefetch_related('items__menu_item').order_by('-created_at'):
        orders_data.append({
            'id':           order.id,
            'status':       order.status,
            'total_amount': str(order.total_amount),
            'created_at':   order.created_at.isoformat(),
            'items': [
                {
                    'name':     item.menu_item.name,
                    'quantity': item.quantity,
                    'subtotal': str(item.subtotal),
                }
                for item in order.items.all()
            ],
        })

    return JsonResponse({'orders': orders_data})


# ─────────────────────────────────────────────────────────────────────────────
# Kitchen dashboard
# ─────────────────────────────────────────────────────────────────────────────

@kitchen_required
def kitchen_dashboard(request, restaurant_id):
    """GET /ordering/kitchen/<restaurant_id>/ — real-time kitchen view (staff only)."""
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)

    # Safety: if the authenticated staff belongs to a different restaurant, redirect them.
    try:
        staff_restaurant_id = request.user.staff_profile.restaurant.id
        if staff_restaurant_id != restaurant_id and request.user.staff_profile.role not in ('owner',):
            return redirect('ordering:kitchen', restaurant_id=staff_restaurant_id)
    except Exception:
        pass

    active_sessions = (
        TableSession.objects
        .filter(table__restaurant=restaurant, status=TableSession.STATUS_OPEN)
        .select_related('table')
        .prefetch_related(
            'customer_sessions__orders__items__menu_item',
        )
        .order_by('table__table_number', 'started_at')
    )

    profile = getattr(request.user, 'staff_profile', None)

    return render(request, 'ordering/kitchen.html', {
        'restaurant':      restaurant,
        'active_sessions': active_sessions,
        'profile':         profile,
    })


@require_POST
def update_order_status(request):
    """POST /ordering/status/update/ — change status of an order (kitchen staff only)."""
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'Authentication required.'}, status=401)
    try:
        profile = request.user.staff_profile
        if not profile.is_active or profile.role not in KITCHEN_ROLES:
            return JsonResponse({'status': 'error', 'message': 'Access denied.'}, status=403)
    except Exception:
        return JsonResponse({'status': 'error', 'message': 'Access denied.'}, status=403)
    try:
        data  = json.loads(request.body)
        order = get_object_or_404(Order, id=data['order_id'])
        order.status = data['status']
        order.save()

        restaurant_id = order.restaurant.id
        channel_layer = get_channel_layer()

        # Notify the customer who placed this order
        async_to_sync(channel_layer.group_send)(
            f"order_{order.id}",
            {'type': 'order_status_changed', 'order_id': order.id, 'status': order.status},
        )
        # Notify all kitchen screens (so status moves on every open tab)
        async_to_sync(channel_layer.group_send)(
            f"kitchen_{restaurant_id}",
            {'type': 'order_status_changed', 'order_id': order.id, 'status': order.status},
        )

        return JsonResponse({'status': 'ok'})
    except Exception as exc:
        return JsonResponse({'status': 'error', 'message': str(exc)}, status=400)


# ─────────────────────────────────────────────────────────────────────────────
# Billing & session lifecycle
# ─────────────────────────────────────────────────────────────────────────────

@require_POST
def request_bill(request):
    """POST /ordering/bill/request/ — customer asks for the bill."""
    cs = get_active_customer_session(request)
    if not cs:
        return JsonResponse({'status': 'no_session', 'message': 'No active table session.'}, status=400)

    ts = cs.table_session

    # Must have at least one non-cancelled order across the whole table
    if not Order.objects.filter(
        customer_session__table_session=ts
    ).exclude(status='cancelled').exists():
        return JsonResponse(
            {'status': 'no_orders', 'message': 'Please place an order before requesting the bill.'},
            status=400,
        )

    if ts.bill_requested_at:
        return JsonResponse({'status': 'already_requested'})

    ts.bill_requested_at = timezone.now()
    ts.save(update_fields=['bill_requested_at'])

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'kitchen_{ts.restaurant.id}',
        {
            'type':       'bill_requested',
            'session_id': ts.id,
            'table':      ts.table_number,
            'time':       ts.bill_requested_at.isoformat(),
        }
    )

    return JsonResponse({'status': 'ok'})


def billing_dashboard(request, restaurant_id):
    """GET /ordering/billing/<restaurant_id>/ — staff billing overview."""
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)

    active_sessions = (
        TableSession.objects
        .filter(table__restaurant=restaurant, status=TableSession.STATUS_OPEN)
        .select_related('table')
        .prefetch_related('customer_sessions__orders')
        .order_by('-bill_requested_at', '-started_at')
    )

    return render(request, 'ordering/billing.html', {
        'restaurant': restaurant,
        'sessions':   active_sessions,
    })


def bill_detail_data(request, session_id):
    """GET /ordering/billing/detail/<session_id>/ — JSON bill for a session."""
    ts = get_object_or_404(TableSession, id=session_id)

    orders = (
        Order.objects
        .filter(customer_session__table_session=ts)
        .exclude(status='cancelled')
        .prefetch_related('items__menu_item')
    )

    items_breakdown = [
        {
            'name':       oi.menu_item.name,
            'quantity':   oi.quantity,
            'unit_price': str(oi.unit_price),
            'subtotal':   str(oi.subtotal),
        }
        for order in orders
        for oi in order.items.all()
    ]

    return JsonResponse({
        'session_id':     ts.id,
        'table_number':   ts.table_number,
        'total_amount':   str(ts.session_total),
        'items':          items_breakdown,
        'bill_requested': bool(ts.bill_requested_at),
        'is_paid':        ts.is_paid,
    })


@require_POST
def close_table_session(request, session_id):
    """POST /ordering/billing/close/<session_id>/ — staff marks table as paid."""
    try:
        ts = get_object_or_404(TableSession, id=session_id, status=TableSession.STATUS_OPEN)
        ts.close(paid=True)

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'kitchen_{ts.restaurant.id}',
            {
                'type':       'table_closed',
                'session_id': ts.id,
                'table':      ts.table_number,
            }
        )
        return JsonResponse({'status': 'ok'})
    except Exception as exc:
        return JsonResponse({'status': 'error', 'message': str(exc)}, status=400)


def table_session_bill(request, session_id):
    """GET /ordering/billing/session/<session_id>/ — printable combined bill."""
    ts = get_object_or_404(TableSession, id=session_id)

    orders = (
        Order.objects
        .filter(customer_session__table_session=ts)
        .exclude(status='cancelled')
        .prefetch_related('items__menu_item', 'customer_session')
        .order_by('created_at')
    )

    subtotal    = sum(order.total_amount for order in orders)
    gst         = subtotal * Decimal('0.05')
    grand_total = subtotal + gst

    return render(request, 'ordering/session_bill.html', {
        'table_session': ts,
        'orders':        orders,
        'subtotal':      subtotal,
        'gst':           gst,
        'grand_total':   grand_total,
    })
