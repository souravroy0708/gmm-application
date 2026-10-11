from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.accounts.models import pincode_validator
from apps.core.constants import PaymentMethod, PaymentStatus
from apps.core.models import TimeStampedModel


class OrderStatus(models.TextChoices):
    PLACED = "PLACED", _("Placed")
    CONFIRMED = "CONFIRMED", _("Confirmed")
    PACKED = "PACKED", _("Packed")
    DISPATCHED = "DISPATCHED", _("Dispatched")
    DELIVERED = "DELIVERED", _("Delivered")
    CANCELLED = "CANCELLED", _("Cancelled")


ALLOWED_TRANSITIONS = {
    OrderStatus.PLACED: {OrderStatus.CONFIRMED, OrderStatus.CANCELLED},
    OrderStatus.CONFIRMED: {OrderStatus.PACKED, OrderStatus.CANCELLED},
    OrderStatus.PACKED: {OrderStatus.DISPATCHED, OrderStatus.CANCELLED},
    OrderStatus.DISPATCHED: {OrderStatus.DELIVERED},
    OrderStatus.DELIVERED: set(),
    OrderStatus.CANCELLED: set(),
}


class ServiceablePin(TimeStampedModel):
    pincode = models.CharField("PIN code", max_length=6, unique=True, validators=[pincode_validator])
    area_name = models.CharField(max_length=120, blank=True)
    delivery_fee = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0.00"))
    cod_allowed = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "serviceable PIN code"
        ordering = ["pincode"]

    def __str__(self):
        return f"{self.pincode} {self.area_name}".strip()


class Order(TimeStampedModel):
    order_no = models.CharField(max_length=30, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="orders")
    status = models.CharField(max_length=12, choices=OrderStatus.choices, default=OrderStatus.PLACED, db_index=True)
    payment_method = models.CharField(max_length=5, choices=PaymentMethod.choices)
    payment_status = models.CharField(max_length=16, choices=PaymentStatus.choices, db_index=True)
    address_snapshot = models.JSONField()
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    tax_total = models.DecimalField(_("GST included"), max_digits=12, decimal_places=2, default=Decimal("0.00"))
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    total = models.DecimalField(max_digits=12, decimal_places=2)
    customer_note = models.TextField(blank=True)
    cancel_reason = models.CharField(max_length=255, blank=True)
    idempotency_key = models.CharField(max_length=64, null=True, blank=True)
    placed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="orders_taken",
        help_text=_("Set when staff placed the order on the customer's behalf."),
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["-created_at"])]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "idempotency_key"],
                condition=models.Q(idempotency_key__isnull=False),
                name="unique_idempotency_key_per_user",
            ),
            models.CheckConstraint(condition=models.Q(total__gte=0), name="order_total_non_negative"),
        ]

    def __str__(self):
        return self.order_no

    @property
    def pincode(self):
        return (self.address_snapshot or {}).get("pincode", "")

    @property
    def customer_can_cancel(self):
        return self.status == OrderStatus.PLACED


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey("catalog.ProductVariant", on_delete=models.PROTECT, related_name="order_items")
    # Snapshot of what was sold, so catalogue edits never rewrite history.
    product_name = models.CharField(max_length=150)
    variant_label = models.CharField(max_length=50)
    sku = models.CharField(max_length=40)
    hsn_code = models.CharField(max_length=8, blank=True)
    gst_rate = models.DecimalField(max_digits=4, decimal_places=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price per pack incl. GST")
    quantity = models.PositiveIntegerField()
    taxable_value = models.DecimalField(max_digits=12, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2)
    line_total = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        constraints = [models.CheckConstraint(condition=models.Q(quantity__gt=0), name="order_item_qty_positive")]

    def __str__(self):
        return f"{self.quantity} x {self.product_name} ({self.variant_label})"


class OrderStatusLog(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="status_logs")
    from_status = models.CharField(max_length=12, blank=True)
    to_status = models.CharField(max_length=12)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]

    def __str__(self):
        return f"{self.order.order_no}: {self.from_status or '-'} -> {self.to_status}"
