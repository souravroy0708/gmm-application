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

    def test_share_links_and_og_image(self):
        r = self.client.get(reverse("advisory:detail", args=["paddy"]))
        self.assertContains(r, "https://wa.me/?text=")
        self.assertContains(r, "facebook.com/sharer/sharer.php?u=http")
        self.assertContains(r, 'property="og:image"')
        self.assertContains(r, "images/krishi/og/paddy.png")

    def test_index_share_and_season_filter(self):
        r = self.client.get(reverse("advisory:index"))
        self.assertContains(r, "https://wa.me/?text=")
        self.assertContains(r, 'data-seasons="')
