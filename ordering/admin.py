from django.contrib import admin
from .models import Order, OrderItem, TableSession

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['unit_price', 'subtotal']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'restaurant', 'table_session', 'status', 'total_amount', 'created_at']
    list_filter = ['restaurant', 'status']
    inlines = [OrderItemInline]

@admin.register(TableSession)
class TableSessionAdmin(admin.ModelAdmin):
    list_display  = ['restaurant', 'table_number', 'is_active', 'is_paid', 'session_total_display', 'created_at', 'closed_at']
    list_filter   = ['restaurant', 'is_active', 'is_paid']
    readonly_fields = ['created_at', 'session_token', 'session_total_display']

    fieldsets = [
        (None, {
            'fields': ['restaurant', 'table_number', 'session_token', 'is_active', 'created_at'],
        }),
        ('Billing', {
            'fields': ['bill_requested_at', 'is_paid', 'closed_at', 'session_total_display'],
            'description': 'Billing lifecycle for this table visit.',
        }),
    ]

    @admin.display(description='Session Total (₹)')
    def session_total_display(self, obj):
        return f'₹{obj.session_total}'