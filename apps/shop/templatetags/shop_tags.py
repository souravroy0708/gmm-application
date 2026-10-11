from django import template
from django.templatetags.static import static

from apps.core.fields import normalize_phone

register = template.Library()

# Website photos used until a photo is uploaded in the admin (Product images).
FALLBACK = {
    "premium-jackpot-soil-booster": "premium-jackpot-soil-booster",
    "micro-max-jackpot-soil-booster": "micro-max-jackpot-soil-booster",
    "nirmala-agri-vita-green-gold": "nirmala-agri-vita-green-gold-1",
    "jackpot-dhamaka": "jackpot-dhamaka-1",
}


@register.filter
def photo(product):
    """URL of the product photo: admin-uploaded image first, else the website photo, else ''."""
    first = next(iter(product.images.all()), None)
    if first:
        return first.image.url
    name = FALLBACK.get(product.slug)
    return static(f"images/products/{name}.webp") if name else ""


def _canon(value):
    """Any way of typing an Indian mobile ('9083732101', '+91 90837-32101', '919083732101',
    '09083732101') -> '+919083732101'. Unknown shapes are returned as typed."""
    return normalize_phone(value)


@register.filter
def wa_num(value):
    """For wa.me links: digits only, country code included exactly once -> '919083732101'."""
    return "".join(c for c in _canon(value) if c.isdigit())


@register.filter
def tel_num(value):
    """For tel: links -> '+919083732101'."""
    c = _canon(value)
    return "+" + "".join(x for x in c if x.isdigit()) if c else ""


@register.filter
def phone_pretty(value):
    """For display -> '+91 90837 32101'."""
    c = _canon(value)
    return f"{c[:3]} {c[3:8]} {c[8:]}" if len(c) == 13 and c.startswith("+91") else c


@register.filter
def digits(value):
    """Kept for backwards compatibility; same as wa_num."""
    return wa_num(value)


@register.filter
def lname(product, lang):
    return product.localized_name(lang)


@register.filter
def ldesc(product, lang):
    text = product.short_description_bn if lang == "bn" and product.short_description_bn else product.short_description
    return text
