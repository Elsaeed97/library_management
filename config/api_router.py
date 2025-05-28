from django.urls import include
from django.urls import path

app_name = "api"

urlpatterns = [
    path("auth/", include("library_management.users.urls", namespace="auth")),
]
