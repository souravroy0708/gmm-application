from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import SiteSetting


@admin.register(SiteSetting)
class SiteSettingAdmin(ModelAdmin):
    fieldsets = (
        ("Business", {"fields": ("business_name", "legal_address", "gstin", "cin", "state_name", "state_code")}),
        ("Contact", {"fields": ("support_phone", "whatsapp_number", "support_email")}),
        ("UPI payment", {"fields": ("upi_id", "upi_qr")}),
        ("Bank transfer", {"fields": ("bank_account_name", "bank_name", "bank_account_number", "bank_ifsc")}),
        ("Ordering rules", {"fields": ("min_order_value", "free_delivery_above")}),
        ("Cash on delivery", {"fields": ("cod_enabled", "cod_min_order", "cod_max_order")}),
    )

    def has_add_permission(self, request):
        return not SiteSetting.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
