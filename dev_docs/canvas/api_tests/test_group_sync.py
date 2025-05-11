#!/usr/bin/env python
import os
import sys
import asyncio
import logging
import django
from asgiref.sync import sync_to_async

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gradebench.settings')
django.setup()

# After Django setup, we can import models and functions
from lms.canvas.models import CanvasCourse, CanvasIntegration
from lms.canvas.client import Client
from lms.canvas.syncer import CanvasSyncer
from core.models import Team, Student
from django.utils import timezone

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_group_sync')

@sync_to_async
def get_course(canvas_id):
    try:
        return CanvasCourse.objects.get(canvas_id=canvas_id)
    except CanvasCourse.DoesNotExist:
        return None

@sync_to_async
def create_team(canvas_group_id, canvas_course, name, description):
    team, created = Team.objects.update_or_create(
        canvas_group_id=canvas_group_id,
        canvas_course=canvas_course,
        defaults={
            'name': name,
            'description': description,
            'last_synced_at': timezone.now()
        }
    )
    return team, created

@sync_to_async
def count_students():
    return Student.objects.count()

@sync_to_async
def count_students_with_teams():
    return Student.objects.exclude(team=None).count()

@sync_to_async
def count_teams():
    return Team.objects.count()

async def test_group_sync():
    # Get a course
    course = await get_course(11913456)  # Replace with your course ID
    if not course:
        logger.error(f"Course not found")
        return
    
    logger.info(f"Using course: {course.name} (ID: {course.canvas_id})")

    # Get the integration associated with this course
    integration = course.integration
    if not integration:
        logger.error("No integration associated with this course")
        return

    # Create client and syncer
    client = Client(integration)
    
    # Test fetching group categories
    logger.info(f"Fetching group categories for course {course.canvas_id}...")
    try:
        categories = await client.get_group_categories(course.canvas_id)
        logger.info(f"Found {len(categories)} group categories")
        
        # If no categories, try manually creating a test team
        if not categories:
            logger.info("No categories found, creating a test team directly")
            team, created = await create_team(
                canvas_group_id=999999,  # Test ID
                canvas_course=course,
                name="Test Team",
                description="Test team created directly"
            )
            logger.info(f"Created test team: {team.name}, created: {created}")
        
        for cat in categories:
            logger.info(f"Category: {cat.get('name')} (ID: {cat.get('id')})")
            
            # Test fetching groups for this category
            groups = await client.get_groups(cat['id'])
            logger.info(f"Found {len(groups)} groups in category {cat.get('name')}")
            
            for group in groups:
                logger.info(f"Group: {group.get('name')} (ID: {group.get('id')})")
                
                # Try to create team directly
                team, created = await create_team(
                    canvas_group_id=group['id'],
                    canvas_course=course,
                    name=group.get('name', ''),
                    description=group.get('description', '')
                )
                logger.info(f"Created team: {team.name}, created: {created}")
                
                # Test fetching members for this group
                members = await client.get_group_members(group['id'])
                logger.info(f"Found {len(members)} members in group {group.get('name')}")
    except Exception as e:
        logger.error(f"Error fetching or creating groups: {str(e)}")

    # Check summary
    student_count = await count_students()
    students_with_teams = await count_students_with_teams()
    team_count = await count_teams()
    
    logger.info(f"Summary:")
    logger.info(f"- Total Student records: {student_count}")
    logger.info(f"- Students with teams: {students_with_teams}")
    logger.info(f"- Total Team records: {team_count}")

if __name__ == "__main__":
    asyncio.run(test_group_sync())