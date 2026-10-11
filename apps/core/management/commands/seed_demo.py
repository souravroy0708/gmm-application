from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.catalog.models import Category, CropDose, Product, ProductVariant
from apps.core.models import SiteSetting
from apps.orders.models import ServiceablePin

KG, TREE = CropDose.Unit.KG_PER_ACRE, CropDose.Unit.G_PER_TREE
LABEL = "As stated on the product label"


class Command(BaseCommand):
    help = (
        "Load GMM's launch catalogue and business details (from gmmdistributors.xyz). "
        "Prices, stock and GST rates are placeholders - variants stay INACTIVE until you set them."
    )

    @transaction.atomic
    def handle(self, *args, **options):
        cfg = SiteSetting.load()
        cfg.business_name = "GMM Distributors Private Limited"
        cfg.legal_address = "Nirmala Bhawan, Fansi Bagan, Ward No. 13, Arambagh, Hooghly, West Bengal - 712601"
        cfg.cin = "U24299WB2020PTC240755"
        cfg.support_phone = "9083732101"
        cfg.whatsapp_number = "919083732101"
        cfg.support_email = "ray.chikur@gmail.com"
        cfg.save()

        ServiceablePin.objects.get_or_create(pincode="712601", defaults={"area_name": "Arambagh, Hooghly"})

        cats = {}
        for slug, name, name_bn, order in [
            ("soil-boosters", "Soil Boosters", "মাটি বুস্টার", 1),
            ("humic-granules", "Humic Granules", "হিউমিক সার", 2),
            ("organic-manure", "Organic Manure", "জৈব সার", 3),
        ]:
            cats[slug], _created = Category.objects.update_or_create(
                slug=slug, defaults={"name": name, "name_bn": name_bn, "sort_order": order}
            )

        catalogue = [
            ("soil-boosters", "premium-jackpot-soil-booster", "Premium Jackpot Soil Booster",
             "Soil booster for vegetables and a range of crops.", [("Standard pack", "PJSB-STD", "0")], []),
            ("soil-boosters", "micro-max-jackpot-soil-booster", "Micro Max Jackpot Soil Booster",
             "Soil booster with a crop-wise dosage schedule.", [("5 kg", "MMJSB-5KG", "5")],
             [("Rice", 3, None, KG), ("Maize", 3, None, KG), ("Beans", 3, None, KG),
              ("Potato", 4, None, KG), ("Brinjal", 4, None, KG), ("Tomato", 4, None, KG),
              ("Fruit trees", 70, 80, TREE)]),
            ("humic-granules", "nirmala-agri-vita-green-gold", "Nirmala Agri Vita Green Gold",
             "Granulated soil conditioner with humic, fulvic, amino, seaweed and bentonite.",
             [("1 kg", "NAVGG-1KG", "1"), ("10 kg", "NAVGG-10KG", "10")],
             [("Vegetables and fruit crops", 10, 12, KG)]),
            ("organic-manure", "organic-manure-mixture", "Organic Manure Mixture",
             "Organic manure for agricultural use.", [("Standard pack", "OMM-STD", "0")], []),
            ("organic-manure", "bio-organic-manure", "Bio Organic Manure",
             "Bio-organic manure for agricultural use.", [("Standard pack", "BOM-STD", "0")], []),
        ]
        for i, (cat, slug, name, desc, variants, doses) in enumerate(catalogue, start=1):
            product, _created = Product.objects.update_or_create(
                slug=slug,
                defaults={"category": cats[cat], "name": name, "short_description": desc, "sort_order": i},
            )
            for label, sku, kg in variants:
                ProductVariant.objects.get_or_create(
                    sku=sku,
                    defaults={
                        "product": product, "label": label, "weight_kg": Decimal(kg),
                        "price": Decimal("0.00"), "stock": 0, "is_active": False,
                    },
                )
            for crop, dmin, dmax, unit in doses:
                CropDose.objects.get_or_create(
                    product=product, crop_name=crop,
                    defaults={"dose_min": dmin, "dose_max": dmax, "unit": unit, "label_note": LABEL},
                )

        self.stdout.write(self.style.SUCCESS("Seeded settings, 1 PIN code, 3 categories and 5 products."))
        self.stdout.write(
            "Next: in the admin set pack sizes, prices, GST rates, HSN codes and stock, "
            "then activate each pack. Also add your GSTIN, UPI ID and bank details in Business settings."
        )
