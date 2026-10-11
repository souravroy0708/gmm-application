from django.db import models
from django.utils.translation import gettext_lazy as _


class PaymentMethod(models.TextChoices):
    COD = "COD", _("Cash on delivery")
    UPI = "UPI", _("UPI transfer")
    BANK = "BANK", _("Bank transfer")


class PaymentStatus(models.TextChoices):
    COD_DUE = "COD_DUE", _("COD due")
    COLLECTED = "COLLECTED", _("COD collected")
    AWAITING_PROOF = "AWAITING_PROOF", _("Awaiting payment proof")
    PROOF_SUBMITTED = "PROOF_SUBMITTED", _("Proof submitted")
    VERIFIED = "VERIFIED", _("Payment verified")
    REJECTED = "REJECTED", _("Proof rejected")
