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


# ---- order safety limits ----
MAX_QTY_PER_ITEM = 10      # max quantity of any one product/variant in a cart or order
MAX_CART_LINES = 10        # max different products in one cart / order
ACTIVE_ORDER_STATUSES = ("PLACED", "CONFIRMED", "PACKED", "DISPATCHED")   # one at a time per customer


def say(en, bn):
    """Message in the visitor's language (English / Bengali)."""
    from django.utils.translation import get_language
    return bn if (get_language() or "").startswith("bn") else en
