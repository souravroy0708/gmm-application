from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from unfold.admin import ModelAdmin, TabularInline
from unfold.forms import AdminPasswordChangeForm

from .forms import UserChangeForm, UserCreationForm
from .models import Address, User


class AddressInline(TabularInline):
    model = Address
    extra = 0
    fields = ("full_name", "phone", "village_town", "district", "pincode", "is_default")
    show_change_link = True


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm

    list_display = ("name", "phone", "email", "is_staff", "is_active", "date_joined")
    list_filter = ("is_staff", "is_active", "language")
    search_fields = ("name", "phone", "email")
    ordering = ("-date_joined",)
    inlines = [AddressInline]

    fieldsets = (
        (None, {"fields": ("phone", "password")}),
        ("Personal info", {"fields": ("name", "email", "language")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("phone", "name", "usable_password", "password1", "password2")}),
    )


@admin.register(Address)
class AddressAdmin(ModelAdmin):
    list_display = ("full_name", "phone", "village_town", "district", "pincode", "user", "is_default")
    list_filter = ("district", "state", "is_default")
    search_fields = ("full_name", "phone", "pincode", "village_town", "user__phone", "user__name")
    autocomplete_fields = ("user",)
