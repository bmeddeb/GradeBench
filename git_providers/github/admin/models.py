from django.db import models
from git_providers.github.models import Repository


class GitHub(Repository):
    """
    Proxy model to represent GitHub in the admin panel.
    This is a proxy of Repository to avoid database errors.
    """

    class Meta:
        verbose_name = "GitHub"
        verbose_name_plural = "GitHub"
        app_label = "git_providers"
        proxy = True  # Make this a proxy model of Repository

    def __str__(self):
        return "GitHub"
