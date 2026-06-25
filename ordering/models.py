from django.db import models
import uuid

class TableSession(models.Model):
    restaurant = models.ForeignKey('restaurants.Restaurant', on_delete=models.CASCADE)
    table_number = models.CharField(max_length=20)
    session_token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    # ── Billing fields ──────────────────────────────────────────────────────
    bill_requested_at = models.DateTimeField(null=True, blank=True)   # when customer taps "Request Bill"
    is_paid           = models.BooleanField(default=False)            # flipped by staff after payment
    closed_at         = models.DateTimeField(null=True, blank=True)   # when table is cleared / session ends

    @property
    def session_total(self):
        """Sum of all non-cancelled order totals for this session."""
        result = self.order_set.exclude(status='cancelled').aggregate(
            total=models.Sum('total_amount')
        )
        return result['total'] or 0

    def __str__(self):
        return f"{self.restaurant} — Table {self.table_number}"


class Cart(models.Model):
    session = models.OneToOneField(TableSession, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    menu_item = models.ForeignKey('restaurants.MenuItem', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    notes = models.TextField(blank=True)

    @property
    def subtotal(self):
        return self.menu_item.price * self.quantity


class Order(models.Model):
    STATUS = [
        ('pending',    'Pending'),
        ('preparing',  'Preparing'),
        ('ready',      'Ready'),
        ('served',     'Served'),
        ('cancelled',  'Cancelled'),
    ]
    restaurant = models.ForeignKey('restaurants.Restaurant', on_delete=models.CASCADE)
    table_session = models.ForeignKey(TableSession, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS, default='pending')
    total_amount = models.DecimalField(max_digits=8, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    menu_item = models.ForeignKey('restaurants.MenuItem', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)  # snapshot at order time
    notes = models.TextField(blank=True)

    @property
    def subtotal(self):
        return self.unit_price * self.quantity