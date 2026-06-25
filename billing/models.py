"""
billing/models.py
-----------------
Data models for the authenticated Billing Dashboard module.

StaffProfile   — extends User with a restaurant role (owner / manager / cashier)
Bill           — one Bill per TableSession; immutable after payment
Payment        — one or more payments per Bill (split-payment support)
"""

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

from restaurants.models import Restaurant
from ordering.models import TableSession


# ── Staff / roles ─────────────────────────────────────────────────────────────

class StaffProfile(models.Model):
    ROLE_OWNER   = 'owner'
    ROLE_MANAGER = 'manager'
    ROLE_CASHIER = 'cashier'
    ROLES = [
        (ROLE_OWNER,   'Owner'),
        (ROLE_MANAGER, 'Manager'),
        (ROLE_CASHIER, 'Cashier'),
    ]

    user       = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staff_profile')
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='staff')
    role       = models.CharField(max_length=20, choices=ROLES, default=ROLE_CASHIER)
    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        name = self.user.get_full_name() or self.user.username
        return f"{name} — {self.get_role_display()} @ {self.restaurant.name}"

    @property
    def can_manage(self):
        return self.role in (self.ROLE_OWNER, self.ROLE_MANAGER)

    @property
    def is_owner(self):
        return self.role == self.ROLE_OWNER


# ── Bill ──────────────────────────────────────────────────────────────────────

class Bill(models.Model):
    STATUS_DRAFT = 'draft'
    STATUS_PAID  = 'paid'
    STATUS_VOID  = 'void'
    STATUSES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_PAID,  'Paid'),
        (STATUS_VOID,  'Void'),
    ]

    DISCOUNT_PERCENT = 'percent'
    DISCOUNT_FLAT    = 'flat'
    DISCOUNT_TYPES   = [
        (DISCOUNT_PERCENT, 'Percentage (%)'),
        (DISCOUNT_FLAT,    'Flat Amount (₹)'),
    ]

    bill_number   = models.CharField(max_length=30, unique=True, editable=False)
    table_session = models.OneToOneField(
        TableSession, on_delete=models.PROTECT, related_name='bill'
    )
    restaurant = models.ForeignKey(
        Restaurant, on_delete=models.PROTECT, related_name='bills'
    )
    cashier = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name='bills_processed'
    )

    # ── Computed amounts ──────────────────────────────────────────────────
    subtotal       = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_percentage = models.DecimalField(max_digits=5,  decimal_places=2, default=5)
    tax_amount     = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    service_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    discount_type   = models.CharField(max_length=10, choices=DISCOUNT_TYPES, blank=True, default='')
    discount_value  = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_reason = models.TextField(blank=True)
    discount_by     = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='discounts_applied'
    )
    discount_at     = models.DateTimeField(null=True, blank=True)

    round_off   = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # ── Meta ─────────────────────────────────────────────────────────────
    status         = models.CharField(max_length=10, choices=STATUSES, default=STATUS_DRAFT)
    customer_count = models.PositiveIntegerField(default=0)
    notes          = models.TextField(blank=True)
    created_at     = models.DateTimeField(auto_now_add=True)
    paid_at        = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.bill_number} — ₹{self.grand_total} [{self.get_status_display()}]"

    def save(self, *args, **kwargs):
        if not self.bill_number:
            self.bill_number = self._generate_bill_number()
        super().save(*args, **kwargs)

    def _generate_bill_number(self) -> str:
        today  = timezone.localdate()
        prefix = f"BILL-{today.strftime('%Y%m%d')}-"
        count  = Bill.objects.filter(bill_number__startswith=prefix).count()
        return f"{prefix}{str(count + 1).zfill(4)}"

    # ── Computed properties ───────────────────────────────────────────────
    @property
    def is_paid(self) -> bool:
        return self.status == self.STATUS_PAID

    @property
    def amount_paid(self):
        return sum(p.amount for p in self.payments.all())

    @property
    def amount_due(self):
        return max(self.grand_total - self.amount_paid, 0)

    @property
    def dining_duration(self) -> str:
        end   = self.paid_at or timezone.now()
        secs  = int((end - self.table_session.started_at).total_seconds())
        h, r  = divmod(secs, 3600)
        m     = r // 60
        return f"{h}h {m}m" if h else f"{m}m"


# ── Payment ───────────────────────────────────────────────────────────────────

class Payment(models.Model):
    METHOD_CASH        = 'cash'
    METHOD_UPI         = 'upi'
    METHOD_CREDIT_CARD = 'credit_card'
    METHOD_DEBIT_CARD  = 'debit_card'
    METHODS = [
        (METHOD_CASH,        'Cash'),
        (METHOD_UPI,         'UPI'),
        (METHOD_CREDIT_CARD, 'Credit Card'),
        (METHOD_DEBIT_CARD,  'Debit Card'),
    ]

    bill            = models.ForeignKey(Bill, related_name='payments', on_delete=models.PROTECT)
    payment_method  = models.CharField(max_length=20, choices=METHODS)
    amount          = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_ref = models.CharField(max_length=100, blank=True)
    received_by     = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name='payments_received'
    )
    paid_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"₹{self.amount} {self.get_payment_method_display()} — {self.bill.bill_number}"
