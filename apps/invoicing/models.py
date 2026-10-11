from decimal import Decimal

from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel


class Invoice(TimeStampedModel):
    """Tax invoice for an order. Numbers are sequential per financial year and never reused."""

    order = models.OneToOneField("orders.Order", on_delete=models.PROTECT, related_name="invoice")
    invoice_no = models.CharField(max_length=16, unique=True)
    financial_year = models.CharField(max_length=7, db_index=True)
    issued_at = models.DateTimeField(default=timezone.now)
    seller_snapshot = models.JSONField(default=dict)
    is_interstate = models.BooleanField(default=False)
    cgst = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    sgst = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    igst = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    pdf_file = models.FileField(upload_to="invoices/%Y/", blank=True)  # PDF rendering arrives in Phase 3

    class Meta:
        ordering = ["-issued_at"]

    def __str__(self):
        return self.invoice_no
