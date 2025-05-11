from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
    verbose_name = "Core"

    def ready(self):
        """
        Initialize signals or other configurations when the app is ready.
        """
        # Import signals here to avoid circular imports
        # import core.signals
        pass
