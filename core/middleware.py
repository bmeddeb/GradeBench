from django.shortcuts import redirect
from django.contrib import messages
from social_core.exceptions import AuthAlreadyAssociated, AuthCanceled
import logging

logger = logging.getLogger(__name__)

class SocialAuthExceptionMiddleware:
    """Middleware to handle social auth exceptions."""
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        return self.get_response(request)
        
    def process_exception(self, request, exception):
        if isinstance(exception, AuthAlreadyAssociated):
            # This GitHub account is already connected to another user
            logger.warning(f"Auth already associated exception: {str(exception)}")
            messages.error(request, "This GitHub account is already connected to another user. Please use a different GitHub account or contact support.")
            return redirect('profile')
            
        elif isinstance(exception, AuthCanceled):
            # User canceled the authentication process
            logger.info("User canceled authentication")
            messages.info(request, "Authentication was canceled.")
            return redirect('profile')
            
        return None 