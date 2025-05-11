from django.db import models
from lms.canvas.models import CanvasCourse


class Canvas(CanvasCourse):
    """
    Proxy model to represent Canvas in the admin panel.
    This is a proxy of CanvasCourse to avoid database errors.
    """

    class Meta:
        verbose_name = "Canvas"
        verbose_name_plural = "Canvas"
        app_label = "lms"
        proxy = True  # Make this a proxy model of CanvasCourse

    def __str__(self):
        return "Canvas"
