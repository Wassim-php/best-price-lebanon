from django.urls import path

from .views import (
    change_password,
    login_user,
    logout_user,
    register_user,
    update_location,
)

urlpatterns = [
    path("register", register_user),
    path("login", login_user),
    path("logout", logout_user),
    path("location", update_location),
    path("password", change_password),
]
