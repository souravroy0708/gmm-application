from decimal import Decimal

from django.db import models, transaction
from django.utils.translation import gettext_lazy as _


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Sequence(models.Model):
    """Gap-free counters (order numbers, invoice numbers) safe under concurrency."""

    key = models.CharField(max_length=64, unique=True)
    value = models.PositiveBigIntegerField(default=0)

    def __str__(self):
        return f"{self.key} = {self.value}"

    @classmethod
    def next(cls, key):
        # Call inside the same transaction that uses the number, so a rollback
        # also rolls the counter back and no numbers are skipped.
        with transaction.atomic():
            obj, _created = cls.objects.select_for_update().get_or_create(key=key)
            obj.value += 1
            obj.save(update_fields=["value"])
            return obj.value


class SiteSetting(models.Model):
    """Single row of business-wide settings, editable by the owner in the admin."""

    business_name = models.CharField(max_length=200, default="GMM Distributors Private Limited")
    legal_address = models.TextField(blank=True)
    gstin = models.CharField("GSTIN", max_length=15, blank=True)
    cin = models.CharField("CIN", max_length=21, blank=True)
    state_name = models.CharField(max_length=60, default="West Bengal")
    state_code = models.CharField(
        max_length=2, default="19", help_text=_("GST state code of the dispatch location (West Bengal = 19).")
    )
    support_phone = models.CharField(max_length=20, blank=True)
    whatsapp_number = models.CharField(max_length=20, blank=True)
    support_email = models.EmailField(blank=True)

    upi_id = models.CharField("UPI ID", max_length=100, blank=True)
    upi_qr = models.ImageField("UPI QR code", upload_to="settings/", blank=True)
    bank_account_name = models.CharField(max_length=150, blank=True)
    bank_name = models.CharField(max_length=100, blank=True)
    bank_account_number = models.CharField(max_length=30, blank=True)
    bank_ifsc = models.CharField("IFSC", max_length=11, blank=True)

    min_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    free_delivery_above = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text=_("Delivery is free when the order subtotal reaches this value. Leave blank to disable."),
    )
    cod_enabled = models.BooleanField(default=True)
    cod_min_order = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    cod_max_order = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text=_("Highest order value allowed for COD. Leave blank for no limit."),
    )

    class Meta:
        verbose_name = _("business settings")
        verbose_name_plural = _("business settings")

    def __str__(self):
        return self.business_name

    def save(self, *args, **kwargs):
        self.pk = 1  # singleton
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass  # never delete the settings row

    @classmethod
    def load(cls):
        obj, _created = cls.objects.get_or_create(pk=1)
        return obj
