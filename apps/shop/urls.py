from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .forms import LoginForm

app_name = "shop"

urlpatterns = [
    path("", views.products, name="products"),
    # account
    path("login/", auth_views.LoginView.as_view(authentication_form=LoginForm), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("register/", views.register, name="register"),
    # cart & checkout
    path("cart/", views.cart_view, name="cart"),
    path("cart/add/", views.cart_add, name="cart_add"),
    path("cart/update/", views.cart_update, name="cart_update"),
    path("checkout/", views.checkout, name="checkout"),
    # orders
    path("orders/", views.order_list, name="orders"),
    path("orders/<str:order_no>/", views.order_detail, name="order_detail"),
    path("orders/<str:order_no>/cancel/", views.order_cancel, name="order_cancel"),
    path("orders/<str:order_no>/pay/", views.order_pay, name="order_pay"),
    path("orders/<str:order_no>/invoice/", views.invoice, name="invoice"),
    # addresses
    path("addresses/", views.address_list, name="addresses"),
    path("addresses/new/", views.address_form, name="address_new"),
    path("addresses/<int:pk>/edit/", views.address_form, name="address_edit"),
    path("addresses/<int:pk>/delete/", views.address_delete, name="address_delete"),
    path("addresses/<int:pk>/default/", views.address_default, name="address_default"),
]
