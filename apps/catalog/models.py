from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel


class Category(TimeStampedModel):
    name = models.CharField(max_length=100)
    name_bn = models.CharField("name (Bengali)", max_length=100, blank=True)
    slug = models.SlugField(unique=True)
    sort_order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name


class Product(TimeStampedModel):
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    name = models.CharField(max_length=150)
    name_bn = models.CharField("name (Bengali)", max_length=150, blank=True)
    slug = models.SlugField(unique=True)
    short_description = models.CharField(max_length=255, blank=True)
    short_description_bn = models.CharField("short description (Bengali)", max_length=255, blank=True)
    description = models.TextField(blank=True)
    description_bn = models.TextField("description (Bengali)", blank=True)
    label_image = models.ImageField(
        upload_to="products/labels/", blank=True,
        help_text=_("Photo of the product label. Dosage and claims shown to customers must match it."),
    )
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name

    def localized_name(self, language="en"):
        return self.name_bn if language == "bn" and self.name_bn else self.name


class ProductImage(TimeStampedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="products/")
    alt_text = models.CharField(max_length=150, blank=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return f"{self.product} image {self.pk}"


class ProductVariant(TimeStampedModel):
    """A sellable pack, e.g. 'Micro Max 5 kg'. Stock and price live here."""

    GST_RATES = [(Decimal("0"), "0%"), (Decimal("5"), "5%"), (Decimal("12"), "12%"), (Decimal("18"), "18%")]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    label = models.CharField(_("pack"), max_length=50, help_text=_("e.g. 1 kg, 5 kg, 10 kg"))
    sku = models.CharField(max_length=40, unique=True)
    weight_kg = models.DecimalField(max_digits=8, decimal_places=3, default=Decimal("0"))
    price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0"))],
        help_text=_("Selling price per pack, including GST."),
    )
    gst_rate = models.DecimalField(max_digits=4, decimal_places=1, choices=GST_RATES, default=Decimal("5"))
    hsn_code = models.CharField("HSN code", max_length=8, blank=True)
    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["product__sort_order", "product__name", "sort_order", "weight_kg"]
        constraints = [
            models.UniqueConstraint(fields=["product", "label"], name="unique_pack_label_per_product"),
            models.CheckConstraint(condition=models.Q(price__gte=0), name="variant_price_non_negative"),
        ]

    def __str__(self):
        return f"{self.product.name} - {self.label}"

    @property
    def in_stock(self):
        return self.stock > 0


class CropDose(TimeStampedModel):
    """Label dosage for a crop. Powers the 'how much do I need?' calculator."""

    class Unit(models.TextChoices):
        KG_PER_ACRE = "KG_ACRE", _("kg per acre")
        G_PER_TREE = "G_TREE", _("g per tree")

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="crop_doses")
    crop_name = models.CharField(max_length=100)
    crop_name_bn = models.CharField("crop name (Bengali)", max_length=100, blank=True)
    dose_min = models.DecimalField(max_digits=8, decimal_places=2)
    dose_max = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    unit = models.CharField(max_length=10, choices=Unit.choices, default=Unit.KG_PER_ACRE)
    label_note = models.CharField(max_length=200, blank=True, help_text=_("Shown as 'as per product label'."))

    class Meta:
        ordering = ["product", "crop_name"]
        verbose_name = "crop dose"

    def __str__(self):
        return f"{self.product.name}: {self.crop_name}"
