from django import template
from django.utils import timezone
import pytz

register = template.Library()


@register.filter
def user_timezone(value, user):
    user_tz = pytz.timezone(user.profile.timezone)
    return timezone.localtime(value, user_tz)
