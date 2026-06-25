import os

from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.views.static import serve
from restaurants.models import Restaurant

def home(request):
    restaurant = Restaurant.objects.filter(is_active=True).first()
    if restaurant:
        return redirect('restaurants:menu', restaurant_slug=restaurant.slug)
    return redirect('/admin/')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home),
    path('', include('restaurants.urls')),
    path('ordering/', include('ordering.urls')),

    # AR model files (.glb / .usdz) are stored on the local filesystem and
    # committed to git, so they must be served in production too.
    re_path(
        r'^media/ar_models/(?P<path>.*)$',
        serve,
        {'document_root': os.path.join(settings.MEDIA_ROOT, 'ar_models')},
    ),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)