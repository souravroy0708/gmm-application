from django import template
from django.templatetags.static import static

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


@register.filter
def digits(value):
    """'+91 90837-32101' -> '919083732101' (for wa.me links)."""
    d = "".join(c for c in str(value or "") if c.isdigit())
    return d if len(d) > 10 else f"91{d}" if d else ""


@register.filter
def lname(product, lang):
    return product.localized_name(lang)


@register.filter
def ldesc(product, lang):
    text = product.short_description_bn if lang == "bn" and product.short_description_bn else product.short_description
    return text
