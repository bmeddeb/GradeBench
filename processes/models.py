from django.db import models
from django.utils.translation import gettext_lazy as _


class Process(models.Model):
    """Base model for processes in the system."""
    name = models.CharField(_('Process Name'), max_length=255)
    description = models.TextField(_('Description'), blank=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Process')
        verbose_name_plural = _('Processes')
        ordering = ['-created_at']

    def __str__(self):
        return self.name
