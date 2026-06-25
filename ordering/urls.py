from django.urls import path
from . import views

app_name = 'ordering'

urlpatterns = [
    path('cart/add/', views.cart_add, name='cart_add'),
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/remove/<int:item_id>/', views.cart_remove, name='cart_remove'),
    path('place/', views.place_order, name='place_order'),
    path('kitchen/<int:restaurant_id>/', views.kitchen_dashboard, name='kitchen'),
    path('status/update/', views.update_order_status, name='update_status'),
    path('confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
    path('cart/data/', views.cart_data, name='cart_data'),
    path('bill/request/', views.request_bill, name='request_bill'),
    path('billing/<int:restaurant_id>/', views.billing_dashboard, name='billing'),
    path('billing/detail/<int:session_id>/', views.bill_detail_data, name='bill_detail'),
    path('billing/close/<int:session_id>/', views.close_table_session, name='close_table'),
    path('billing/session/<int:session_id>/', views.table_session_bill, name='session_bill'),
    path('session/orders/', views.session_orders, name='session_orders'),
]