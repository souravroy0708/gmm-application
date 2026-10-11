from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User


class ThoughtCardTests(TestCase):
    def setUp(self):
        self.url = reverse("thoughts:create")
        self.staff = User.objects.create_user("9876543210", name="Ravi Das", password="s3cret-pass-123", is_staff=True)
        self.customer = User.objects.create_user("9876543211", name="Customer", password="s3cret-pass-123")

    def test_anonymous_is_sent_to_login(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 302)
        self.assertIn(reverse("shop:login"), r["Location"])
        self.assertIn("next=", r["Location"])

    def test_customer_is_forbidden(self):
        self.client.force_login(self.customer)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_staff_sees_the_maker(self):
        self.client.force_login(self.staff)
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'id="thCanvas"')
        self.assertContains(r, "images/logo.jpg")
        self.assertContains(r, "js/thoughts.js")
        self.assertContains(r, 'maxlength="160"')

    def test_author_name_is_prefilled_and_escaped(self):
        self.staff.name = '<b>"x"</b>'
        self.staff.save()
        self.client.force_login(self.staff)
        r = self.client.get(self.url)
        self.assertNotContains(r, '<b>"x"</b>')
        self.assertContains(r, "&lt;b&gt;")
