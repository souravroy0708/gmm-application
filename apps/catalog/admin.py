from django.contrib import admin, messages
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import display

from .sample_data import fill_products
from .models import Category, CropDose, Product, ProductImage, ProductVariant


class ProductVariantInline(TabularInline):
    model = ProductVariant
    extra = 0
    fields = ("label", "sku", "weight_kg", "price", "gst_rate", "hsn_code", "stock", "is_active")


class ProductImageInline(TabularInline):
    model = ProductImage
    extra = 0
    fields = ("image", "alt_text", "sort_order")


class CropDoseInline(TabularInline):
    model = CropDose
    extra = 0
    fields = ("crop_name", "crop_name_bn", "dose_min", "dose_max", "unit", "label_note")


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ("name", "name_bn", "sort_order", "is_active")
    list_editable = ("sort_order", "is_active")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "name_bn")


@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_display = ("name", "category", "packs", "total_stock", "is_active", "is_featured")
    list_filter = ("category", "is_active", "is_featured")
    search_fields = ("name", "name_bn", "variants__sku")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProductVariantInline, CropDoseInline, ProductImageInline]
    actions = ["fill_sample", "fill_sample_overwrite"]
    fieldsets = (
        ("Product", {"fields": ("category", "name", "slug", "short_description", "description", "label_image")}),
        ("Bengali content", {"fields": ("name_bn", "short_description_bn", "description_bn")}),
        ("Visibility", {"fields": ("is_active", "is_featured", "sort_order")}),
    )

    @admin.action(description="Fill sample details (only empty fields)")
    def fill_sample(self, request, queryset):
        n = fill_products(queryset)
        self.message_user(request, f"Sample details filled for {n} product(s). Please review prices, GST and HSN.", messages.SUCCESS)

    @admin.action(description="Fill sample details (OVERWRITE existing values)")
    def fill_sample_overwrite(self, request, queryset):
        n = fill_products(queryset, force=True)
        self.message_user(request, f"Sample details written for {n} product(s). Please review prices, GST and HSN.", messages.WARNING)

    @display(description="Packs")
    def packs(self, obj):
        return ", ".join(v.label for v in obj.variants.all()) or "-"

    @display(description="Stock")
    def total_stock(self, obj):
        return sum(v.stock for v in obj.variants.all())

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("variants")


@admin.register(ProductVariant)
class ProductVariantAdmin(ModelAdmin):
    """Quick price and stock editing across all packs."""

    list_display = ("sku", "product", "label", "price", "gst_rate", "stock", "is_active")
    list_display_links = ("sku",)
    list_editable = ("price", "stock", "is_active")
    list_filter = ("is_active", "product__category", "gst_rate")
    search_fields = ("sku", "product__name", "label")
    list_select_related = ("product",)
