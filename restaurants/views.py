from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import ensure_csrf_cookie
from django.http import JsonResponse
from .models import Restaurant, MenuItem


@ensure_csrf_cookie
def menu(request, restaurant_slug):
    from ordering.models import TableSession
    restaurant = get_object_or_404(Restaurant, slug=restaurant_slug, is_active=True)
    categories = restaurant.categories.prefetch_related('items').all()

    bill_requested = False
    session_id = request.session.get(f'table_session_{restaurant.id}')
    if session_id:
        try:
            table_session = TableSession.objects.get(id=session_id, is_active=True)
            bill_requested = bool(table_session.bill_requested_at)
        except TableSession.DoesNotExist:
            pass

    return render(request, 'restaurants/menu.html', {
        'restaurant': restaurant,
        'categories': categories,
        'bill_requested': bill_requested,
    })

def menu_item_detail(request, item_id):
    """JSON endpoint — returns all data needed for the item detail modal."""
    item = get_object_or_404(MenuItem, id=item_id, is_available=True)
    return JsonResponse({
        'id':          item.id,
        'name':        item.name,
        'description': item.description,
        'price':       str(item.price),
        'category':    item.category.name,
        'is_veg':      item.is_veg,
        'image':       item.image.url if item.image else None,
        'ar_glb':      item.ar_model_file.url if item.ar_model_file else None,
        'ar_usdz':     item.ar_model_usdz.url if item.ar_model_usdz else None,
        'ar_has_model': item.ar_has_model,
    })