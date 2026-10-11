from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.core.models import Sequence, SiteSetting
from apps.orders.models import Order, OrderStatus
from apps.orders.services import money

from .models import Invoice


class InvoiceError(Exception):
    """A rule was broken; the message is safe to show to staff."""


def financial_year(day):
    """India's financial year runs April-March, e.g. 2026-27."""
    start = day.year if day.month >= 4 else day.year - 1
    return f"{start}-{(start + 1) % 100:02d}"


@transaction.atomic
def issue_invoice(order):
    """Issue (once) the tax invoice for a confirmed order. Idempotent."""
    order = Order.objects.select_for_update().get(pk=order.pk)
    existing = Invoice.objects.filter(order=order).first()
    if existing:
        return existing
    if order.status in (OrderStatus.PLACED, OrderStatus.CANCELLED):
        raise InvoiceError(f"{order.order_no}: confirm the order before issuing an invoice.")

    cfg = SiteSetting.load()
    fy = financial_year(timezone.localdate())
    # Same transaction as the invoice row, so a failure never burns a number.
    number = Sequence.next(f"invoice:{fy}")
    invoice_no = f"GMM/{fy}/{number:04d}"
    if len(invoice_no) > 16:  # GST rule: invoice number up to 16 characters
        raise InvoiceError("Invoice number exceeds 16 characters; change the numbering format with your CA.")

    buyer_state = (order.address_snapshot or {}).get("state", "").strip().lower()
    interstate = bool(buyer_state) and buyer_state != cfg.state_name.strip().lower()
    tax = order.tax_total  # delivery charges are not taxed in v1 - confirm with your CA
    if interstate:
        cgst = sgst = Decimal("0.00")
        igst = tax
    else:
        cgst = money(tax / 2)
        sgst = tax - cgst
        igst = Decimal("0.00")

    return Invoice.objects.create(
        order=order,
        invoice_no=invoice_no,
        financial_year=fy,
        seller_snapshot={
            "name": cfg.business_name, "gstin": cfg.gstin, "cin": cfg.cin,
            "address": cfg.legal_address, "state": cfg.state_name, "state_code": cfg.state_code,
        },
        is_interstate=interstate,
        cgst=cgst, sgst=sgst, igst=igst,
    )
