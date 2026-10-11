from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User


class ThoughtCardTests(TestCase):
    def setUp(self):
        self.url = reverse("thoughts:create")

    def test_open_to_visitors_without_login(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'id="thCanvas"')
        self.assertContains(r, "images/logo.jpg")
        self.assertContains(r, "js/thoughts.js")
        self.assertContains(r, 'maxlength="160"')

    def test_disclaimer_in_english(self):
        self.client.cookies["django_language"] = "en"
        r = self.client.get(self.url)
        self.assertContains(r, 'class="th-disc"')
        self.assertContains(r, "not responsible for any misuse")

    def test_disclaimer_in_bengali(self):
        self.client.cookies["django_language"] = "bn"
        r = self.client.get(self.url)
        self.assertContains(r, 'class="th-disc"')
        self.assertContains(r, "দাবিত্যাগ")

    def test_visitor_name_box_starts_empty(self):
        r = self.client.get(self.url)
        self.assertContains(r, 'id="thName" maxlength="40" value=""')

    def test_logged_in_name_is_prefilled_and_escaped(self):
        user = User.objects.create_user("9876543211", name='<b>"x"</b>', password="s3cret-pass-123")
        self.client.force_login(user)
        r = self.client.get(self.url)
        self.assertNotContains(r, '<b>"x"</b>')
        self.assertContains(r, "&lt;b&gt;")

    def test_footer_link_visible_to_everyone(self):
        r = self.client.get(reverse("shop:products"))
        self.assertContains(r, self.url)


class ThoughtHighlightTests(TestCase):
    """The daily-use entry points: raised tab, home banner, desktop header pill."""

    def test_home_has_banner_tab_and_header_pill(self):
        r = self.client.get(reverse("shop:products"))
        self.assertContains(r, 'class="kp-promo th-promo"')
        self.assertContains(r, 'class="th-tab ')
        self.assertContains(r, 'class="thbtn"')
        self.assertContains(r, "thoughts-nav.css")
        self.assertContains(r, 'id="i-quote"')

    def test_tab_is_marked_active_on_the_thoughts_page(self):
        r = self.client.get(reverse("thoughts:create"))
        self.assertContains(r, 'class="th-tab on"')

    def test_tab_present_on_other_pages_too(self):
        for name in ["pages:contact", "advisory:index", "shop:cart"]:
            self.assertContains(self.client.get(reverse(name)), 'class="th-tab ', msg_prefix=name)
