from django.http import Http404
from django.shortcuts import render

from .data import CROPS, MONTHS, get_crop


def _calendar_rows():
    rows = []
    for c in CROPS:
        cells = []
        for m in range(1, 13):
            state = "sow" if m in c["sow"] else "harvest" if m in c["harvest"] else "grow" if m in c["grow"] else ""
            cells.append(state)
        rows.append({"crop": c, "cells": cells})
    return rows


def index(request):
    return render(request, "advisory/index.html", {"crops": CROPS, "months": MONTHS, "calendar": _calendar_rows()})


def detail(request, slug):
    crop = get_crop(slug)
    if crop is None:
        raise Http404
    others = [c for c in CROPS if c["slug"] != slug]
    wa_text = f"নমস্কার, আমি {crop['name']} চাষ নিয়ে পরামর্শ চাই।"
    return render(request, "advisory/detail.html", {"crop": crop, "others": others, "wa_text": wa_text})
