from django.shortcuts import redirect
from django.contrib import messages
from social_core.exceptions import AuthAlreadyAssociated, AuthCanceled
from django.utils import timezone
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
            logger.warning(
                f"Auth already associated exception: {str(exception)}")
            messages.error(
                request,
                "This GitHub account is already connected to another user. Please use a different GitHub account or contact support.",
            )
            return redirect("profile")

        elif isinstance(exception, AuthCanceled):
            # User canceled the authentication process
            logger.info("User canceled authentication")
            messages.info(request, "Authentication was canceled.")
            return redirect("profile")

        return None


class UserTimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tzname = None
        # 1. User override (session or profile)
        if request.user.is_authenticated and hasattr(request.user, 'profile') and request.user.profile.timezone:
            tzname = request.user.profile.timezone
        # 2. Cookie (from JS)
        elif 'detected_timezone' in request.COOKIES:
            tzname = request.COOKIES['detected_timezone']
        # 3. Fallback
        else:
            tzname = 'UTC'
        timezone.activate(tzname)
        return self.get_response(request)
