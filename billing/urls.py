from django.urls import path
from . import views

app_name = 'billing'

urlpatterns = [
    # Auth
    path('login/',  views.login_view,  name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboard
    path('',        views.dashboard,  name='dashboard'),

    # Open bills (active sessions)
    path('open/',   views.open_bills, name='open_bills'),

    # Bill detail & actions
    path('bills/<int:session_id>/',                         views.bill_detail,          name='bill_detail'),
    path('bills/<int:bill_id>/recalc/',                     views.recalc_bill,          name='recalc_bill'),
    path('bills/<int:bill_id>/discount/',                   views.apply_discount_view,  name='apply_discount'),
    path('bills/<int:bill_id>/discount/remove/',            views.remove_discount_view, name='remove_discount'),
    path('bills/<int:bill_id>/payment/',                    views.add_payment_view,     name='add_payment'),
    path('bills/<int:bill_id>/payment/<int:payment_id>/delete/', views.delete_payment_view, name='delete_payment'),
    path('bills/<int:bill_id>/close/',                      views.close_bill_view,      name='close_bill'),
    path('bills/<int:bill_id>/receipt/',                    views.receipt_view,         name='receipt'),

    # History & reports
    path('history/', views.history_view, name='history'),
    path('reports/', views.reports_view, name='reports'),
]
