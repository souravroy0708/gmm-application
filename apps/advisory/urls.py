from django.urls import path

from . import views

app_name = "advisory"

urlpatterns = [
    path("krishi-paramarsha/", views.index, name="index"),
    path("krishi-paramarsha/<slug:slug>/", views.detail, name="detail"),
]
