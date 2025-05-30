from django.urls import include
from django.urls import path

app_name = "api"

urlpatterns = [
    path("auth/", include("library_management.users.urls", namespace="auth")),
    path("", include("library_management.libraries.urls", namespace="libraries")),
]
