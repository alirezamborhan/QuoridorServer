from django.urls import path
from . import views

urlpatterns = [
    path("signup/", views.signup, name="signup"),
    path("signin/", views.signin, name="signin"),
    path("two_or_four/", views.two_or_four, name="two_or_four"),
    path("logout/", views.logout, name="logout"),
    path("play_and_status/", views.play_and_status, name="play_and_status"),
    path("leave/", views.leave, name="leave"),
    path("scores/", views.scores, name="scores"),
    path("user_info/", views.user_info, name="user_info"),
]
