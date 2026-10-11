from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.constants import PaymentMethod, PaymentStatus
from apps.core.models import TimeStampedModel


class Payment(TimeStampedModel):
    """One payment attempt for an order. A rejected proof can be followed by a new one."""

    order = models.ForeignKey("orders.Order", on_delete=models.PROTECT, related_name="payments")
    method = models.CharField(max_length=5, choices=PaymentMethod.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=16, choices=PaymentStatus.choices, default=PaymentStatus.AWAITING_PROOF, db_index=True)
    reference = models.CharField(
        _("UTR / reference"), max_length=30, blank=True,
        help_text=_("12-digit UPI reference (UTR) or bank transfer reference."),
    )
    proof_image = models.ImageField(upload_to="payment_proofs/%Y/%m/", blank=True)
    reject_reason = models.CharField(max_length=255, blank=True)
    note = models.CharField(max_length=255, blank=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="payments_handled"
    )
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            # The same UTR cannot back two live payments (stops proof reuse).
            models.UniqueConstraint(
                fields=["reference"],
                condition=models.Q(status__in=["PROOF_SUBMITTED", "VERIFIED"]) & ~models.Q(reference=""),
                name="unique_live_payment_reference",
            ),
        ]

    def __str__(self):
        return f"{self.order.order_no} - {self.get_method_display()} - {self.get_status_display()}"
