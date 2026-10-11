from django.urls import path

from . import views

app_name = "thoughts"

urlpatterns = [
    path("thoughts/", views.create, name="create"),
]
