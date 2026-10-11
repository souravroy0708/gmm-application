import re

from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

phone_validator = RegexValidator(
    regex=r"^\+91[6-9]\d{9}$",
    message=_("Enter a valid 10-digit Indian mobile number."),
)


def normalize_phone(raw):
    """Return +91XXXXXXXXXX for any common way of typing an Indian mobile number."""
    value = str(raw or "").strip()
    digits = re.sub(r"\D", "", value)
    if len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]
    elif len(digits) == 11 and digits.startswith("0"):
        digits = digits[1:]
    if len(digits) == 10:
        return f"+91{digits}"
    return value


class PhoneField(models.CharField):
    """Stores Indian mobile numbers in one canonical form (+91XXXXXXXXXX)."""

    default_validators = [phone_validator]

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("max_length", 13)
        super().__init__(*args, **kwargs)

    def to_python(self, value):
        value = super().to_python(value)
        return normalize_phone(value) if value else value
