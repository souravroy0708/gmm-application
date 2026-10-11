from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models, transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.fields import PhoneField, normalize_phone
from apps.core.models import TimeStampedModel


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, phone, name, password, **extra):
        if not phone:
            raise ValueError("A phone number is required.")
        user = self.model(phone=normalize_phone(phone), name=name or "", **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, phone, name="", password=None, **extra):
        extra.setdefault("is_staff", False)
        extra.setdefault("is_superuser", False)
        return self._create_user(phone, name, password, **extra)

    def create_superuser(self, phone, name="", password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        if not extra["is_staff"] or not extra["is_superuser"]:
            raise ValueError("Superuser must have is_staff=True and is_superuser=True.")
        return self._create_user(phone, name, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    """Customer or staff account. The mobile number is the login (USERNAME_FIELD)."""

    phone = PhoneField(_("mobile number"), unique=True)
    name = models.CharField(_("full name"), max_length=150)
    email = models.EmailField(_("email"), blank=True)
    language = models.CharField(
        max_length=2, choices=[("en", "English"), ("bn", "বাংলা")], default="en"
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(_("staff status"), default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = ["name"]

    class Meta:
        verbose_name = _("customer / user")
        verbose_name_plural = _("customers / users")
        ordering = ["-date_joined"]

    def __str__(self):
        return f"{self.name} ({self.phone})" if self.name else self.phone

    def get_full_name(self):
        return self.name

    def get_short_name(self):
        return self.name.split(" ")[0] if self.name else self.phone

    def save(self, *args, **kwargs):
        self.phone = normalize_phone(self.phone)
        super().save(*args, **kwargs)


pincode_validator = RegexValidator(r"^[1-9]\d{5}$", _("Enter a valid 6-digit PIN code."))


class Address(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="addresses")
    full_name = models.CharField(max_length=150)
    phone = PhoneField()
    line1 = models.CharField(_("house / street"), max_length=200)
    line2 = models.CharField(_("area / locality"), max_length=200, blank=True)
    village_town = models.CharField(_("village / town"), max_length=120)
    post_office = models.CharField(max_length=120, blank=True)
    district = models.CharField(max_length=100)
    state = models.CharField(max_length=100, default="West Bengal")
    pincode = models.CharField("PIN code", max_length=6, validators=[pincode_validator])
    landmark = models.CharField(max_length=150, blank=True)
    is_default = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "addresses"
        ordering = ["-is_default", "-updated_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user"], condition=models.Q(is_default=True), name="one_default_address_per_user"
            )
        ]

    def __str__(self):
        return f"{self.full_name}, {self.village_town} - {self.pincode}"

    def clean(self):
        super().clean()
        if self._state.adding and self.user_id:
            if Address.objects.filter(user_id=self.user_id).count() >= settings.MAX_ADDRESSES_PER_USER:
                raise ValidationError(
                    _("You can save at most %(n)d addresses."), params={"n": settings.MAX_ADDRESSES_PER_USER}
                )

    def save(self, *args, **kwargs):
        with transaction.atomic():
            others = Address.objects.filter(user_id=self.user_id).exclude(pk=self.pk)
            if self.is_default:
                others.filter(is_default=True).update(is_default=False)
            elif not others.exists():
                self.is_default = True  # the first address is always the default
            super().save(*args, **kwargs)

    def snapshot(self):
        """Frozen copy stored on an order, so later edits never change old orders."""
        return {
            "full_name": self.full_name,
            "phone": self.phone,
            "line1": self.line1,
            "line2": self.line2,
            "village_town": self.village_town,
            "post_office": self.post_office,
            "district": self.district,
            "state": self.state,
            "pincode": self.pincode,
            "landmark": self.landmark,
        }
