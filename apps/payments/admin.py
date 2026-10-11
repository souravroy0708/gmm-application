from django import forms
from django.contrib import admin, messages
from django.utils.html import format_html
from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import RangeDateFilter
from unfold.decorators import display

from apps.core.constants import PaymentStatus

from . import services
from .models import Payment
from .services import PaymentError

STATUS_COLORS = {
    "COD_DUE": "warning",
    "COLLECTED": "success",
    "AWAITING_PROOF": "warning",
    "PROOF_SUBMITTED": "info",
    "VERIFIED": "success",
    "REJECTED": "danger",
}


class PaymentAdminForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ("status", "reject_reason", "note")

    def clean(self):
        data = super().clean()
        if data.get("status") == PaymentStatus.REJECTED and not (data.get("reject_reason") or "").strip():
            self.add_error("reject_reason", "Give a reason so the customer knows what to fix.")
        return data


@admin.register(Payment)
class PaymentAdmin(ModelAdmin):
    form = PaymentAdminForm
    list_display = ("order", "method", "amount", "status_badge", "reference", "created_at")
    list_filter = ("status", "method", ("created_at", RangeDateFilter))
    search_fields = ("order__order_no", "reference", "order__user__phone", "order__user__name")
    list_select_related = ("order",)
    actions = ["verify_selected"]
    fieldsets = (
        ("Payment", {"fields": ("order", "method", "amount", "reference", "proof_preview", "created_at")}),
        ("Review", {"fields": ("status", "reject_reason", "note", "verified_by", "verified_at")}),
    )
    readonly_fields = ("order", "method", "amount", "reference", "proof_preview", "created_at", "verified_by", "verified_at")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @display(description="Status", ordering="status", label=STATUS_COLORS)
    def status_badge(self, obj):
        return obj.status

    @display(description="Proof")
    def proof_preview(self, obj):
        if obj.proof_image:
            return format_html('<a href="{}" target="_blank" rel="noopener">Open screenshot</a>', obj.proof_image.url)
        return "No screenshot uploaded"

    def save_model(self, request, obj, form, change):
        if change and "status" in form.changed_data:
            new_status, reason = obj.status, obj.reject_reason
            obj.status = Payment.objects.get(pk=obj.pk).status  # let the service apply the change
            super().save_model(request, obj, form, change)
            try:
                services.set_status(obj, new_status, request.user, reason)
            except PaymentError as exc:
                self.message_user(request, str(exc), messages.ERROR)
        else:
            super().save_model(request, obj, form, change)

    @admin.action(description="Verify selected payment proofs")
    def verify_selected(self, request, queryset):
        done = 0
        for payment in queryset:
            try:
                services.set_status(payment, PaymentStatus.VERIFIED, request.user)
                done += 1
            except PaymentError as exc:
                self.message_user(request, str(exc), messages.ERROR)
        if done:
            self.message_user(request, f"{done} payment(s) verified.", messages.SUCCESS)
