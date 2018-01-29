from django.urls import path
from . import views

urlpatterns = [
    path("signup/", views.signup, name="signup"),
    path("signin/", views.signin, name="signin"),
    path("two_or_four/", views.signin, name="two_or_four"),
    path("logout/", views.logout, name="logout"),
    path("play_and_status/", views.play_and_status, name="play_and_status"),
]
