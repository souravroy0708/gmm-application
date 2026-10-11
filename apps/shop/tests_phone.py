from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from apps.core.models import SiteSetting
from apps.shop.templatetags.shop_tags import phone_pretty, tel_num, wa_num

FORMS = ["9083732101", "919083732101", "+919083732101", "+91 90837-32101", "09083732101", " 91 90837 32101 "]


class PhoneFilterTests(SimpleTestCase):
    def test_every_typing_style_gives_the_same_result(self):
        for raw in FORMS:
            self.assertEqual(wa_num(raw), "919083732101", raw)
            self.assertEqual(tel_num(raw), "+919083732101", raw)
            self.assertEqual(phone_pretty(raw), "+91 90837 32101", raw)

    def test_empty(self):
        self.assertEqual(wa_num(""), "")
        self.assertEqual(tel_num(None), "")


class PhoneLinkPageTests(TestCase):
    def check_pages(self, phone, wa):
        s = SiteSetting.load()
        s.support_phone, s.whatsapp_number = phone, wa
        s.save()
        for name in ["shop:products", "pages:contact", "advisory:index", "advisory:detail"]:
            args = ["paddy"] if name == "advisory:detail" else []
            html = self.client.get(reverse(name, args=args)).content.decode()
            self.assertNotIn("91919083732101", html, name)
            self.assertNotIn("+91+91", html, name)
            self.assertNotIn("tel:9083732101", html, name)
            self.assertIn("https://wa.me/919083732101", html, name)
            self.assertIn("tel:+919083732101", html, name)

    def test_number_stored_with_country_code(self):
        self.check_pages("9083732101", "919083732101")

    def test_number_stored_as_ten_digits(self):
        self.check_pages("9083732101", "9083732101")

    def test_number_stored_with_plus_and_spaces(self):
        self.check_pages("+91 90837 32101", "+91 90837-32101")
