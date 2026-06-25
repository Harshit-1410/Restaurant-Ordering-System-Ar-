"""
ordering/admin.py
-----------------
Django admin for the new secure multi-table ordering models.

Key feature: TableAdmin exposes the QR URL for each table so the owner can
copy it into a QR-code generator without ever knowing (or sharing) table IDs.
"""

from django.contrib import admin
from django.utils.html import format_html

from .models import (
    Cart, CartItem, CustomerSession, Order, OrderItem, Table, TableSession,
)


# ── Inlines ───────────────────────────────────────────────────────────────────

class OrderItemInline(admin.TabularInline):
    model          = OrderItem
    extra          = 0
    readonly_fields = ['unit_price', 'subtotal']


class CustomerSessionInline(admin.TabularInline):
    model          = CustomerSession
    extra          = 0
    readonly_fields = ['browser_uuid', 'created_at', 'last_seen']
    can_delete     = False


# ── Table ─────────────────────────────────────────────────────────────────────

@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display    = ['table_number', 'restaurant', 'is_active', 'qr_token_short', 'qr_url_link']
    list_filter     = ['restaurant', 'is_active']
    readonly_fields = ['qr_token', 'qr_url_link']
    search_fields   = ['table_number', 'restaurant__name']

    fieldsets = [
        (None, {
            'fields': ['restaurant', 'table_number', 'is_active'],
        }),
        ('QR Code', {
            'fields': ['qr_token', 'qr_url_link'],
            'description': (
                'Copy the full URL below and paste it into any QR-code generator '
                '(e.g. qr-code-generator.com). '
                'Use "Rotate Token" to invalidate old printed codes.'
            ),
        }),
    ]

    actions = ['rotate_qr_token']

    # ── Store request so display methods can build absolute URLs ──────────
    def changelist_view(self, request, *args, **kwargs):
        self._request = request
        return super().changelist_view(request, *args, **kwargs)

    def changeform_view(self, request, *args, **kwargs):
        self._request = request
        return super().changeform_view(request, *args, **kwargs)

    # ── Display helpers ───────────────────────────────────────────────────
    @admin.display(description='QR Token (preview)')
    def qr_token_short(self, obj):
        return obj.qr_token[:16] + '…'

    @admin.display(description='QR URL (full — paste into QR generator)')
    def qr_url_link(self, obj):
        request = getattr(self, '_request', None)
        url     = obj.qr_menu_url(request)   # absolute when request is available
        return format_html(
            '<code style="word-break:break-all;user-select:all">{}</code>',
            url,
        )

    @admin.action(description='Rotate QR token (invalidates printed codes)')
    def rotate_qr_token(self, request, queryset):
        for table in queryset:
            table.rotate_token()
        count = queryset.count()
        self.message_user(
            request,
            f'{count} QR token(s) rotated. Re-print the affected QR codes.',
        )


# ── TableSession ──────────────────────────────────────────────────────────────

@admin.register(TableSession)
class TableSessionAdmin(admin.ModelAdmin):
    list_display  = [
        'id', 'table_number_display', 'restaurant_display', 'status',
        'started_at', 'ended_at', 'bill_requested_at', 'session_total_display',
        'customer_count',
    ]
    list_filter   = ['status', 'table__restaurant']
    readonly_fields = ['started_at', 'ended_at', 'session_total_display', 'customer_count']
    inlines        = [CustomerSessionInline]

    @admin.display(description='Table', ordering='table__table_number')
    def table_number_display(self, obj):
        return f"Table {obj.table_number}"

    @admin.display(description='Restaurant', ordering='table__restaurant__name')
    def restaurant_display(self, obj):
        return obj.restaurant.name

    @admin.display(description='Total (₹)')
    def session_total_display(self, obj):
        return f'₹{obj.session_total}'

    @admin.display(description='Guests')
    def customer_count(self, obj):
        return obj.customer_sessions.count()


# ── CustomerSession ───────────────────────────────────────────────────────────

@admin.register(CustomerSession)
class CustomerSessionAdmin(admin.ModelAdmin):
    list_display  = ['id', 'table_session', 'browser_uuid_short', 'created_at', 'last_seen', 'order_count']
    list_filter   = ['table_session__table__restaurant', 'table_session__status']
    readonly_fields = ['created_at', 'last_seen']

    @admin.display(description='Browser UUID')
    def browser_uuid_short(self, obj):
        return obj.browser_uuid[:12] + '…'

    @admin.display(description='Orders')
    def order_count(self, obj):
        return obj.orders.count()


# ── Order ─────────────────────────────────────────────────────────────────────

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display  = [
        'id', 'table_number_display', 'restaurant_display',
        'status', 'total_amount', 'created_at',
    ]
    list_filter   = ['status', 'customer_session__table_session__table__restaurant']
    readonly_fields = ['created_at', 'updated_at']
    inlines        = [OrderItemInline]

    @admin.display(description='Table')
    def table_number_display(self, obj):
        return f"Table {obj.table_session.table_number}"

    @admin.display(description='Restaurant')
    def restaurant_display(self, obj):
        return obj.restaurant.name
