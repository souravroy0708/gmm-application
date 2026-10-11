from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import gettext_lazy as _

from apps.accounts.models import Address, User
from apps.core.constants import PaymentMethod
from apps.core.fields import normalize_phone
from apps.core.models import SiteSetting


class LoginForm(AuthenticationForm):
    username = forms.CharField(label=_("Mobile number"), widget=forms.TextInput(
        attrs={"type": "tel", "inputmode": "numeric", "autofocus": True, "placeholder": _("10-digit mobile number")}))
    password = forms.CharField(label=_("Password"), widget=forms.PasswordInput)

    def clean_username(self):
        return normalize_phone(self.cleaned_data["username"])


class RegisterForm(forms.ModelForm):
    password = forms.CharField(label=_("Password"), widget=forms.PasswordInput, help_text=_("At least 8 characters."))

    class Meta:
        model = User
        fields = ["name", "phone"]
        labels = {"name": _("Your name"), "phone": _("Mobile number")}
        widgets = {"phone": forms.TextInput(attrs={"type": "tel", "inputmode": "numeric"})}

    def clean_password(self):
        pw = self.cleaned_data["password"]
        password_validation.validate_password(pw)
        return pw

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ["full_name", "phone", "line1", "village_town", "post_office",
                  "district", "pincode", "landmark", "is_default"]
        labels = {"full_name": _("Name"), "phone": _("Mobile number"), "line1": _("House / street"),
                  "village_town": _("Village / town"), "post_office": _("Post office"), "district": _("District"),
                  "pincode": _("PIN code"), "landmark": _("Landmark"), "is_default": _("Use as my main address")}
        widgets = {"phone": forms.TextInput(attrs={"type": "tel", "inputmode": "numeric"}),
                   "pincode": forms.TextInput(attrs={"inputmode": "numeric", "maxlength": 6})}

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            self.instance.user = user  # needed for the "max addresses" check in Address.clean()


class CheckoutForm(forms.Form):
    address = forms.ModelChoiceField(queryset=Address.objects.none(), widget=forms.RadioSelect, empty_label=None)
    payment_method = forms.ChoiceField(widget=forms.RadioSelect)
    note = forms.CharField(required=False, label=_("Note (optional)"), max_length=300,
                           widget=forms.Textarea(attrs={"rows": 2}))

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["address"].queryset = user.addresses.all()
        cfg = SiteSetting.load()
        self.fields["payment_method"].choices = [
            (v, l) for v, l in PaymentMethod.choices if v != PaymentMethod.COD or cfg.cod_enabled
        ]


class ProofForm(forms.Form):
    reference = forms.CharField(label=_("Payment reference number (UTR)"), max_length=30)
    proof_image = forms.ImageField(required=False, label=_("Screenshot (optional)"))
