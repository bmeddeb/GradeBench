"""
Testing group category creation

Run with:
python manage.py shell -c "exec(open('django_shell_test.py').read())"
"""

import asyncio
from asgiref.sync import sync_to_async
from lms.canvas.models import CanvasIntegration, CanvasCourse, CanvasGroupCategory
from lms.canvas.client import Client

# Define an async function to handle the group category creation


async def create_test_group_category():
    # Get the integration
    integration = await sync_to_async(CanvasIntegration.objects.first)()
    if not integration:
        print("No Canvas integration found.")
        return

    print(f"Using integration: {integration}")

    # Create client
    client = Client(integration)

    # Use the course ID
    course_id = 11913456  # Replace with the course ID from your URL

    # Check if the course exists
    try:
        course = await sync_to_async(CanvasCourse.objects.get)(canvas_id=course_id)
        print(f"Found course: {course.name}")
    except CanvasCourse.DoesNotExist:
        print(f"Course with ID {course_id} does not exist in the database")
        return

    # Create a test group category
    name = "TestGroup-" + \
        asyncio.current_task().get_name()[-4:]  # Add uniqueness
    print(f"Creating group category '{name}' in course {course_id}...")

    # Create the group category
    try:
        # Make the API call to create the group category
        result = await client.create_group_category(
            course_id=course_id,
            name=name,
            self_signup="enabled",
            group_limit=4
        )

        print(f"API Response: {result}")

        # Check if the category was created in Canvas
        if 'id' in result:
            print(f"Group category created in Canvas with ID: {result['id']}")

            # Explicitly save to our database
            category = await client._save_group_category(result, course)
            print(
                f"Group category saved to local database with ID: {category.id}")

            # List all categories for verification
            categories = await sync_to_async(list)(CanvasGroupCategory.objects.filter(course=course))
            print(f"All categories for this course ({len(categories)}):")
            for cat in categories:
                print(
                    f" - {cat.name} (Canvas ID: {cat.canvas_id}, DB ID: {cat.id})")

        else:
            print("Failed to create group category in Canvas - missing ID in response")

    except Exception as e:
        print(f"Error creating group category: {e}")
        import traceback
        print(traceback.format_exc())

# Run the async function
asyncio.run(create_test_group_category())
print("Test completed")
