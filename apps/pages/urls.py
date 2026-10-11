from django.urls import path
from django.views.generic import TemplateView

app_name = "pages"

urlpatterns = [
    path("contact/", TemplateView.as_view(template_name="pages/contact.html"), name="contact"),
    path("leadership/", TemplateView.as_view(template_name="pages/leadership.html"), name="leadership"),
    path("vision-mission/", TemplateView.as_view(template_name="pages/vision_mission.html"), name="vision_mission"),
]
