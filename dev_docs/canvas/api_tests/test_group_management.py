#!/usr/bin/env python

from lms.canvas.client import Client
from lms.canvas.models import CanvasIntegration, CanvasCourse
import django
import os
import sys
import logging
import asyncio
import random
from pprint import pprint
from datetime import datetime

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gradebench.settings")

django.setup()


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_group_management():
    try:
        # Get the first Canvas integration
        integration = CanvasIntegration.objects.first()
        if not integration:
            logger.error("No Canvas integration found.")
            return

        # Create client
        client = Client(integration)

        # Configure test parameters
        course_id = 11921869  # Replace with an actual test course ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_id = random.randint(1000, 9999)
        test_id = f"{timestamp}_{random_id}"

        print(f"\n--- Starting group management test {test_id} ---\n")

        # 1. Create a group category
        print("1. Creating a group category...")
        category_name = f"Test Category {test_id}"
        category = await client.create_group_category(
            course_id=course_id,
            name=category_name,
            self_signup="enabled",
            group_limit=4
        )
        print(
            f"Category created: {category.get('name')} (ID: {category.get('id')})")
        category_id = category.get('id')

        # 2. Create a group in the category
        print("\n2. Creating a group...")
        group_name = f"Test Group {test_id}"
        group = await client.create_group(
            category_id=category_id,
            name=group_name,
            description="Test group created by API test script"
        )
        print(f"Group created: {group.get('name')} (ID: {group.get('id')})")
        group_id = group.get('id')

        # 3. Update the group category
        print("\n3. Updating the group category...")
        updated_category = await client.update_group_category(
            category_id=category_id,
            name=f"{category_name} (Updated)",
            group_limit=5
        )
        print(
            f"Category updated: {updated_category.get('name')} (ID: {updated_category.get('id')})")

        # 4. Update the group
        print("\n4. Updating the group...")
        updated_group = await client.update_group(
            group_id=group_id,
            name=f"{group_name} (Updated)",
            description="Updated test group description"
        )
        print(
            f"Group updated: {updated_group.get('name')} (ID: {updated_group.get('id')})")

        print("\n--- Test completed successfully ---")

    except Exception as e:
        logger.error(f"Error testing group management: {e}")
        raise


if __name__ == "__main__":
    # Run the test
    asyncio.run(test_group_management())
