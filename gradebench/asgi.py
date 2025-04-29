"""
ASGI config for gradebench project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from starlette.staticfiles import StaticFiles
from starlette.applications import Starlette
from core.db import database

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gradebench.settings')

django_app = get_asgi_application()

# Create a Starlette app to serve static files and mount Django
app = Starlette()

# Mount static files at /static
app.mount('/static', StaticFiles(directory=os.path.join(
    os.path.dirname(__file__), '..', 'static')), name='static')

# Mount Django at root
app.mount('/', django_app)

# Add database connection lifecycle hooks


@app.on_event("startup")
async def app_startup():
    await database.connect()


@app.on_event("shutdown")
async def app_shutdown():
    await database.disconnect()

application = app
