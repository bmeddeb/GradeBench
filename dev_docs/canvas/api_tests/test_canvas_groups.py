#!/usr/bin/env python

import os
import sys
import logging
import asyncio
from django.db import close_old_connections

# Set up Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gradebench.settings")

import django

django.setup()

from asgiref.sync import sync_to_async
from lms.canvas.models import CanvasIntegration
from lms.canvas.client import Client

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create async versions of the ORM methods
async_get_first_integration = sync_to_async(CanvasIntegration.objects.first)


async def test_api():
    try:
        # Get the first Canvas integration (async version)
        integration = await async_get_first_integration()
        if not integration:
            logger.error("No Canvas integration found.")
            return

        client = Client(integration)
        course_id = 11921869

        print(f"Testing group categories for course {course_id}...")
        categories = await client.get_group_categories(course_id)
        print(f"Found {len(categories)} group categories")

        for cat in categories:
            print(f'Category: {cat.get("name")} (ID: {cat.get("id")})')
            groups = await client.get_groups(cat["id"])
            print(f"  - Found {len(groups)} groups in this category")

            for group in groups:
                print(f'    - Group: {group.get("name")} (ID: {group.get("id")})')
                members = await client.get_group_members(group["id"])
                print(f"      - Members: {len(members)}")
                if members:
                    print(
                        f'      - First member: {members[0].get("name")} (ID: {members[0].get("id")}'
                    )

        print("Test completed successfully.")
    except Exception as e:
        logger.error(f"Error testing Canvas API: {e}")
        raise
    finally:
        await sync_to_async(close_old_connections)()


if __name__ == "__main__":
    asyncio.run(test_api())
