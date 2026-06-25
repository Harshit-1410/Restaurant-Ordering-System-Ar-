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

    # Media files (food images, AR models) are committed to git and always
    # present on Railway — serve them directly in production too.
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)