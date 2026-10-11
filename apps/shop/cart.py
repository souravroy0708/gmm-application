"""Very simple session cart: {variant_id: quantity}."""
from decimal import Decimal

from apps.catalog.models import ProductVariant

SESSION_KEY = "cart"


class Cart:
    def __init__(self, request):
        self.session = request.session
        self.data = self.session.get(SESSION_KEY, {})

    def _save(self):
        self.session[SESSION_KEY] = self.data
        self.session.modified = True

    def set(self, variant_id, qty):
        if qty <= 0:
            self.data.pop(str(variant_id), None)
        else:
            self.data[str(variant_id)] = qty
        self._save()

    def add(self, variant_id, qty):
        self.set(variant_id, self.data.get(str(variant_id), 0) + qty)

    def remove(self, variant_id):
        self.set(variant_id, 0)

    def clear(self):
        self.data = {}
        self._save()

    def items(self):
        """[(variant_id, qty)] - the shape place_order() expects."""
        return [(int(k), v) for k, v in self.data.items()]

    @property
    def count(self):
        return sum(self.data.values())

    def lines(self):
        variants = ProductVariant.objects.select_related("product").prefetch_related("product__images").filter(pk__in=self.data.keys())
        out = []
        for v in variants:
            qty = self.data[str(v.pk)]
            out.append({"variant": v, "qty": qty, "total": v.price * qty})
        return out

    def subtotal(self, lines=None):
        return sum((l["total"] for l in (lines if lines is not None else self.lines())), Decimal("0.00"))


def cart_context(request):
    """Cart count/total and business settings (phone, WhatsApp) for every page."""
    from apps.core.models import SiteSetting

    cart = Cart(request)
    return {
        "cart_count": cart.count,
        "cart_total": cart.subtotal() if cart.count else 0,
        "site": SiteSetting.load(),
    }
