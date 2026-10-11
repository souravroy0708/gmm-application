from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings

from .models import Address, User


def make_user(phone="9876543210", name="Test Farmer"):
    return User.objects.create_user(phone, name=name, password="s3cret-pass-123")


def make_address(user, **kw):
    data = dict(full_name=user.name, phone=user.phone, line1="Main road", village_town="Arambagh",
                district="Hooghly", state="West Bengal", pincode="712601")
    data.update(kw)
    return Address.objects.create(user=user, **data)


class PhoneAndUserTests(TestCase):
    def test_phone_is_normalized_to_e164(self):
        for raw in ["9876543210", "+91 98765 43210", "09876543210", "91-9876543210"]:
            User.objects.all().delete()
            self.assertEqual(make_user(raw).phone, "+919876543210")

    def test_same_number_typed_differently_is_a_duplicate(self):
        make_user("9876543210")
        dup = User(phone="+91 98765-43210", name="Other")
        with self.assertRaises(ValidationError):
            dup.full_clean(exclude=["password"])

    def test_invalid_numbers_rejected(self):
        for bad in ["12345", "5876543210", "abcdefghij"]:
            with self.assertRaises(ValidationError):
                User(phone=bad, name="x").full_clean(exclude=["password"])

    def test_lookup_by_any_format(self):
        user = make_user("9876543210")
        self.assertEqual(User.objects.get(phone="098765 43210"), user)


class AddressTests(TestCase):
    def setUp(self):
        self.user = make_user()

    def test_first_address_becomes_default(self):
        self.assertTrue(make_address(self.user).is_default)

    def test_new_default_replaces_old_default(self):
        a1 = make_address(self.user)
        a2 = make_address(self.user, is_default=True)
        a1.refresh_from_db()
        self.assertFalse(a1.is_default)
        self.assertTrue(a2.is_default)

    @override_settings(MAX_ADDRESSES_PER_USER=2)
    def test_address_limit(self):
        make_address(self.user)
        make_address(self.user)
        with self.assertRaises(ValidationError):
            Address(user=self.user, full_name="x", phone=self.user.phone, line1="y",
                    village_town="z", district="d", pincode="712601").full_clean()

    def test_pincode_validation(self):
        with self.assertRaises(ValidationError):
            Address(user=self.user, full_name="x", phone=self.user.phone, line1="y",
                    village_town="z", district="d", pincode="01234").full_clean()
