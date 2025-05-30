from django.apps import AppConfig


class LibrariesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "library_management.libraries"

    def ready(self):
        import library_management.libraries.signals  # noqa: F401
