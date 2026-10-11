"""Simple sample product data. Fills only EMPTY fields (force=True overwrites).
Prices, GST, HSN and doses are SAMPLE values - confirm with GMM / your CA before going live.
"""
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.files import File

from .models import Category, CropDose, Product, ProductImage, ProductVariant

NOTE = "Use as directed on the product label."
NOTE_BN = "প্যাকেটের গায়ে লেখা নিয়ম মেনে ব্যবহার করুন।"

CATEGORY_BN = {"soil-boosters": "মাটি বুস্টার", "humic-granules": "হিউমিক দানা", "organic-manure": "জৈব সার"}

# slug: name_bn, short (en, bn), image file, packs [(label, sku, price, kg, hsn, stock)]
PRODUCTS = {
    "premium-jackpot-soil-booster": dict(
        sort=1, featured=True, name_bn="প্রিমিয়াম জ্যাকপট সয়েল বুস্টার",
        short="Soil booster for vegetables and other crops.", short_bn="সবজি ও নানা ফসলের জন্য মাটি বুস্টার।",
        image="premium-jackpot-soil-booster",
        packs=[("1 kg", "PJSB-STD", "250", "1", "3105", 100)]),
    "micro-max-jackpot-soil-booster": dict(
        sort=2, featured=False, name_bn="মাইক্রো ম্যাক্স জ্যাকপট সয়েল বুস্টার",
        short="Soil booster with a crop-wise dose.", short_bn="ফসল অনুযায়ী মাত্রা দেওয়া মাটি বুস্টার।",
        image="micro-max-jackpot-soil-booster",
        packs=[("5 kg", "MMJSB-5KG", "650", "5", "3105", 30)],
        doses=[("Paddy", "ধান", "10", "15"), ("Potato", "আলু", "12", "20"), ("Vegetables", "সবজি", "8", "12")]),
    "nirmala-agri-vita-green-gold": dict(
        sort=3, featured=True, name_bn="নির্মলা অ্যাগ্রি ভিটা গ্রিন গোল্ড",
        short="Granular soil conditioner with humic, fulvic, amino and seaweed.",
        short_bn="হিউমিক, ফুলভিক, অ্যামিনো ও শৈবালযুক্ত দানাদার মাটি উন্নয়নকারী।",
        image="nirmala-agri-vita-green-gold-1",
        packs=[("1 kg", "NAVGG-1KG", "180", "1", "3105", 80), ("10 kg", "NAVGG-10KG", "1600", "10", "3105", 50)]),
    "organic-manure-mixture": dict(
        sort=4, featured=False, name_bn="জৈব সার মিশ্রণ",
        short="Organic manure for farm use.", short_bn="চাষের জমির জন্য জৈব সার।",
        image=None, packs=[("5 kg", "OMM-STD", "150", "5", "3101", 330)]),
    "bio-organic-manure": dict(
        sort=5, featured=False, name_bn="বায়ো অর্গানিক সার",
        short="Bio-organic manure for farm use.", short_bn="চাষের জমির জন্য জৈব-জীবাণু সার।",
        image=None, packs=[("5 kg", "BOM-STD", "200", "5", "3101", 500)]),
}

EMPTY = ("", None, 0, Decimal("0"))


def _fill(obj, field, value, force):
    """Set field if empty (or force). Returns True if changed."""
    if force or getattr(obj, field) in EMPTY:
        setattr(obj, field, value)
        return True
    return False


def fill_products(queryset=None, force=False):
    """Fill sample details. Returns number of products changed."""
    qs = queryset if queryset is not None else Product.objects.all()
    photos = Path(settings.BASE_DIR) / "static" / "images" / "products"

    for cat in Category.objects.filter(slug__in=CATEGORY_BN):
        if _fill(cat, "name_bn", CATEGORY_BN[cat.slug], force):
            cat.save()

    touched = 0
    for p in qs:
        d = PRODUCTS.get(p.slug)
        if not d:
            continue

        changed = False
        for field, value in [
            ("name_bn", d["name_bn"]), ("short_description", d["short"]), ("short_description_bn", d["short_bn"]),
            ("description", f"{d['short']} {NOTE}"), ("description_bn", f"{d['short_bn']} {NOTE_BN}"),
            ("sort_order", d["sort"]),
        ]:
            changed |= _fill(p, field, value, force)
        if force:
            p.is_featured = d["featured"]
        p.is_active = True
        p.save()

        # Packs: create if missing, fill if empty
        for label, sku, price, kg, hsn, stock in d["packs"]:
            v, _ = ProductVariant.objects.get_or_create(product=p, sku=sku, defaults={"label": label})
            for field, value in [("price", Decimal(price)), ("weight_kg", Decimal(kg)),
                                 ("gst_rate", Decimal("5")), ("hsn_code", hsn), ("stock", stock)]:
                changed |= _fill(v, field, value, force)
            v.is_active = True
            v.save()

        # Crop doses (only if product has none)
        if d.get("doses") and not p.crop_doses.exists():
            for crop, crop_bn, lo, hi in d["doses"]:
                CropDose.objects.create(product=p, crop_name=crop, crop_name_bn=crop_bn,
                                        dose_min=Decimal(lo), dose_max=Decimal(hi),
                                        unit=CropDose.Unit.KG_PER_ACRE, label_note=NOTE)
            changed = True

        # Photo (only if product has none)
        img = photos / f"{d['image']}.webp" if d["image"] else None
        if img and img.exists() and not p.images.exists():
            with open(img, "rb") as fh:
                ProductImage.objects.create(product=p, alt_text=f"{p.name} pack", image=File(fh, name=img.name))
            changed = True

        touched += changed
    return touched
