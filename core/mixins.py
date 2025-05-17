"""
Core mixins for timestamp and sync tracking functionality.
"""
from django.db import models


class TimestampedModel(models.Model):
    """
    An abstract base class model that provides self-updating
    'created_at' and 'updated_at' fields.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SyncableModel(TimestampedModel):
    """
    An abstract base class model that extends TimestampedModel
    with sync tracking capability.
    """
    last_synced_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        abstract = True