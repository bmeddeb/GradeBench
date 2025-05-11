from django.db import models
from project_mgmt.taiga.models import Project


class Taiga(Project):
    """
    Proxy model to represent Taiga in the admin panel.
    This is a proxy of Project to avoid database errors.
    """

    class Meta:
        verbose_name = "Taiga"
        verbose_name_plural = "Taiga"
        app_label = "project_mgmt"
        proxy = True  # Make this a proxy model of Project

    def __str__(self):
        return "Taiga"
