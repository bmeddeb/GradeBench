#!/usr/bin/env python

from asgiref.sync import sync_to_async
from lms.canvas.models import CanvasIntegration
from lms.canvas.client import Client
import django
import os
import sys
import logging
import asyncio
from django.db import close_old_connections

# Set up Django environment FIRST, before importing any models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gradebench.settings")

django.setup()

# Now import your models and other Django-dependent code

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create async versions of the ORM methods
async_get_first_integration = sync_to_async(CanvasIntegration.objects.first)


async def test_create_group_category():
    try:
        # Ensure database connections are closed before starting
        close_old_connections()

        # Get the first Canvas integration (async version)
        integration = await async_get_first_integration()
        if not integration:
            logger.error("No Canvas integration found.")
            return

        client = Client(integration)
        course_id = 11921869  # Replace with an actual test course ID

        # Test creating a group category
        name = "Test Group Set " + \
            asyncio.current_task().get_name()[-4:]  # Add uniqueness
        logger.info(
            f"Creating group category '{name}' in course {course_id}...")

        result = await client.create_group_category(
            course_id=course_id,
            name=name,
            self_signup="enabled",  # Allow self-signup
            auto_leader="first",    # First student is leader
            group_limit=4           # Max 4 students per group
        )

        logger.info(f"Group category created successfully: {result}")
        logger.info(f"Group category ID: {result.get('id')}")
        logger.info(f"Group category name: {result.get('name')}")
        logger.info(f"Self signup: {result.get('self_signup')}")
        logger.info(f"Auto leader: {result.get('auto_leader')}")
        logger.info(f"Group limit: {result.get('group_limit')}")

        print("Test completed successfully.")
    except Exception as e:
        logger.error(f"Error testing group category creation: {e}")
        raise
    finally:
        # Ensure connections are closed when done
        close_old_connections()

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_create_group_category())
