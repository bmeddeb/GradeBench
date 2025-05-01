from django.apps import AppConfig


class IntegrationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'integrations'
    verbose_name = 'Integrations'

    def ready(self):
        """
        Initialize signals or other configurations when the app is ready.
        """
        # Import signals here to avoid circular imports
        # import integrations.signals
        pass
