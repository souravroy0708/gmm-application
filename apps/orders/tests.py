from decimal import Decimal

from django.test import TestCase

from apps.accounts.tests import make_address, make_user
from apps.catalog.models import Category, Product, ProductVariant
from apps.core.constants import PaymentMethod, PaymentStatus
from apps.core.models import SiteSetting
from apps.invoicing import services as invoice_services
from apps.invoicing.services import InvoiceError, financial_year
from apps.payments import services as payment_services
from apps.payments.services import PaymentError

from . import services
from .models import OrderStatus, ServiceablePin
from .services import OrderError


class Base(TestCase):
    def setUp(self):
        self.user = make_user()
        self.address = make_address(self.user)
        self.staff = make_user("9000000001", "Staff")
        ServiceablePin.objects.create(pincode="712601", delivery_fee=Decimal("50.00"))
        cat = Category.objects.create(name="Soil Boosters", slug="sb")
        self.product = Product.objects.create(category=cat, name="Micro Max", slug="micro-max")
        self.v5 = ProductVariant.objects.create(
            product=self.product, label="5 kg", sku="MM-5", price=Decimal("1050.00"),
            gst_rate=Decimal("5"), stock=10,
        )
        self.v1 = ProductVariant.objects.create(
            product=self.product, label="1 kg", sku="MM-1", price=Decimal("250.00"),
            gst_rate=Decimal("5"), stock=3,
        )

    def order(self, items=None, method=PaymentMethod.COD, **kw):
        return services.place_order(
            user=self.user, address=self.address, items=items or [(self.v5.pk, 2)],
            payment_method=method, **kw,
        )


class PlaceOrderTests(Base):
    def test_totals_tax_stock_and_logs(self):
        order = self.order([(self.v5.pk, 2), (self.v1.pk, 1)])
        self.assertRegex(order.order_no, r"^GMM-\d{6}-0001$")
        self.assertEqual(order.subtotal, Decimal("2350.00"))
        self.assertEqual(order.delivery_fee, Decimal("50.00"))
        self.assertEqual(order.total, Decimal("2400.00"))
        # 5% GST included in the price: 2350 - 2350/1.05 = 111.90
        self.assertEqual(order.tax_total, Decimal("111.90"))
        self.assertEqual(sum(i.taxable_value + i.tax_amount for i in order.items.all()), order.subtotal)
        self.v5.refresh_from_db(); self.v1.refresh_from_db()
        self.assertEqual((self.v5.stock, self.v1.stock), (8, 2))
        self.assertEqual(order.status, OrderStatus.PLACED)
        self.assertEqual(order.payment_status, PaymentStatus.COD_DUE)
        self.assertEqual(order.payments.count(), 1)
        self.assertEqual(order.status_logs.count(), 1)
        self.assertEqual(order.address_snapshot["pincode"], "712601")

    def test_order_numbers_are_sequential(self):
        self.assertTrue(self.order().order_no.endswith("0001"))
        self.assertTrue(self.order().order_no.endswith("0002"))

    def test_snapshot_survives_catalogue_changes(self):
        order = self.order()
        self.v5.price = Decimal("9999.00"); self.v5.save()
        self.address.village_town = "Changed"; self.address.save()
        order.refresh_from_db()
        self.assertEqual(order.items.get().unit_price, Decimal("1050.00"))
        self.assertEqual(order.address_snapshot["village_town"], "Arambagh")

    def test_insufficient_stock_changes_nothing(self):
        with self.assertRaises(OrderError):
            self.order([(self.v1.pk, 4)])
        self.v1.refresh_from_db()
        self.assertEqual(self.v1.stock, 3)

    def test_last_unit_cannot_be_sold_twice(self):
        self.order([(self.v1.pk, 3)])
        with self.assertRaises(OrderError):
            self.order([(self.v1.pk, 1)])

    def test_idempotency_key_prevents_duplicate_orders(self):
        a = self.order(idempotency_key="abc-123")
        b = self.order(idempotency_key="abc-123")
        self.assertEqual(a.pk, b.pk)
        self.v5.refresh_from_db()
        self.assertEqual(self.v5.stock, 8)

    def test_unserviceable_pin_rejected(self):
        far = make_address(self.user, pincode="110001", is_default=True)
        with self.assertRaises(OrderError):
            services.place_order(user=self.user, address=far, items=[(self.v5.pk, 1)], payment_method="COD")

    def test_cannot_use_someone_elses_address(self):
        other = make_address(make_user("9111111111", "Other"))
        with self.assertRaises(OrderError):
            services.place_order(user=self.user, address=other, items=[(self.v5.pk, 1)], payment_method="COD")

    def test_inactive_variant_rejected(self):
        self.v5.is_active = False; self.v5.save()
        with self.assertRaises(OrderError):
            self.order()

    def test_cod_limits_and_min_order(self):
        cfg = SiteSetting.load()
        cfg.cod_max_order = Decimal("1000.00"); cfg.save()
        with self.assertRaises(OrderError):
            self.order()  # 2150 > 1000
        self.assertEqual(self.order(method=PaymentMethod.UPI).payment_status, PaymentStatus.AWAITING_PROOF)
        cfg.min_order_value = Decimal("5000.00"); cfg.save()
        with self.assertRaises(OrderError):
            self.order(method=PaymentMethod.UPI)

    def test_free_delivery_threshold(self):
        cfg = SiteSetting.load(); cfg.free_delivery_above = Decimal("2000.00"); cfg.save()
        self.assertEqual(self.order().delivery_fee, Decimal("0.00"))

    def test_staff_on_behalf_order_is_recorded(self):
        order = self.order(placed_by=self.staff)
        self.assertEqual(order.placed_by, self.staff)


class StatusTests(Base):
    def test_happy_path_and_log(self):
        order = self.order()
        for status in [OrderStatus.CONFIRMED, OrderStatus.PACKED, OrderStatus.DISPATCHED, OrderStatus.DELIVERED]:
            order = services.change_status(order, status, actor=self.staff)
        self.assertEqual(order.status_logs.count(), 5)

    def test_illegal_jump_rejected(self):
        with self.assertRaises(OrderError):
            services.change_status(self.order(), OrderStatus.DELIVERED, self.staff)

    def test_cancel_restores_stock_and_is_final(self):
        order = self.order()
        services.cancel_order(order, self.staff, "Customer asked")
        self.v5.refresh_from_db()
        self.assertEqual(self.v5.stock, 10)
        with self.assertRaises(OrderError):
            services.change_status(order, OrderStatus.CONFIRMED, self.staff)

    def test_cannot_cancel_after_dispatch(self):
        order = self.order()
        for s in [OrderStatus.CONFIRMED, OrderStatus.PACKED, OrderStatus.DISPATCHED]:
            order = services.change_status(order, s, self.staff)
        with self.assertRaises(OrderError):
            services.cancel_order(order, self.staff)

    def test_prepaid_cannot_dispatch_before_payment_verified(self):
        order = self.order(method=PaymentMethod.UPI)
        services.change_status(order, OrderStatus.CONFIRMED, self.staff)
        services.change_status(order, OrderStatus.PACKED, self.staff)
        with self.assertRaises(OrderError):
            services.change_status(order, OrderStatus.DISPATCHED, self.staff)
        payment = payment_services.submit_proof(order, "123456789012")
        payment_services.set_status(payment, PaymentStatus.VERIFIED, self.staff)
        self.assertEqual(services.change_status(order, OrderStatus.DISPATCHED, self.staff).status, OrderStatus.DISPATCHED)


class PaymentTests(Base):
    def setUp(self):
        super().setUp()
        self.order_obj = self.order(method=PaymentMethod.UPI)

    def test_utr_format_enforced(self):
        for bad in ["", "12345", "ABCDEFGHIJKL", "1234567890123"]:
            with self.assertRaises(PaymentError):
                payment_services.submit_proof(self.order_obj, bad)

    def test_submit_verify_flow_updates_order(self):
        payment = payment_services.submit_proof(self.order_obj, " 123456789012 ")
        self.order_obj.refresh_from_db()
        self.assertEqual(self.order_obj.payment_status, PaymentStatus.PROOF_SUBMITTED)
        payment_services.set_status(payment, PaymentStatus.VERIFIED, self.staff)
        self.order_obj.refresh_from_db(); payment.refresh_from_db()
        self.assertEqual(self.order_obj.payment_status, PaymentStatus.VERIFIED)
        self.assertEqual(payment.verified_by, self.staff)

    def test_reject_needs_reason_then_customer_can_resubmit(self):
        payment = payment_services.submit_proof(self.order_obj, "123456789012")
        with self.assertRaises(PaymentError):
            payment_services.set_status(payment, PaymentStatus.REJECTED, self.staff, "")
        payment_services.set_status(payment, PaymentStatus.REJECTED, self.staff, "Amount does not match")
        second = payment_services.submit_proof(self.order_obj, "210987654321")
        self.assertEqual(second.status, PaymentStatus.PROOF_SUBMITTED)
        self.assertEqual(self.order_obj.payments.count(), 2)

    def test_same_utr_cannot_be_reused(self):
        payment_services.submit_proof(self.order_obj, "123456789012")
        other = self.order(method=PaymentMethod.UPI)
        with self.assertRaises(PaymentError):
            payment_services.submit_proof(other, "123456789012")

    def test_cod_collection_rules(self):
        cod = self.order()
        with self.assertRaises(PaymentError):
            payment_services.mark_cod_collected(cod, self.staff)  # not dispatched yet
        for s in [OrderStatus.CONFIRMED, OrderStatus.PACKED, OrderStatus.DISPATCHED]:
            services.change_status(cod, s, self.staff)
        payment_services.mark_cod_collected(cod, self.staff)
        cod.refresh_from_db()
        self.assertEqual(cod.payment_status, PaymentStatus.COLLECTED)


class InvoiceTests(Base):
    def confirmed(self, **kw):
        order = self.order(**kw)
        return services.change_status(order, OrderStatus.CONFIRMED, self.staff)

    def test_financial_year(self):
        from datetime import date
        self.assertEqual(financial_year(date(2026, 3, 31)), "2025-26")
        self.assertEqual(financial_year(date(2026, 4, 1)), "2026-27")
        self.assertEqual(financial_year(date(2026, 12, 31)), "2026-27")

    def test_cannot_invoice_unconfirmed_order(self):
        with self.assertRaises(InvoiceError):
            invoice_services.issue_invoice(self.order())

    def test_numbers_are_sequential_unique_and_idempotent(self):
        a, b = self.confirmed(), self.confirmed()
        inv_a = invoice_services.issue_invoice(a)
        inv_b = invoice_services.issue_invoice(b)
        self.assertRegex(inv_a.invoice_no, r"^GMM/\d{4}-\d{2}/0001$")
        self.assertTrue(inv_b.invoice_no.endswith("/0002"))
        self.assertLessEqual(len(inv_b.invoice_no), 16)
        self.assertEqual(invoice_services.issue_invoice(a).pk, inv_a.pk)

    def test_intra_state_splits_cgst_sgst(self):
        order = self.confirmed()
        inv = invoice_services.issue_invoice(order)
        self.assertFalse(inv.is_interstate)
        self.assertEqual(inv.cgst + inv.sgst, order.tax_total)
        self.assertEqual(inv.igst, Decimal("0.00"))

    def test_inter_state_uses_igst(self):
        self.address.state = "Bihar"; self.address.save()
        order = self.confirmed()
        inv = invoice_services.issue_invoice(order)
        self.assertTrue(inv.is_interstate)
        self.assertEqual(inv.igst, order.tax_total)
        self.assertEqual(inv.cgst + inv.sgst, Decimal("0.00"))
