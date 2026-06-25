from django.urls import path
from . import views

app_name = 'restaurants'

urlpatterns = [
    path('<slug:restaurant_slug>/', views.menu, name='menu'),
    path('item/<int:item_id>/detail/', views.menu_item_detail, name='item_detail'),
]