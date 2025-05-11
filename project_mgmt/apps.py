from django.apps import AppConfig


class ProjectMgmtConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "project_mgmt"
    verbose_name = "Project Management"

    def ready(self):
        """
        Initialize signals or other configurations when the app is ready.
        """
        # Import signals here to avoid circular imports
        # import project_mgmt.signals
        pass
