from django.contrib import admin, messages
from django.utils.html import format_html, format_html_join
from unfold.admin import ModelAdmin, TabularInline
from unfold.contrib.filters.admin import RangeDateFilter
from unfold.decorators import display

from apps.invoicing import services as invoice_services
from apps.invoicing.services import InvoiceError
from apps.payments import services as payment_services
from apps.payments.models import Payment
from apps.payments.services import PaymentError

from . import services
from .models import Order, OrderItem, OrderStatus, OrderStatusLog, ServiceablePin
from .services import OrderError

STATUS_COLORS = {
    OrderStatus.PLACED: "info",
    OrderStatus.CONFIRMED: "info",
    OrderStatus.PACKED: "warning",
    OrderStatus.DISPATCHED: "warning",
    OrderStatus.DELIVERED: "success",
    OrderStatus.CANCELLED: "danger",
}
PAYMENT_COLORS = {
    "COD_DUE": "warning",
    "COLLECTED": "success",
    "AWAITING_PROOF": "warning",
    "PROOF_SUBMITTED": "info",
    "VERIFIED": "success",
    "REJECTED": "danger",
}


class ReadOnlyInline(TabularInline):
    extra = 0
    can_delete = False

    def get_readonly_fields(self, request, obj=None):
        return list(self.fields)  # every column is display-only

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class OrderItemInline(ReadOnlyInline):
    model = OrderItem
    fields = ("product_name", "variant_label", "sku", "quantity", "unit_price", "gst_rate", "line_total")


class OrderStatusLogInline(ReadOnlyInline):
    model = OrderStatusLog
    fields = ("created_at", "from_status", "to_status", "actor", "note")


class PaymentInline(ReadOnlyInline):
    model = Payment
    fields = ("created_at", "method", "amount", "status", "reference", "proof_image", "reject_reason")
    show_change_link = True


@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = ("order_no", "customer", "status_badge", "payment_method", "payment_badge", "total", "pincode", "created_at")
    list_filter = ("status", "payment_method", "payment_status", ("created_at", RangeDateFilter))
    search_fields = ("order_no", "user__phone", "user__name")
    list_select_related = ("user",)
    date_hierarchy = "created_at"
    inlines = [OrderItemInline, PaymentInline, OrderStatusLogInline]
    fieldsets = (
        ("Order", {"fields": ("order_no", "user", "status", "payment_method", "payment_status", "created_at", "placed_by")}),
        ("Delivery", {"fields": ("address_display", "customer_note")}),
        ("Amounts (Rs.)", {"fields": ("subtotal", "tax_total", "delivery_fee", "total")}),
        ("Cancellation", {"fields": ("cancel_reason",)}),
    )
    actions = [
        "confirm_orders", "mark_packed", "mark_dispatched", "mark_delivered",
        "cancel_orders", "mark_cod_collected", "issue_invoices",
    ]

    # Orders are created through the order service and changed through actions,
    # so money fields and history can never be edited by hand.
    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in self.model._meta.fields] + ["address_display"]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @display(description="Customer", ordering="user__name")
    def customer(self, obj):
        return f"{obj.user.name} ({obj.user.phone})"

    @display(description="Status", ordering="status", label=STATUS_COLORS)
    def status_badge(self, obj):
        return obj.status

    @display(description="Payment", ordering="payment_status", label=PAYMENT_COLORS)
    def payment_badge(self, obj):
        return obj.payment_status

    @display(description="Delivery address")
    def address_display(self, obj):
        a = obj.address_snapshot or {}
        lines = [
            a.get("full_name"), a.get("phone"), a.get("line1"), a.get("line2"),
            f"{a.get('village_town', '')}, {a.get('post_office', '')}".strip(", "),
            f"{a.get('district', '')}, {a.get('state', '')} - {a.get('pincode', '')}",
            a.get("landmark"),
        ]
        return format_html_join("", "{}<br>", ((line,) for line in lines if line))

    def _run(self, request, queryset, func, done_text):
        done = 0
        for order in queryset:
            try:
                func(order)
                done += 1
            except (OrderError, PaymentError, InvoiceError) as exc:
                self.message_user(request, str(exc), messages.ERROR)
        if done:
            self.message_user(request, f"{done} order(s) {done_text}.", messages.SUCCESS)

    def _move(self, request, queryset, status, text, note=""):
        self._run(request, queryset, lambda o: services.change_status(o, status, request.user, note), text)

    @admin.action(description="Confirm selected orders")
    def confirm_orders(self, request, queryset):
        self._move(request, queryset, OrderStatus.CONFIRMED, "confirmed")

    @admin.action(description="Mark as packed")
    def mark_packed(self, request, queryset):
        self._move(request, queryset, OrderStatus.PACKED, "marked packed")

    @admin.action(description="Mark as dispatched")
    def mark_dispatched(self, request, queryset):
        self._move(request, queryset, OrderStatus.DISPATCHED, "dispatched")

    @admin.action(description="Mark as delivered")
    def mark_delivered(self, request, queryset):
        self._move(request, queryset, OrderStatus.DELIVERED, "marked delivered")

    @admin.action(description="Cancel selected orders (restores stock)")
    def cancel_orders(self, request, queryset):
        self._move(request, queryset, OrderStatus.CANCELLED, "cancelled", note="Cancelled by staff")

    @admin.action(description="Mark COD cash as collected")
    def mark_cod_collected(self, request, queryset):
        self._run(request, queryset, lambda o: payment_services.mark_cod_collected(o, request.user), "marked as cash collected")

    @admin.action(description="Issue invoice for selected orders")
    def issue_invoices(self, request, queryset):
        self._run(request, queryset, invoice_services.issue_invoice, "invoiced")


@admin.register(ServiceablePin)
class ServiceablePinAdmin(ModelAdmin):
    list_display = ("pincode", "area_name", "delivery_fee", "cod_allowed", "is_active")
    list_display_links = ("pincode",)
    list_editable = ("delivery_fee", "cod_allowed", "is_active")
    list_filter = ("is_active", "cod_allowed")
    search_fields = ("pincode", "area_name")
