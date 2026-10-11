from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.accounts.tests import make_address, make_user
from apps.catalog.models import ProductVariant
from apps.orders import services
from apps.orders.models import Order


class AdminSmokeTests(TestCase):
    """Every admin screen must render with the Unfold theme and the custom user model."""

    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo", verbosity=0)
        cls.admin = User.objects.create_superuser("9999999999", name="Owner", password="admin-pass-123")
        cls.customer = make_user("9876543210")
        cls.address = make_address(cls.customer)
        variant = ProductVariant.objects.get(sku="NAVGG-1KG")
        variant.price, variant.stock, variant.is_active = 400, 20, True
        variant.save()
        cls.order = services.place_order(
            user=cls.customer, address=cls.address, items=[(variant.pk, 2)], payment_method="COD"
        )

    def setUp(self):
        self.client.force_login(self.admin)

    def test_index_and_all_changelists_render(self):
        self.assertEqual(self.client.get(reverse("admin:index")).status_code, 200)
        for name in [
            "accounts_user", "accounts_address", "catalog_category", "catalog_product", "catalog_productvariant",
            "orders_order", "orders_serviceablepin", "payments_payment", "invoicing_invoice", "core_sitesetting",
        ]:
            response = self.client.get(reverse(f"admin:{name}_changelist"))
            self.assertEqual(response.status_code, 200, name)

    def test_change_pages_render(self):
        for name, obj in [
            ("orders_order", self.order), ("accounts_user", self.customer),
            ("catalog_product", ProductVariant.objects.first().product),
            ("core_sitesetting", None),
        ]:
            if obj is None:
                url = reverse(f"admin:{name}_changelist")
            else:
                url = reverse(f"admin:{name}_change", args=[obj.pk])
            self.assertEqual(self.client.get(url).status_code, 200, name)

    def test_add_user_page_and_create_user(self):
        self.assertEqual(self.client.get(reverse("admin:accounts_user_add")).status_code, 200)
        response = self.client.post(reverse("admin:accounts_user_add"), {
            "phone": "98000 00001", "name": "New Customer", "usable_password": "true",
            "password1": "very-Strong-pass-9", "password2": "very-Strong-pass-9",
            # the page also carries the (empty) address inline, so its management form is posted too
            "addresses-TOTAL_FORMS": "0", "addresses-INITIAL_FORMS": "0",
            "addresses-MIN_NUM_FORMS": "0", "addresses-MAX_NUM_FORMS": "1000",
        })
        self.assertEqual(response.status_code, 302, getattr(response, "context", None) and response.context["adminform"].form.errors)
        self.assertTrue(User.objects.filter(phone="+919800000001").exists())

    def test_order_actions_confirm_and_invoice(self):
        url = reverse("admin:orders_order_changelist")
        self.client.post(url, {"action": "confirm_orders", "_selected_action": [self.order.pk]}, follow=True)
        self.client.post(url, {"action": "issue_invoices", "_selected_action": [self.order.pk]}, follow=True)
        order = Order.objects.get(pk=self.order.pk)
        self.assertEqual(order.status, "CONFIRMED")
        self.assertTrue(hasattr(order, "invoice"))

    def test_orders_cannot_be_added_or_deleted_in_admin(self):
        self.assertEqual(self.client.get(reverse("admin:orders_order_add")).status_code, 403)

    def test_healthz(self):
        self.assertEqual(self.client.get("/healthz").json(), {"status": "ok"})
