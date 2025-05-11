#!/usr/bin/env python
from lms.canvas.client import Client
from lms.canvas.models import CanvasIntegration
import os
import sys
import django
import asyncio
import logging

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gradebench.settings")
django.setup()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Now import Django models


async def test_canvas_api():
    """Test Canvas API for fetching group categories and groups"""
    try:
        # Get the first Canvas integration
        integration = CanvasIntegration.objects.first()
        if not integration:
            logger.error(
                "No Canvas integration found. Please set up Canvas integration first.")
            return

        # Create API client
        client = Client(integration)

        # Course ID to test with (replace with your actual course ID)
        course_id = 11921869  # Use the course ID from your error message

        logger.info(f"Testing Canvas API for course {course_id}")

        # Test fetching group categories
        logger.info("Fetching group categories...")
        categories = await client.get_group_categories(course_id)
        logger.info(f"Found {len(categories)} group categories")

        for category in categories:
            logger.info(
                f"Category: {category.get('name')} (ID: {category.get('id')})")

            # Test fetching groups in this category
            logger.info(
                f"Fetching groups for category {category.get('id')}...")
            groups = await client.get_groups(category.get('id'))
            logger.info(f"Found {len(groups)} groups in category")

            for group in groups:
                logger.info(
                    f"Group: {group.get('name')} (ID: {group.get('id')})")

                # Test fetching group members
                logger.info(f"Fetching members for group {group.get('id')}...")
                members = await client.get_group_members(group.get('id'))
                logger.info(f"Found {len(members)} members in group")

                for member in members:
                    logger.info(
                        f"Member: {member.get('name')} (ID: {member.get('id')})")

        logger.info("Canvas API test completed successfully!")

    except Exception as e:
        logger.error(f"Error in test_canvas_api: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(test_canvas_api())
