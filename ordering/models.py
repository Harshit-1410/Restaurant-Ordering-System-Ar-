"""
ordering/models.py
------------------
Secure multi-table ordering data model.

Architecture
~~~~~~~~~~~~
Table
  │  Each physical table has a unique random QR token.
  │  The QR code points to /{slug}/?t={qr_token} — never /{slug}/?table=N.
  │
TableSession   (1 per Table per dining period)
  │  Starts when the first customer scans the QR.
  │  Ends when staff clicks "Close Table" on the billing dashboard.
  │
CustomerSession  (1 per browser / device per TableSession)
  │  Created when a browser scans the QR.
  │  Tracks which device placed which order.
  │  Linked via a browser_uuid stored in the Django server-side session cookie.
  │
Cart  (1:1 with CustomerSession)
  └─ CartItem
  
Order  (M:1 with CustomerSession)
  └─ OrderItem
"""

import secrets

from django.db import models
from django.utils import timezone


# ── Token generation ──────────────────────────────────────────────────────────

def _generate_qr_token():
    """Cryptographically secure URL-safe random token for QR codes."""
    return secrets.token_urlsafe(24)


# ── Table ─────────────────────────────────────────────────────────────────────

class Table(models.Model):
    """
    A physical table in the restaurant.
    Never expose `id` or `table_number` in URLs — only `qr_token`.
    """
    restaurant   = models.ForeignKey(
        'restaurants.Restaurant', on_delete=models.CASCADE, related_name='tables'
    )
    table_number = models.CharField(max_length=20)
    qr_token     = models.CharField(max_length=64, unique=True, default=_generate_qr_token)
    is_active    = models.BooleanField(default=True)

    class Meta:
        unique_together = [('restaurant', 'table_number')]
        ordering        = ['table_number']

    def __str__(self):
        return f"Table {self.table_number} — {self.restaurant.name}"

    def qr_menu_url(self, request=None):
        """Absolute or relative URL that the QR code should encode."""
        path = f"/{self.restaurant.slug}/?t={self.qr_token}"
        if request:
            return request.build_absolute_uri(path)
        return path

    def rotate_token(self):
        """Issue a new QR token (invalidates all previously printed QR codes)."""
        self.qr_token = _generate_qr_token()
        self.save(update_fields=['qr_token'])


# ── TableSession ──────────────────────────────────────────────────────────────

class TableSession(models.Model):
    """
    One session per table per dining period.
    Multiple CustomerSessions can belong to one TableSession — one per device.
    """
    STATUS_OPEN   = 'open'
    STATUS_PAID   = 'paid'
    STATUS_CLOSED = 'closed'
    STATUS_CHOICES = [
        (STATUS_OPEN,   'Open'),
        (STATUS_PAID,   'Paid'),
        (STATUS_CLOSED, 'Closed'),
    ]

    table             = models.ForeignKey(Table, on_delete=models.CASCADE, related_name='sessions')
    status            = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN)
    started_at        = models.DateTimeField(auto_now_add=True)
    ended_at          = models.DateTimeField(null=True, blank=True)
    bill_requested_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"Session #{self.id} — {self.table} — {self.get_status_display()}"

    # ── Convenience properties ────────────────────────────────────────────
    @property
    def restaurant(self):
        return self.table.restaurant

    @property
    def table_number(self):
        return self.table.table_number

    @property
    def is_active(self):
        return self.status == self.STATUS_OPEN

    @property
    def is_paid(self):
        return self.status == self.STATUS_PAID

    @property
    def orders(self):
        """All Orders placed at this table session (across all customer sessions)."""
        return Order.objects.filter(customer_session__table_session=self)

    @property
    def session_total(self):
        """Sum of all non-cancelled order totals for this session."""
        result = self.orders.exclude(status='cancelled').aggregate(
            total=models.Sum('total_amount')
        )
        return result['total'] or 0

    def close(self, paid=True):
        self.status   = self.STATUS_PAID if paid else self.STATUS_CLOSED
        self.ended_at = timezone.now()
        self.save(update_fields=['status', 'ended_at'])


# ── CustomerSession ───────────────────────────────────────────────────────────

class CustomerSession(models.Model):
    """
    One session per browser/device within a TableSession.
    Identified by a browser_uuid generated server-side and stored in the
    Django session cookie — never trusted from a URL parameter.
    """
    table_session  = models.ForeignKey(
        TableSession, on_delete=models.CASCADE, related_name='customer_sessions'
    )
    browser_uuid   = models.CharField(max_length=64)
    customer_name  = models.CharField(max_length=100, blank=True,
        help_text='Optional display name entered by the customer in the cart.')
    created_at     = models.DateTimeField(auto_now_add=True)
    last_seen      = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('table_session', 'browser_uuid')]
        ordering        = ['created_at']

    def __str__(self):
        display = self.customer_name or f"Guest {self.id}"
        return f"{display} @ Table {self.table_session.table_number}"


# ── Cart ──────────────────────────────────────────────────────────────────────

class Cart(models.Model):
    """One cart per CustomerSession. Cleared after each order is placed."""
    customer_session = models.OneToOneField(
        CustomerSession, on_delete=models.CASCADE, related_name='cart'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart — {self.customer_session}"


class CartItem(models.Model):
    cart      = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    menu_item = models.ForeignKey('restaurants.MenuItem', on_delete=models.CASCADE)
    quantity  = models.PositiveIntegerField(default=1)
    notes     = models.TextField(blank=True)

    @property
    def subtotal(self):
        return self.menu_item.price * self.quantity

    def __str__(self):
        return f"{self.quantity}× {self.menu_item.name}"


# ── Order ─────────────────────────────────────────────────────────────────────

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending',   'Pending'),
        ('preparing', 'Preparing'),
        ('ready',     'Ready'),
        ('served',    'Served'),
        ('cancelled', 'Cancelled'),
    ]

    customer_session = models.ForeignKey(
        CustomerSession, on_delete=models.CASCADE, related_name='orders'
    )
    status       = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_amount = models.DecimalField(max_digits=8, decimal_places=2)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.id} — {self.customer_session}"

    # ── Convenience properties ────────────────────────────────────────────
    @property
    def table_session(self):
        return self.customer_session.table_session

    @property
    def restaurant(self):
        return self.customer_session.table_session.table.restaurant


# ── OrderItem ─────────────────────────────────────────────────────────────────

class OrderItem(models.Model):
    order      = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    menu_item  = models.ForeignKey('restaurants.MenuItem', on_delete=models.CASCADE)
    quantity   = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)
    notes      = models.TextField(blank=True)

    @property
    def subtotal(self):
        return self.unit_price * self.quantity

    def __str__(self):
        return f"{self.quantity}× {self.menu_item.name}"
