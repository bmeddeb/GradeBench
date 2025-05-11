import asyncio
from lms.canvas.models import CanvasIntegration, CanvasCourse, CanvasGroupCategory
from lms.canvas.client import Client

# This script is meant to be run with: python manage.py shell < test_django_shell.py


async def test_group_category():
    # Get the integration
    integration = CanvasIntegration.objects.first()
    print(f"Using integration: {integration}")

    # Create client
    client = Client(integration)

    # Use the course ID
    course_id = 11913456  # Replace with the course ID from your URL

    # Check if the course exists
    try:
        course = CanvasCourse.objects.get(canvas_id=course_id)
        print(f"Found course: {course.name}")
    except CanvasCourse.DoesNotExist:
        print(f"Course with ID {course_id} does not exist in the database")
        return

    # Create a test group category
    name = "Test Group Category"
    print(f"Creating group category '{name}' in course {course_id}...")

    # Create the group category
    try:
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

            # List all categories
            all_categories = list(CanvasGroupCategory.objects.filter(
                course=course).values('id', 'name', 'canvas_id'))
            print(f"All categories for this course: {all_categories}")

        else:
            print("Failed to create group category in Canvas - missing ID in response")

    except Exception as e:
        print(f"Error creating group category: {e}")
        import traceback
        print(traceback.format_exc())

# Run the test
asyncio.run(test_group_category())
print("Test completed")
