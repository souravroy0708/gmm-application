from urllib.parse import quote

from django.http import Http404
from django.shortcuts import render
from django.templatetags.static import static
from django.utils import timezone

from .data import CROPS, DAILY_TIPS, MONTHS, crop_image, crop_og, get_crop


def _seasons(c):
    sow, out = set(c["sow"]), []
    if sow & {3, 4, 5}:
        out.append("summer")
    if sow & {6, 7, 8}:
        out.append("monsoon")
    if sow & {9, 10, 11, 12, 1, 2}:
        out.append("winter")
    return " ".join(out)


def _prep(c):
    return dict(c, img=crop_image(c["slug"]), og=crop_og(c["slug"]), seasons=_seasons(c))


def _calendar_rows(crops):
    rows = []
    for c in crops:
        cells = ["sow" if m in c["sow"] else "harvest" if m in c["harvest"] else "grow" if m in c["grow"] else "" for m in range(1, 13)]
        rows.append({"crop": c, "cells": cells})
    return rows


def _share(request, title, text, og_rel):
    url = request.build_absolute_uri(request.path)
    return {
        "share_url": url, "share_title": title, "share_text": text,
        "og_image": request.build_absolute_uri(static(og_rel)),
        "wa_link": "https://wa.me/?text=" + quote(f"{text}\n{url}"),
        "fb_link": "https://www.facebook.com/sharer/sharer.php?u=" + quote(url, safe=""),
    }


def index(request):
    crops = [_prep(c) for c in CROPS]
    now = timezone.localtime().month
    ctx = {
        "crops": crops, "months": MONTHS, "calendar": _calendar_rows(crops), "now": now, "now_name": MONTHS[now - 1],
        "sow_now": [c for c in crops if now in c["sow"]], "harvest_now": [c for c in crops if now in c["harvest"]],
        "tip": DAILY_TIPS[timezone.localdate().toordinal() % len(DAILY_TIPS)],
        "hero_img": crops[0]["img"],
    }
    ctx.update(_share(request, "কৃষি পরামর্শ | GMM Distributors",
                      "🌾 ধান, আলু, পাট, সরিষা ও সবজি চাষের সহজ বাংলা গাইড — GMM কৃষি পরামর্শ", crops[0]["og"]))
    return render(request, "advisory/index.html", ctx)


def detail(request, slug):
    base = get_crop(slug)
    if base is None:
        raise Http404
    crop = _prep(base)
    others = [_prep(c) for c in CROPS if c["slug"] != slug]
    ctx = {"crop": crop, "others": others, "wa_text": f"নমস্কার, আমি {crop['name']} চাষ নিয়ে পরামর্শ চাই।"}
    ctx.update(_share(request, f"{crop['name']} চাষের পরামর্শ | GMM",
                      f"🌱 {crop['name']} চাষ: জাত, সার, রোগ-পোকা ও ভুল এড়ানোর সহজ বাংলা গাইড — GMM কৃষি পরামর্শ", crop["og"]))
    return render(request, "advisory/detail.html", ctx)
