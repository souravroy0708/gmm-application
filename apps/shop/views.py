import uuid

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext as _
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.accounts.models import Address
from apps.catalog.models import Product, ProductVariant
from apps.core.models import SiteSetting
from apps.invoicing.services import InvoiceError, issue_invoice
from apps.orders.models import Order, ServiceablePin
from apps.orders.services import OrderError, cancel_order, place_order
from apps.payments.services import PaymentError, submit_proof

from .cart import Cart
from .forms import AddressForm, CheckoutForm, ProofForm, RegisterForm


def _int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


# ---------- Account ----------
def register(request):
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, _("Welcome! Your account is ready."))
        return redirect("shop:products")
    return render(request, "registration/register.html", {"form": form})


# ---------- Products & cart ----------
def products(request):
    items = (
        Product.objects.filter(is_active=True)
        .prefetch_related("variants", "images")
        .order_by("sort_order", "name")
    )
    for p in items:
        p.packs = [v for v in p.variants.all() if v.is_active]
        p.default_pack = next((v for v in p.packs if v.in_stock), None)
    return render(request, "shop/products.html", {"products": [p for p in items if p.packs]})


@require_POST
def cart_add(request):
    variant = get_object_or_404(ProductVariant, pk=_int(request.POST.get("variant_id")), is_active=True)
    qty = max(_int(request.POST.get("qty"), 1), 1)
    cart = Cart(request)
    already = cart.data.get(str(variant.pk), 0)
    if already + qty > variant.stock:
        qty = max(variant.stock - already, 0)
        messages.warning(request, _("Only %(n)s available of %(name)s (%(label)s).") % {"n": variant.stock, "name": variant.product.name, "label": variant.label})
    if qty:
        cart.add(variant.pk, qty)
        messages.success(request, _("Added: %(name)s (%(label)s)") % {"name": variant.product.name, "label": variant.label})
    return redirect(request.POST.get("next") or "shop:products")


def cart_view(request):
    cart = Cart(request)
    lines = cart.lines()
    return render(request, "shop/cart.html", {"lines": lines, "subtotal": cart.subtotal(lines)})


@require_POST
def cart_update(request):
    cart = Cart(request)
    variant_id = _int(request.POST.get("variant_id"))
    if request.POST.get("action") == "remove":
        cart.remove(variant_id)
    else:
        cart.set(variant_id, _int(request.POST.get("qty")))
    return redirect("shop:cart")


# ---------- Checkout ----------
@login_required
def checkout(request):
    cart = Cart(request)
    lines = cart.lines()
    if not lines:
        messages.info(request, _("Your cart is empty."))
        return redirect("shop:products")
    addresses = list(request.user.addresses.all())
    if not addresses:
        messages.info(request, _("Please add your delivery address first."))
        return redirect("/addresses/new/?next=/checkout/")

    pins = {p.pincode: p for p in ServiceablePin.objects.filter(is_active=True,
            pincode__in=[a.pincode for a in addresses])}
    for a in addresses:
        a.pin = pins.get(a.pincode)

    form = CheckoutForm(request.POST or None, user=request.user,
                        initial={"address": addresses[0].pk, "payment_method": "COD"})
    if request.method == "POST" and form.is_valid():
        try:
            order = place_order(
                user=request.user,
                address=form.cleaned_data["address"],
                items=cart.items(),
                payment_method=form.cleaned_data["payment_method"],
                idempotency_key=request.POST.get("token") or None,
                note=form.cleaned_data["note"],
            )
        except OrderError as e:
            messages.error(request, str(e))
        else:
            cart.clear()
            messages.success(request, _("Order placed! Thank you."))
            return redirect("shop:order_detail", order_no=order.order_no)

    return render(request, "shop/checkout.html", {
        "form": form, "lines": lines, "subtotal": cart.subtotal(lines),
        "addresses": addresses, "token": uuid.uuid4().hex,
    })


# ---------- Orders ----------
@login_required
def order_list(request):
    return render(request, "shop/orders.html", {"orders": request.user.orders.all()})


@login_required
def order_detail(request, order_no):
    order = get_object_or_404(Order.objects.prefetch_related("items"), order_no=order_no, user=request.user)
    show_pay_box = order.payment_method != "COD" and order.status != "CANCELLED" \
        and order.payment_status in ("AWAITING_PROOF", "REJECTED")
    last_payment = order.payments.first()
    return render(request, "shop/order_detail.html", {
        "order": order, "cfg": SiteSetting.load(), "proof_form": ProofForm(),
        "show_pay_box": show_pay_box, "last_payment": last_payment,
        "can_invoice": order.status not in ("PLACED", "CANCELLED"),
    })


@login_required
@require_POST
def order_cancel(request, order_no):
    order = get_object_or_404(Order, order_no=order_no, user=request.user)
    try:
        cancel_order(order, actor=request.user, reason="Cancelled by customer")
        messages.success(request, _("Order cancelled."))
    except OrderError as e:
        messages.error(request, str(e))
    return redirect("shop:order_detail", order_no=order_no)


@login_required
@require_POST
def order_pay(request, order_no):
    order = get_object_or_404(Order, order_no=order_no, user=request.user)
    form = ProofForm(request.POST, request.FILES)
    if form.is_valid():
        try:
            submit_proof(order, form.cleaned_data["reference"], form.cleaned_data["proof_image"])
            messages.success(request, _("Payment details sent. We will check and confirm soon."))
        except PaymentError as e:
            messages.error(request, str(e))
    else:
        messages.error(request, _("Please enter the payment reference number."))
    return redirect("shop:order_detail", order_no=order_no)


@login_required
def invoice(request, order_no):
    order = get_object_or_404(Order.objects.prefetch_related("items"), order_no=order_no, user=request.user)
    try:
        inv = issue_invoice(order)
    except InvoiceError as e:
        messages.info(request, _("Your invoice will be ready after we confirm the order."))
        return redirect("shop:order_detail", order_no=order_no)
    return render(request, "shop/invoice.html", {"order": order, "inv": inv, "seller": inv.seller_snapshot})


# ---------- Addresses ----------
@login_required
def address_list(request):
    return render(request, "shop/addresses.html", {"addresses": request.user.addresses.all()})


@login_required
def address_form(request, pk=None):
    address = get_object_or_404(Address, pk=pk, user=request.user) if pk else None
    form = AddressForm(request.POST or None, instance=address, user=request.user,
                       initial={} if address else {"full_name": request.user.name, "phone": request.user.phone})
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, _("Address saved."))
        nxt = request.GET.get("next", "")
        return redirect(nxt if nxt.startswith("/") and not nxt.startswith("//") else "shop:addresses")
    return render(request, "shop/address_form.html", {"form": form, "editing": bool(address)})


@login_required
@require_POST
def address_delete(request, pk):
    get_object_or_404(Address, pk=pk, user=request.user).delete()
    messages.success(request, _("Address removed."))
    return redirect("shop:addresses")


@login_required
@require_POST
def address_default(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    address.is_default = True
    address.save()
    return redirect("shop:addresses")
