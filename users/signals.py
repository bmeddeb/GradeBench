from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User, Group
from .models import BaseUserProfile


# Create user profile when a new user is created
@receiver(post_save, sender=User)
def create_base_user_profile(sender, instance, created, **kwargs):
    """Create a base user profile when a new user is created"""
    if created:
        BaseUserProfile.objects.get_or_create(user=instance)


# Save the user profile when the user is saved
@receiver(post_save, sender=User)
def save_base_user_profile(sender, instance, **kwargs):
    """Save the base user profile when the user is saved"""
    if hasattr(instance, 'user_profile'):
        instance.user_profile.save()
