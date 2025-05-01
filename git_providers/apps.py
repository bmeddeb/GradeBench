from django.apps import AppConfig


class GitProvidersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'git_providers'
    verbose_name = 'Git Providers'

    def ready(self):
        """
        Initialize signals or other configurations when the app is ready.
        """
        # Import signals here to avoid circular imports
        # import git_providers.signals
        pass
