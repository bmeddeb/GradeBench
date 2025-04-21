import os
import databases
from django.conf import settings
from functools import wraps
from asgiref.sync import sync_to_async

# Initialize database
database = databases.Database(settings.DATABASE_URL)

# Helper functions for async database operations
async def get_db():
    """Get database connection."""
    if not database.is_connected:
        await database.connect()
    return database

async def close_db():
    """Close database connection."""
    if database.is_connected:
        await database.disconnect()

def async_db_operation(f):
    """Decorator for async database operations."""
    @wraps(f)
    async def wrapper(*args, **kwargs):
        db = await get_db()
        try:
            return await f(db, *args, **kwargs)
        finally:
            # We don't close the connection after each operation to reuse it
            pass
    return wrapper

# Convert Django ORM operations to async
def django_model_to_dict(instance):
    """Convert Django model instance to dictionary."""
    return {field.name: getattr(instance, field.name) for field in instance._meta.fields}

async def async_save(model_instance):
    """Save a Django model instance asynchronously."""
    return await sync_to_async(model_instance.save)()

async def async_get(model_class, **kwargs):
    """Get a Django model instance asynchronously."""
    return await sync_to_async(model_class.objects.get)(**kwargs)

async def async_filter(model_class, **kwargs):
    """Filter Django model instances asynchronously."""
    queryset = await sync_to_async(model_class.objects.filter)(**kwargs)
    return await sync_to_async(list)(queryset) 