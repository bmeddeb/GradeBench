# lms/canvas/management/commands/sync_calendar.py

import os
import requests
from django.core.management.base import BaseCommand
from django.utils import timezone
from dotenv import load_dotenv

from lms.canvas.models import CanvasCourse, CalendarEvent


class Command(BaseCommand):
    help = "Fetch Canvas calendar events for a course and upsert into CalendarEvent"

    def add_arguments(self, parser):
        parser.add_argument("course_id", type=int, help="Canvas course ID to sync")

    def handle(self, *args, **options):
        load_dotenv()
        API_URL = os.getenv("CANVAS_API_URL")
        API_KEY = os.getenv("CANVAS_API_TOKEN")
        course_id = options["course_id"]

        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        }
        params = {"context_codes[]": f"course_{course_id}", "per_page": 100}

        resp = requests.get(
            f"{API_URL}/api/v1/calendar_events", headers=headers, params=params
        )
        resp.raise_for_status()
        events = resp.json()

        course = CanvasCourse.objects.get(course_id=course_id)

        for ev in events:
            obj, created = CalendarEvent.objects.update_or_create(
                event_id=ev["id"],
                defaults={
                    "course": course,
                    "title": ev["title"],
                    "description": ev.get("description", ""),
                    "start_at": ev["start_at"],
                    "end_at": ev.get("end_at"),
                    "all_day": ev.get("all_day", False),
                    "html_url": ev.get("html_url", ""),
                    "created_at_canvas": ev["created_at"],
                    "updated_at_canvas": ev["updated_at"],
                    "synced_at": timezone.now(),
                },
            )
            action = "Created" if created else "Updated"
            self.stdout.write(f"{action} event {obj.title} ({obj.event_id})")
