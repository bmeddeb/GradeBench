"""
ASGI config for gradebench project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from django.conf import settings
from core.db import database

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gradebench.settings')

# Get the ASGI application
application = get_asgi_application()

# Add database connection lifecycle hooks
async def app_startup():
    await database.connect()

async def app_shutdown():
    await database.disconnect()

# Attach lifecycle hooks to the application
application.on_startup = [app_startup]
application.on_shutdown = [app_shutdown]
