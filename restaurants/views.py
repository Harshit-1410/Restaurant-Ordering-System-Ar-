"""
restaurants/views.py
--------------------
Menu page and item detail JSON endpoint.

QR flow (new):
  Customer scans QR → /{slug}/?t={token}
  The menu view validates the token, creates/reuses a TableSession and
  CustomerSession, and stores the CustomerSession PK in the Django session.
  All subsequent cart/order requests use that session — no URL params required.
"""

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import ensure_csrf_cookie

from .models import MenuItem, Restaurant


@ensure_csrf_cookie
def menu(request, restaurant_slug):
    """
    Main menu page.

    Handles two cases:
      ?t=<token>  — QR code scanned; validate token, join / create table session.
      (no token)  — Direct access; show menu in browse-only mode (can't order).
    """
    from ordering.session import get_active_customer_session, join_table

    restaurant = get_object_or_404(Restaurant, slug=restaurant_slug, is_active=True)
    categories = restaurant.categories.prefetch_related('items').all()

    qr_error   = None
    qr_token   = request.GET.get('t', '').strip()

    if qr_token:
        _, error = join_table(request, qr_token)
        if error:
            qr_error = (
                'This QR code is invalid or has expired. '
                'Please ask staff for a new code.'
            )

    # Determine whether the current browser has an active ordering session
    cs             = get_active_customer_session(request)
    has_session    = cs is not None
    bill_requested = bool(cs.table_session.bill_requested_at) if cs else False
    table_number   = cs.table_session.table_number if cs else None

    return render(request, 'restaurants/menu.html', {
        'restaurant':    restaurant,
        'categories':    categories,
        'bill_requested': bill_requested,
        'has_session':   has_session,
        'table_number':  table_number,
        'qr_error':      qr_error,
    })


def menu_item_detail(request, item_id):
    """GET /item/<item_id>/detail/ — JSON payload for the item detail modal."""
    item = get_object_or_404(MenuItem, id=item_id, is_available=True)

    def safe_url(field):
        try:
            return field.url if field else None
        except Exception:
            return None

    return JsonResponse({
        'id':           item.id,
        'name':         item.name,
        'description':  item.description,
        'price':        str(item.price),
        'category':     item.category.name,
        'is_veg':       item.is_veg,
        'image':        safe_url(item.image),
        'ar_glb':       safe_url(item.ar_model_file),
        'ar_usdz':      safe_url(item.ar_model_usdz),
        'ar_has_model': item.ar_has_model,
    })
