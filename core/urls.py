from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from restaurants.models import Restaurant

def home(request):
    # redirect to first active restaurant, or admin if none
    restaurant = Restaurant.objects.filter(is_active=True).first()
    if restaurant:
        return redirect('restaurants:menu', restaurant_slug=restaurant.slug)
    return redirect('/admin/')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home),
    path('', include('restaurants.urls')),
    path('ordering/', include('ordering.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)