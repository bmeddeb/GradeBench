#!/usr/bin/env python
from lms.canvas.client import Client
from lms.canvas.models import CanvasIntegration, CanvasCourse
import os
import sys
import asyncio
import logging
from django.core.wsgi import get_wsgi_application

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gradebench.settings')
application = get_wsgi_application()

# Import models after Django setup

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_create_group_category():
    try:
        # Get the first Canvas integration
        integration = CanvasIntegration.objects.first()
        if not integration:
            logger.error("No Canvas integration found.")
            return

        # Create client
        client = Client(integration)

        # Use the course ID from your URL
        course_id = 11913456  # The course ID from your URL

        # Check if the course exists
        try:
            course = CanvasCourse.objects.get(canvas_id=course_id)
            logger.info(f"Found course: {course.name}")
        except CanvasCourse.DoesNotExist:
            logger.error(
                f"Course with ID {course_id} does not exist in the database")
            return

        # Create a test group category
        name = "Test Group Category"
        logger.info(
            f"Creating group category '{name}' in course {course_id}...")

        # Create the group category
        try:
            result = await client.create_group_category(
                course_id=course_id,
                name=name,
                self_signup="enabled",
                group_limit=4
            )

            logger.info(f"API Response: {result}")

            # Check if the category was created in Canvas
            if 'id' in result:
                logger.info(
                    f"Group category created in Canvas with ID: {result['id']}")

                # Explicitly save to our database
                category = await client._save_group_category(result, course)
                logger.info(
                    f"Group category saved to local database with ID: {category.id}")

                # Verify it exists in the database
                from django.db import connection
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT id, name FROM lms_canvas_canvasgroupcategory WHERE canvas_id = %s", [result['id']])
                    row = cursor.fetchone()
                    if row:
                        logger.info(
                            f"Verified in database: ID={row[0]}, Name={row[1]}")
                    else:
                        logger.error(
                            "Could not find the group category in the database after saving")
            else:
                logger.error(
                    "Failed to create group category in Canvas - missing ID in response")

        except Exception as e:
            logger.error(f"Error creating group category: {e}")
            import traceback
            logger.error(traceback.format_exc())
    except Exception as e:
        logger.error(f"Test error: {e}")
        import traceback
        logger.error(traceback.format_exc())

# Run the test
if __name__ == "__main__":
    asyncio.run(test_create_group_category())
