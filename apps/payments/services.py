import re

from django.db import transaction
from django.utils import timezone

from apps.core.constants import PaymentMethod, PaymentStatus
from apps.orders.models import Order, OrderStatus

from .models import Payment


class PaymentError(Exception):
    """A payment rule was broken; the message is safe to show to the user."""


UPI_UTR = re.compile(r"^\d{12}$")
BANK_REF = re.compile(r"^[A-Z0-9]{6,30}$")

# What staff may do to a payment record
ALLOWED = {
    PaymentStatus.PROOF_SUBMITTED: {PaymentStatus.VERIFIED, PaymentStatus.REJECTED},
    PaymentStatus.COD_DUE: {PaymentStatus.COLLECTED},
}


@transaction.atomic
def submit_proof(order, reference, proof_image=None):
    """Customer submits a UTR (and optional screenshot) for a UPI/bank order."""
    order = Order.objects.select_for_update().get(pk=order.pk)
    if order.payment_method == PaymentMethod.COD:
        raise PaymentError("This is a cash on delivery order; no payment proof is needed.")
    if order.status == OrderStatus.CANCELLED:
        raise PaymentError("This order has been cancelled.")
    if order.payment_status in (PaymentStatus.VERIFIED, PaymentStatus.PROOF_SUBMITTED):
        raise PaymentError("Payment proof has already been submitted for this order.")

    reference = (reference or "").strip().upper()
    pattern = UPI_UTR if order.payment_method == PaymentMethod.UPI else BANK_REF
    if not pattern.match(reference):
        raise PaymentError(
            "Enter the 12-digit UPI reference number (UTR)."
            if order.payment_method == PaymentMethod.UPI
            else "Enter the bank transfer reference number (6-30 letters or digits)."
        )
    if Payment.objects.filter(
        reference=reference, status__in=[PaymentStatus.PROOF_SUBMITTED, PaymentStatus.VERIFIED]
    ).exists():
        raise PaymentError("This reference number has already been used.")

    payment = Payment.objects.create(
        order=order, method=order.payment_method, amount=order.total,
        status=PaymentStatus.PROOF_SUBMITTED, reference=reference, proof_image=proof_image or "",
    )
    order.payment_status = PaymentStatus.PROOF_SUBMITTED
    order.save(update_fields=["payment_status", "updated_at"])
    return payment


@transaction.atomic
def set_status(payment, new_status, actor, reason=""):
    """Staff verify, reject or mark a payment collected; keeps the order in sync."""
    payment = Payment.objects.select_for_update().select_related("order").get(pk=payment.pk)
    if new_status == payment.status:
        return payment
    if new_status not in ALLOWED.get(payment.status, set()):
        raise PaymentError(
            f"{payment.order.order_no}: cannot change a payment from {payment.get_status_display()} "
            f"to {PaymentStatus(new_status).label}."
        )
    if new_status == PaymentStatus.REJECTED and not reason.strip():
        raise PaymentError("Please give a reason for rejecting the payment proof.")

    payment.status = new_status
    payment.verified_by = actor
    payment.verified_at = timezone.now()
    payment.reject_reason = reason.strip() if new_status == PaymentStatus.REJECTED else ""
    payment.save()

    order = payment.order
    order.payment_status = new_status
    order.save(update_fields=["payment_status", "updated_at"])
    return payment


@transaction.atomic
def mark_cod_collected(order, actor):
    order = Order.objects.select_for_update().get(pk=order.pk)
    if order.payment_method != PaymentMethod.COD:
        raise PaymentError(f"{order.order_no}: not a cash on delivery order.")
    if order.status not in (OrderStatus.DISPATCHED, OrderStatus.DELIVERED):
        raise PaymentError(f"{order.order_no}: cash can only be collected once the order is dispatched.")
    payment = order.payments.filter(status=PaymentStatus.COD_DUE).first()
    if payment is None:
        raise PaymentError(f"{order.order_no}: no cash payment is pending.")
    return set_status(payment, PaymentStatus.COLLECTED, actor)
