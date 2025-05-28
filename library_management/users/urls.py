from django.urls import path

from library_management.users.api.views import LogoutView
from library_management.users.api.views import PasswordResetConfirmValidateView
from library_management.users.api.views import PasswordResetConfirmView
from library_management.users.api.views import PasswordResetView

app_name = "auth"

urlpatterns = [
    path("logout/", LogoutView.as_view(), name="logout"),
    path("password-reset/", PasswordResetView.as_view(), name="password-reset"),
    path(
        "password-reset/confirm/",
        PasswordResetConfirmView.as_view(),
        name="password-reset-confirm",
    ),
    path(
        "password-reset/validate/",
        PasswordResetConfirmValidateView.as_view(),
        name="password-reset-validate",
    ),
]
