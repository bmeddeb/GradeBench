import asyncio
import logging
from django.core.management.base import BaseCommand
from lms.canvas.models import CanvasIntegration, CanvasCourse, CanvasGroupCategory
from lms.canvas.client import Client
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Test creating a group category in Canvas'

    def add_arguments(self, parser):
        parser.add_argument('course_id', type=int, help='Canvas course ID')
        parser.add_argument('name', type=str, help='Group category name')

    def handle(self, *args, **options):
        course_id = options['course_id']
        name = options['name']

        self.stdout.write(
            f"Testing group category creation for course {course_id} with name '{name}'")

        # Run the async function using the event loop
        asyncio.run(self.create_group_category(course_id, name))

    async def create_group_category(self, course_id, name):
        # Get the integration
        integration = await sync_to_async(CanvasIntegration.objects.first)()
        if not integration:
            self.stdout.write(self.style.ERROR("No Canvas integration found."))
            return

        self.stdout.write(f"Using integration: {integration}")

        # Create client
        client = Client(integration)

        # Check if the course exists
        try:
            course = await sync_to_async(CanvasCourse.objects.get)(canvas_id=course_id)
            self.stdout.write(f"Found course: {course.name}")
        except CanvasCourse.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                f"Course with ID {course_id} does not exist in the database"))
            return

        # Create the group category
        try:
            self.stdout.write(
                f"Creating group category '{name}' in course {course_id}...")

            result = await client.create_group_category(
                course_id=course_id,
                name=name,
                self_signup="enabled",
                group_limit=4
            )

            self.stdout.write(f"API Response: {result}")

            # Check if the category was created in Canvas
            if 'id' in result:
                self.stdout.write(self.style.SUCCESS(
                    f"Group category created in Canvas with ID: {result['id']}"
                ))

                # Explicitly save to our database
                category = await client._save_group_category(result, course)
                self.stdout.write(self.style.SUCCESS(
                    f"Group category saved to local database with ID: {category.id}"
                ))

                # Verify it exists in the database
                exists = await sync_to_async(CanvasGroupCategory.objects.filter(
                    canvas_id=result['id']).exists)()
                if exists:
                    self.stdout.write(self.style.SUCCESS(
                        f"Verified: Group category exists in the database with Canvas ID {result['id']}"
                    ))
                else:
                    self.stdout.write(self.style.ERROR(
                        "Could not find the group category in the database after saving"
                    ))
            else:
                self.stdout.write(self.style.ERROR(
                    "Failed to create group category in Canvas - missing ID in response"
                ))

        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f"Error creating group category: {e}"))
            import traceback
            self.stdout.write(self.style.ERROR(traceback.format_exc()))
