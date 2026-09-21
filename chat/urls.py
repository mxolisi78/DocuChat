from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("upload/", views.upload, name="upload"),
    path("ask/", views.ask_view, name="ask"),
    path("reset/", views.reset, name="reset"),
]