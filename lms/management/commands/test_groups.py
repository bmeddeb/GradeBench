import logging
import asyncio
from django.core.management.base import BaseCommand
from django.db import transaction
from lms.canvas.models import CanvasCourse, CanvasIntegration, CanvasEnrollment
from lms.canvas.client import Client
from core.models import Team, Student
from django.utils import timezone

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Tests group creation and student assignment functionality'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Starting group test...'))

        # Get course
        try:
            course = CanvasCourse.objects.get(canvas_id=11913456)  # Use your course ID
            self.stdout.write(f"Using course: {course.name} (ID: {course.canvas_id})")
        except CanvasCourse.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Course not found"))
            return

        # Check Canvas API for groups
        self.stdout.write("Checking Canvas API for groups...")
        try:
            # Get integration
            integration = course.integration
            if not integration:
                self.stdout.write(self.style.ERROR("No integration found for this course"))
                return

            # Create client
            client = Client(integration)

            # Run in asyncio event loop
            loop = asyncio.get_event_loop()
            categories = loop.run_until_complete(client.get_group_categories(course.canvas_id))

            self.stdout.write(f"Found {len(categories)} group categories")

            for cat in categories:
                self.stdout.write(f"Category: {cat.get('name')} (ID: {cat.get('id')})")

                groups = loop.run_until_complete(client.get_groups(cat['id']))
                self.stdout.write(f"  - Found {len(groups)} groups in this category")

                for group in groups:
                    self.stdout.write(f"    - Group: {group.get('name')} (ID: {group.get('id')})")

                    members = loop.run_until_complete(client.get_group_members(group['id']))
                    self.stdout.write(f"      - Members: {len(members)}")

                    # Try to create team from this group
                    try:
                        # Inspect the group data
                        self.stdout.write(f"      - Group data: {group}")

                        with transaction.atomic():
                            team, created = Team.objects.update_or_create(
                                canvas_group_id=int(group['id']),  # Ensure it's an integer
                                canvas_course=course,
                                defaults={
                                    'name': str(group.get('name', ''))[:100],
                                    'description': str(group.get('description', ''))[:500] if group.get('description') else '',
                                    'last_synced_at': timezone.now()
                                }
                            )
                            self.stdout.write(f"      - Created team: {team.name}, created: {created}")

                            # Assign students to team
                            student_count = 0
                            for member in members:
                                try:
                                    # Debug member data
                                    self.stdout.write(f"        - Member data: {member}")

                                    # Get enrollment for this member - use the id field which matches Canvas user ID
                                    enrollment = CanvasEnrollment.objects.get(
                                        user_id=member['id'],  # The 'id' field in member matches user_id in CanvasEnrollment
                                        course=course
                                    )

                                    # Create or get student
                                    user_name_parts = enrollment.user_name.split()
                                    first_name = user_name_parts[0] if user_name_parts else "Unknown"
                                    last_name = " ".join(user_name_parts[1:]) if len(user_name_parts) > 1 else ""

                                    student, student_created = Student.objects.update_or_create(
                                        canvas_user_id=str(enrollment.user_id),
                                        defaults={
                                            'email': enrollment.email or f"canvas-user-{enrollment.user_id}@example.com",
                                            'first_name': first_name,
                                            'last_name': last_name,
                                        }
                                    )

                                    # Link student to enrollment
                                    enrollment.student = student
                                    enrollment.save(update_fields=['student'])

                                    # Assign team to student
                                    student.team = team
                                    student.save(update_fields=['team'])
                                    student_count += 1

                                except CanvasEnrollment.DoesNotExist:
                                    self.stdout.write(self.style.WARNING(
                                        f"      - Enrollment not found for member ID {member['id']}"
                                    ))
                                except Exception as e:
                                    self.stdout.write(self.style.ERROR(
                                        f"      - Error assigning student for member ID {member['id']}: {str(e)}"
                                    ))

                            self.stdout.write(f"      - Assigned {student_count} students to team {team.name}")

                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"      - Error creating team: {str(e)}"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error checking Canvas API: {str(e)}"))
            import traceback
            traceback.print_exc()
            
        # Skip the manual test team creation since we already created teams from Canvas
        
        # Check results
        self.stdout.write(self.style.SUCCESS('Test complete. Summary:'))
        self.stdout.write(f"- Total Student records: {Student.objects.count()}")
        self.stdout.write(f"- Students with teams: {Student.objects.exclude(team=None).count()}")
        self.stdout.write(f"- Total Team records: {Team.objects.count()}")