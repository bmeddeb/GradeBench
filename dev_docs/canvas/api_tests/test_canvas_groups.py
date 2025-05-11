#!/usr/bin/env python

import logging
from lms.canvas.models import CanvasIntegration
from lms.canvas.client import Client
import os
import django
import asyncio
import sys

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gradebench.settings")
django.setup()


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_api():
    try:
        # Get the first Canvas integration
        integration = CanvasIntegration.objects.first()
        if not integration:
            logger.error("No Canvas integration found.")
            return

        client = Client(integration)
        course_id = 11921869

        print(f'Testing group categories for course {course_id}...')
        categories = await client.get_group_categories(course_id)
        print(f'Found {len(categories)} group categories')

        for cat in categories:
            print(f'Category: {cat.get("name")} (ID: {cat.get("id")})')
            groups = await client.get_groups(cat['id'])
            print(f'  - Found {len(groups)} groups in this category')

            for group in groups:
                print(
                    f'    - Group: {group.get("name")} (ID: {group.get("id")})')
                members = await client.get_group_members(group['id'])
                print(f'      - Members: {len(members)}')
                if members:
                    print(
                        f'      - First member: {members[0].get("name")} (ID: {members[0].get("id")})')

        print("Test completed successfully.")
    except Exception as e:
        logger.error(f"Error testing Canvas API: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(test_api())
