#!/usr/bin/env python
"""
Command to sync Canvas groups, group categories, and memberships.
This command ensures all group data is properly synced by
using the updated API client with correct field inclusion.
"""

import asyncio
import logging
from django.core.management.base import BaseCommand
from django.db import close_old_connections
from asgiref.sync import sync_to_async

from lms.canvas.client import Client
from lms.canvas.models import CanvasIntegration, CanvasCourse
from lms.canvas.syncer import CanvasSyncer

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        "Syncs Canvas groups, categories, and memberships for all or specific courses"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--course-id",
            type=int,
            help="Canvas course ID to sync groups for (default: sync all courses)",
            required=False,
        )
        parser.add_argument("--debug", action="store_true", help="Enable debug logging")
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force resync even if groups already exist",
        )

    def handle(self, *args, **options):
        if options["debug"]:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.INFO)

        course_id = options.get("course_id")
        force = options.get("force", False)

        self.stdout.write(self.style.SUCCESS(f"Starting Canvas group sync..."))
        asyncio.run(self.sync_groups(course_id, force))
        self.stdout.write(self.style.SUCCESS(f"Canvas group sync completed."))

    async def sync_groups(self, course_id=None, force=False):
        """Main entry point for syncing groups"""
        try:
            # Get the first Canvas integration
            integration = await sync_to_async(CanvasIntegration.objects.first)()
            if not integration:
                self.stdout.write(self.style.ERROR("No Canvas integration found."))
                return

            client = Client(integration)
            syncer = CanvasSyncer(client)

            if course_id:
                # Sync a specific course
                try:
                    course = await sync_to_async(CanvasCourse.objects.get)(
                        canvas_id=course_id
                    )
                    self.stdout.write(
                        f"Syncing groups for course {course.name} (ID: {course.canvas_id})..."
                    )
                    await self.sync_groups_for_course(syncer, course, force)
                except CanvasCourse.DoesNotExist:
                    self.stdout.write(
                        self.style.ERROR(
                            f"Course with Canvas ID {course_id} not found."
                        )
                    )
            else:
                # Sync all courses
                courses = await sync_to_async(list)(CanvasCourse.objects.all())
                self.stdout.write(f"Found {len(courses)} courses to sync...")

                for course in courses:
                    self.stdout.write(
                        f"Syncing groups for course {course.name} (ID: {course.canvas_id})..."
                    )
                    await self.sync_groups_for_course(syncer, course, force)

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error syncing Canvas groups: {e}"))
            import traceback

            self.stdout.write(self.style.ERROR(traceback.format_exc()))
        finally:
            # Clean up DB connections
            await sync_to_async(close_old_connections)()

    async def sync_groups_for_course(self, syncer, course, force=False):
        """Sync groups for a single course"""
        try:
            # First, get the group categories via API
            self.stdout.write(f"  Fetching group categories...")
            category_ids = await syncer.sync_canvas_groups(course)
            self.stdout.write(f"  Found {len(category_ids)} group IDs")

            # Then sync memberships
            self.stdout.write(f"  Syncing group memberships...")
            await syncer.sync_group_memberships(course)

            # Summarize results
            self.stdout.write(self.style.SUCCESS(f"  Sync completed for {course.name}"))
            return True
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"  Error syncing course {course.name}: {e}")
            )
            return False
