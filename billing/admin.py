from django.contrib import admin

from .models import Bill, Payment, StaffProfile


class PaymentInline(admin.TabularInline):
    model           = Payment
    extra           = 0
    readonly_fields = ['payment_method', 'amount', 'transaction_ref', 'received_by', 'paid_at']
    can_delete      = False


@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display  = ['user', 'restaurant', 'role', 'is_active', 'created_at']
    list_filter   = ['restaurant', 'role', 'is_active']
    search_fields = ['user__username', 'user__first_name', 'restaurant__name']


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display  = [
        'bill_number', 'table_number', 'restaurant', 'status',
        'grand_total', 'amount_paid_display', 'cashier', 'created_at', 'paid_at',
    ]
    list_filter   = ['status', 'restaurant', 'created_at']
    readonly_fields = [
        'bill_number', 'created_at', 'paid_at',
        'subtotal', 'tax_amount', 'discount_amount', 'round_off', 'grand_total',
    ]
    search_fields = ['bill_number']
    inlines       = [PaymentInline]

    @admin.display(description='Table')
    def table_number(self, obj):
        return f"Table {obj.table_session.table_number}"

    @admin.display(description='Paid')
    def amount_paid_display(self, obj):
        return f"₹{obj.amount_paid}"

    def has_delete_permission(self, request, obj=None):
        return False  # Bills must never be deleted


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display  = ['bill', 'payment_method', 'amount', 'received_by', 'paid_at']
    list_filter   = ['payment_method', 'paid_at']
    readonly_fields = ['bill', 'payment_method', 'amount', 'received_by', 'paid_at']

    def has_delete_permission(self, request, obj=None):
        return False
