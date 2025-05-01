from django.apps import AppConfig


class LMSConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'lms'
    verbose_name = 'Learning Management Systems'

    def ready(self):
        """
        Initialize signals or other configurations when the app is ready.
        """
        # Import signals here to avoid circular imports
        # import lms.signals
        pass
