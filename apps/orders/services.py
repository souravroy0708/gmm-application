"""Order business rules. Views, admin and (later) the API all go through here."""
from decimal import ROUND_HALF_UP, Decimal

from django.db import transaction
from django.db.models import F
from django.utils import timezone

from apps.catalog.models import ProductVariant
from apps.core.constants import PaymentMethod, PaymentStatus
from apps.core.models import Sequence, SiteSetting

from .models import ALLOWED_TRANSITIONS, Order, OrderItem, OrderStatus, OrderStatusLog, ServiceablePin

CENT = Decimal("0.01")


class OrderError(Exception):
    """A rule was broken; the message is safe to show to the user."""


def money(value):
    return Decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


def split_inclusive_tax(line_total, gst_rate):
    """Prices include GST. Return (taxable_value, tax_amount) for a line total."""
    if not gst_rate:
        return money(line_total), Decimal("0.00")
    taxable = money(Decimal(line_total) * 100 / (100 + Decimal(gst_rate)))
    return taxable, money(Decimal(line_total) - taxable)


def generate_order_no(now=None):
    day = timezone.localtime(now or timezone.now()).strftime("%y%m%d")
    return f"GMM-{day}-{Sequence.next(f'order:{day}'):04d}"


@transaction.atomic
def place_order(*, user, address, items, payment_method, idempotency_key=None, note="", placed_by=None):
    """Create an order from [(variant_id, quantity), ...].

    Safe against double submits (idempotency_key) and overselling (row locks on stock).
    """
    from apps.payments.models import Payment  # local import avoids an import cycle

    if idempotency_key:
        existing = Order.objects.filter(user=user, idempotency_key=idempotency_key).first()
        if existing:
            return existing

    if address.user_id != user.pk:
        raise OrderError("Please choose one of your own saved addresses.")
    if payment_method not in PaymentMethod.values:
        raise OrderError("Please choose a payment method.")

    wanted = {}
    for variant_id, qty in items:
        if int(qty) <= 0:
            raise OrderError("Quantity must be at least 1.")
        wanted[variant_id] = wanted.get(variant_id, 0) + int(qty)
    if not wanted:
        raise OrderError("Your cart is empty.")

    variants = {
        v.pk: v
        for v in ProductVariant.objects.select_for_update(of=("self",))
        .select_related("product")
        .filter(pk__in=wanted)
    }
    if len(variants) != len(wanted):
        raise OrderError("Some items are no longer available.")
    for variant_id, qty in wanted.items():
        v = variants[variant_id]
        if not (v.is_active and v.product.is_active):
            raise OrderError(f"{v.product.name} ({v.label}) is not available right now.")
        if v.stock < qty:
            raise OrderError(f"Only {v.stock} left of {v.product.name} ({v.label}).")

    pin = ServiceablePin.objects.filter(pincode=address.pincode, is_active=True).first()
    if pin is None:
        raise OrderError("Sorry, we do not deliver to this PIN code yet.")
    cfg = SiteSetting.load()

    lines, subtotal, tax_total = [], Decimal("0.00"), Decimal("0.00")
    for variant_id, qty in wanted.items():
        v = variants[variant_id]
        line_total = money(v.price * qty)
        taxable, tax = split_inclusive_tax(line_total, v.gst_rate)
        subtotal += line_total
        tax_total += tax
        lines.append((v, qty, line_total, taxable, tax))

    if subtotal < cfg.min_order_value:
        raise OrderError(f"The minimum order value is Rs. {cfg.min_order_value}.")

    delivery_fee = pin.delivery_fee
    if cfg.free_delivery_above is not None and subtotal >= cfg.free_delivery_above:
        delivery_fee = Decimal("0.00")
    total = subtotal + delivery_fee

    if payment_method == PaymentMethod.COD:
        if not cfg.cod_enabled or not pin.cod_allowed:
            raise OrderError("Cash on delivery is not available for this address.")
        if total < cfg.cod_min_order:
            raise OrderError(f"Cash on delivery needs an order of at least Rs. {cfg.cod_min_order}.")
        if cfg.cod_max_order is not None and total > cfg.cod_max_order:
            raise OrderError(f"Cash on delivery is limited to orders up to Rs. {cfg.cod_max_order}.")

    is_cod = payment_method == PaymentMethod.COD
    order = Order.objects.create(
        order_no=generate_order_no(),
        user=user,
        status=OrderStatus.PLACED,
        payment_method=payment_method,
        payment_status=PaymentStatus.COD_DUE if is_cod else PaymentStatus.AWAITING_PROOF,
        address_snapshot=address.snapshot(),
        subtotal=subtotal,
        tax_total=tax_total,
        delivery_fee=delivery_fee,
        total=total,
        customer_note=note,
        idempotency_key=idempotency_key or None,
        placed_by=placed_by,
    )
    OrderItem.objects.bulk_create(
        OrderItem(
            order=order, variant=v, product_name=v.product.name, variant_label=v.label, sku=v.sku,
            hsn_code=v.hsn_code, gst_rate=v.gst_rate, unit_price=v.price, quantity=qty,
            taxable_value=taxable, tax_amount=tax, line_total=line_total,
        )
        for v, qty, line_total, taxable, tax in lines
    )
    for v, qty, *_rest in lines:
        ProductVariant.objects.filter(pk=v.pk).update(stock=F("stock") - qty)
    if is_cod:
        Payment.objects.create(order=order, method=PaymentMethod.COD, amount=total, status=PaymentStatus.COD_DUE)
    OrderStatusLog.objects.create(
        order=order, from_status="", to_status=OrderStatus.PLACED, actor=placed_by or user,
        note="Order placed on customer's behalf" if placed_by else "Order placed",
    )
    return order


@transaction.atomic
def change_status(order, new_status, actor=None, note=""):
    order = Order.objects.select_for_update().get(pk=order.pk)
    old = order.status
    if new_status == old:
        return order
    if new_status not in ALLOWED_TRANSITIONS[OrderStatus(old)]:
        raise OrderError(f"{order.order_no}: cannot move from {old.title()} to {OrderStatus(new_status).label}.")
    if (
        new_status == OrderStatus.DISPATCHED
        and order.payment_method != PaymentMethod.COD
        and order.payment_status != PaymentStatus.VERIFIED
    ):
        raise OrderError(f"{order.order_no}: payment must be verified before dispatch.")

    if new_status == OrderStatus.CANCELLED:
        for item in order.items.all():
            ProductVariant.objects.filter(pk=item.variant_id).update(stock=F("stock") + item.quantity)
        order.cancel_reason = note[:255]
        if order.payment_status == PaymentStatus.VERIFIED:
            note = f"{note} (payment was verified - arrange a refund)".strip()

    order.status = new_status
    order.save(update_fields=["status", "cancel_reason", "updated_at"])
    OrderStatusLog.objects.create(order=order, from_status=old, to_status=new_status, actor=actor, note=note[:255])
    return order


def cancel_order(order, actor=None, reason="Cancelled"):
    return change_status(order, OrderStatus.CANCELLED, actor=actor, note=reason)
