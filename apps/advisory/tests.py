from django.test import TestCase
from django.urls import reverse

from .data import CROPS


class AdvisoryTests(TestCase):
    def test_index_lists_all_crops(self):
        r = self.client.get(reverse("advisory:index"))
        self.assertEqual(r.status_code, 200)
        for c in CROPS:
            self.assertContains(r, c["name"])

    def test_each_detail_page_renders(self):
        for c in CROPS:
            self.assertEqual(self.client.get(reverse("advisory:detail", args=[c["slug"]])).status_code, 200)

    def test_unknown_crop_404(self):
        self.assertEqual(self.client.get(reverse("advisory:detail", args=["nope"])).status_code, 404)
