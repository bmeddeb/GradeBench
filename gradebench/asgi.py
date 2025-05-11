"""
ASGI config for gradebench project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

from core.db import database, get_db, close_db
from django.conf import settings
import os
from django.core.asgi import get_asgi_application
from starlette.staticfiles import StaticFiles
from starlette.applications import Starlette

# Set Django settings module before any Django imports
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gradebench.settings")

# Import Django app first to ensure settings are configured
django_app = get_asgi_application()

# Now it's safe to import the database

# Create a Starlette app to serve static files and mount Django
app = Starlette()

# Mount static files using Django's STATIC_ROOT
if os.path.exists(settings.STATIC_ROOT):
    app.mount(
        settings.STATIC_URL, StaticFiles(directory=settings.STATIC_ROOT), name="static"
    )

# Mount static files from STATICFILES_DIRS
for static_dir in settings.STATICFILES_DIRS:
    if os.path.exists(static_dir):
        app.mount(
            settings.STATIC_URL,
            StaticFiles(directory=static_dir),
            name=f"static_{static_dir}",
        )

# Mount Django at root
app.mount("/", django_app)

# Add database connection lifecycle hooks


@app.on_event("startup")
async def app_startup():
    await get_db()


@app.on_event("shutdown")
async def app_shutdown():
    await close_db()


application = app
