from django.apps import AppConfig


class CustomSocialDjangoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'custom_social_django'
    verbose_name = 'Social Authentication'
    
    # Important: Set this to the original app
    label = 'social_django'
    
    def ready(self):
        """
        Override admin registrations
        """
        # Import the original social_django admin
        import social_django.admin
        
        # Override the admin registration by monkeypatching
        social_django.admin.admin.site.unregister = lambda model: None
