from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Invoice


@admin.register(Invoice)
class InvoiceAdmin(ModelAdmin):
    """Invoices are issued from the Orders screen and are read-only afterwards."""

    list_display = ("invoice_no", "order", "financial_year", "issued_at", "cgst", "sgst", "igst")
    list_filter = ("financial_year", "is_interstate")
    search_fields = ("invoice_no", "order__order_no", "order__user__phone")
    list_select_related = ("order",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
