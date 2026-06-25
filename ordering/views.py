import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from restaurants.models import MenuItem, Restaurant
from .models import Order, OrderItem, Cart, CartItem, TableSession


def get_or_create_cart(request, restaurant):
    session_key = f'table_session_{restaurant.id}'
    session_id = request.session.get(session_key)

    if session_id:
        try:
            table_session = TableSession.objects.get(id=session_id, is_active=True)
        except TableSession.DoesNotExist:
            table_session = TableSession.objects.create(
                restaurant=restaurant,
                table_number=request.GET.get('table', '1')
            )
            request.session[session_key] = table_session.id
    else:
        table_session = TableSession.objects.create(
            restaurant=restaurant,
            table_number=request.GET.get('table', '1')
        )
        request.session[session_key] = table_session.id

    cart, _ = Cart.objects.get_or_create(session=table_session)
    return cart


def cart_data(request):
    restaurant_id = None
    for key in request.session.keys():
        if key.startswith('table_session_'):
            restaurant_id = key.replace('table_session_', '')
            break

    if not restaurant_id:
        return JsonResponse({'total_items': 0, 'total_price': '0.00'})

    try:
        restaurant = Restaurant.objects.get(id=restaurant_id)
        cart = get_or_create_cart(request, restaurant)
        cart_items = cart.items.select_related('menu_item').all()
        total_items = sum(i.quantity for i in cart_items)
        total_price = sum(i.subtotal for i in cart_items)
        return JsonResponse({'total_items': total_items, 'total_price': str(total_price)})
    except Exception:
        return JsonResponse({'total_items': 0, 'total_price': '0.00'})


@require_POST
def cart_add(request):
    try:
        data = json.loads(request.body)
        item_id = data.get('item_id')
        quantity = int(data.get('quantity', 1))

        menu_item = get_object_or_404(MenuItem, id=item_id, is_available=True)
        cart = get_or_create_cart(request, menu_item.restaurant)
        if cart.session.bill_requested_at:
            return JsonResponse({'status': 'error', 'message': 'Cannot add items after requesting the bill.'}, status=400)

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            menu_item=menu_item,
            defaults={'quantity': quantity}
        )
        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        cart_items = cart.items.select_related('menu_item').all()
        total_items = sum(i.quantity for i in cart_items)
        total_price = sum(i.subtotal for i in cart_items)
        return JsonResponse({
            'status': 'ok',
            'total_items': total_items,
            'total_price': str(total_price)
        })

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


def cart_detail(request):
    restaurant_id = None
    for key in request.session.keys():
        if key.startswith('table_session_'):
            restaurant_id = key.replace('table_session_', '')
            break

    if not restaurant_id:
        return render(request, 'ordering/cart.html', {'cart_items': [], 'total': 0})

    try:
        restaurant = Restaurant.objects.get(id=restaurant_id)
        cart = get_or_create_cart(request, restaurant)
        cart_items = cart.items.select_related('menu_item').all()
        total = sum(i.subtotal for i in cart_items)
    except Exception:
        cart_items = []
        total = 0
        restaurant = None

    return render(request, 'ordering/cart.html', {
        'cart_items': cart_items,
        'total': total,
        'restaurant': restaurant,
    })


@require_POST
def cart_remove(request, item_id):
    try:
        cart_item = CartItem.objects.select_related('cart__session').get(id=item_id)
        
        if cart_item.cart.session.bill_requested_at:
            return JsonResponse({'status': 'error', 'message': 'Cannot remove items after requesting the bill.'}, status=400)

        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
        return JsonResponse({'status': 'ok'})
    except CartItem.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Item not found'}, status=404)


@require_POST
def place_order(request):
    try:
        restaurant_id = None
        for key in request.session.keys():
            if key.startswith('table_session_'):
                restaurant_id = key.replace('table_session_', '')
                break

        restaurant = get_object_or_404(Restaurant, id=restaurant_id)
        cart = get_or_create_cart(request, restaurant)
        
        if cart.session.bill_requested_at:
            return JsonResponse({'status': 'error', 'message': 'Cannot place new orders after requesting the bill.'}, status=400)

        cart_items = cart.items.select_related('menu_item').all()

        if not cart_items.exists():
            return JsonResponse({'status': 'error', 'message': 'Cart is empty'}, status=400)

        total = sum(i.subtotal for i in cart_items)

        order = Order.objects.create(
            restaurant=restaurant,
            table_session=cart.session,
            total_amount=total,
            status='pending',
        )

        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                menu_item=cart_item.menu_item,
                quantity=cart_item.quantity,
                unit_price=cart_item.menu_item.price,
                notes=cart_item.notes,
            )

        cart_items.delete()

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'kitchen_{restaurant.id}',
            {
                'type': 'new_order',
                'order_id': order.id,
                'table': cart.session.table_number,
                'items': [
                    {
                        'name': oi.menu_item.name,
                        'quantity': oi.quantity,
                        'notes': oi.notes,
                    }
                    for oi in order.items.select_related('menu_item').all()
                ],
                'total': str(order.total_amount),
                'status': order.status,
            }
        )

        return JsonResponse({'status': 'ok', 'order_id': order.id})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'ordering/confirmation.html', {'order': order})


def kitchen_dashboard(request, restaurant_id):
    from django.utils import timezone
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    today = timezone.localdate()
    active_orders = Order.objects.filter(
        restaurant=restaurant,
        created_at__date=today,
    ).exclude(
        status='cancelled'
    ).prefetch_related('items__menu_item').order_by('-created_at')

    bill_requests = TableSession.objects.filter(
        restaurant=restaurant,
        is_paid=False,
        bill_requested_at__isnull=False
    ).order_by('bill_requested_at')

    return render(request, 'ordering/kitchen.html', {
        'restaurant': restaurant,
        'active_orders': active_orders,
        'bill_requests': bill_requests,
    })


@require_POST
def update_order_status(request):
    try:
        data = json.loads(request.body)
        order = get_object_or_404(Order, id=data['order_id'])
        order.status = data['status']
        order.save()

        # Broadcast to the per-order group so the customer sees it live
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"order_{order.id}",
            {
                'type': 'order_status_changed',
                'order_id': order.id,
                'status': order.status,
            }
        )

        return JsonResponse({'status': 'ok'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@require_POST
def request_bill(request):
    """Customer taps ‘Request Bill’. Sets bill_requested_at on the current TableSession."""
    from django.utils import timezone
    try:
        # Find the active session from the Django session store
        restaurant_id = None
        for key in request.session.keys():
            if key.startswith('table_session_'):
                restaurant_id = key.replace('table_session_', '')
                break

        if not restaurant_id:
            return JsonResponse({'status': 'no_session', 'message': 'No active table session.'}, status=400)

        session_id = request.session.get(f'table_session_{restaurant_id}')
        table_session = TableSession.objects.get(id=session_id, is_active=True)

        if not table_session.order_set.exclude(status='cancelled').exists():
            return JsonResponse({'status': 'no_orders', 'message': 'Please place an order before requesting the bill.'}, status=400)

        if table_session.bill_requested_at:
            # Already requested — idempotent, still return success to the UI
            return JsonResponse({'status': 'already_requested'})

        table_session.bill_requested_at = timezone.now()
        table_session.save(update_fields=['bill_requested_at'])

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'kitchen_{restaurant_id}',
            {
                'type': 'bill_requested',
                'session_id': table_session.id,
                'table': table_session.table_number,
                'time': table_session.bill_requested_at.isoformat(),
            }
        )

        return JsonResponse({'status': 'ok'})

    except TableSession.DoesNotExist:
        return JsonResponse({'status': 'no_session', 'message': 'Session not found or inactive.'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


def billing_dashboard(request, restaurant_id):
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    
    # All active sessions
    active_sessions = TableSession.objects.filter(
        restaurant=restaurant,
        is_active=True
    ).prefetch_related('order_set').order_by('-bill_requested_at', '-created_at')

    return render(request, 'ordering/billing.html', {
        'restaurant': restaurant,
        'sessions': active_sessions,
    })


def bill_detail_data(request, session_id):
    """Returns JSON breakdown of all non-cancelled orders in a session."""
    table_session = get_object_or_404(TableSession, id=session_id)
    orders = table_session.order_set.exclude(status='cancelled').prefetch_related('items__menu_item')
    
    items_breakdown = []
    for order in orders:
        for oi in order.items.all():
            items_breakdown.append({
                'name': oi.menu_item.name,
                'quantity': oi.quantity,
                'unit_price': str(oi.unit_price),
                'subtotal': str(oi.subtotal),
            })
            
    return JsonResponse({
        'session_id': table_session.id,
        'table_number': table_session.table_number,
        'total_amount': str(table_session.session_total),
        'items': items_breakdown,
        'bill_requested': bool(table_session.bill_requested_at),
        'is_paid': table_session.is_paid,
    })


@require_POST
def close_table_session(request, session_id):
    """Marks table as paid, closed, and inactive. Broadcasts event."""
    from django.utils import timezone
    try:
        table_session = get_object_or_404(TableSession, id=session_id, is_active=True)
        table_session.is_paid = True
        table_session.closed_at = timezone.now()
        table_session.is_active = False
        table_session.save(update_fields=['is_paid', 'closed_at', 'is_active'])

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'kitchen_{table_session.restaurant.id}',
            {
                'type': 'table_closed',
                'session_id': table_session.id,
                'table': table_session.table_number,
            }
        )
        return JsonResponse({'status': 'ok'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


def table_session_bill(request, session_id):
    """Full-page view for a combined bill of a TableSession."""
    table_session = get_object_or_404(TableSession, id=session_id)
    
    # Exclude cancelled orders
    orders = table_session.order_set.exclude(status='cancelled').prefetch_related('items__menu_item').order_by('created_at')
    
    subtotal = sum(order.total_amount for order in orders)
    
    # Calculate 5% GST
    from decimal import Decimal
    gst = subtotal * Decimal('0.05')
    grand_total = subtotal + gst
    
    return render(request, 'ordering/session_bill.html', {
        'table_session': table_session,
        'orders': orders,
        'subtotal': subtotal,
        'gst': gst,
        'grand_total': grand_total,
    })


def session_orders(request):
    """Returns all orders placed in the current session as JSON."""
    restaurant_id = None
    for key in request.session.keys():
        if key.startswith('table_session_'):
            restaurant_id = key.replace('table_session_', '')
            break

    if not restaurant_id:
        return JsonResponse({'orders': []})

    session_key = f'table_session_{restaurant_id}'
    session_id = request.session.get(session_key)
    if not session_id:
        return JsonResponse({'orders': []})

    try:
        table_session = TableSession.objects.get(id=session_id, is_active=True)
        orders = Order.objects.filter(table_session=table_session).order_by('-created_at').prefetch_related('items__menu_item')
        orders_data = []
        for order in orders:
            items_data = []
            for item in order.items.all():
                items_data.append({
                    'name': item.menu_item.name,
                    'quantity': item.quantity,
                    'subtotal': str(item.subtotal),
                })
            orders_data.append({
                'id': order.id,
                'status': order.status,
                'total_amount': str(order.total_amount),
                'created_at': order.created_at.isoformat(),
                'items': items_data,
            })
        return JsonResponse({'orders': orders_data})
    except TableSession.DoesNotExist:
        return JsonResponse({'orders': []})