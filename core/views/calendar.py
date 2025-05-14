from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.utils import timezone
from datetime import datetime, timedelta
from core.models import CalendarEvent
import io
from icalendar import Calendar


class CalendarEventsView(LoginRequiredMixin, View):
    def get(self, request):
        """
        Return calendar events as JSON for FullCalendar.
        Optional query parameters:
        - start: Start date (YYYY-MM-DD)
        - end: End date (YYYY-MM-DD)
        """
        start_date = request.GET.get("start")
        end_date = request.GET.get("end")

        # Default to showing events for the next 30 days if no date range provided
        if not start_date:
            start_date = timezone.now().date()
        else:
            start_date = datetime.fromisoformat(start_date).date()

        if not end_date:
            end_date = start_date + timedelta(days=30)
        else:
            end_date = datetime.fromisoformat(end_date).date()

        # Convert dates to datetime objects for filtering
        start_datetime = timezone.make_aware(
            datetime.combine(start_date, datetime.min.time())
        )
        end_datetime = timezone.make_aware(
            datetime.combine(end_date, datetime.max.time()))

        # Get events for the user within the date range
        events = CalendarEvent.objects.filter(
            user=request.user, dtstart__lte=end_datetime, dtend__gte=start_datetime
        ) | CalendarEvent.objects.filter(
            user=request.user, dtstart__range=(start_datetime, end_datetime)
        )

        # Convert to FullCalendar format
        event_data = [event.to_dict() for event in events]

        return JsonResponse(event_data, safe=False)


class UploadICSView(LoginRequiredMixin, View):
    def post(self, request):
        """
        Handle ICS file upload and import events.
        """
        if "ics_file" not in request.FILES:
            return JsonResponse(
                {"status": "error", "message": "No ICS file provided"}, status=400
            )

        ics_file = request.FILES["ics_file"]
        source = request.POST.get("source", "custom")

        try:
            # Read the file into memory
            file_content = io.BytesIO(ics_file.read())

            # Import events from the file
            events_created = CalendarEvent.from_ics(
                file_content, source=source, user=request.user
            )

            return JsonResponse(
                {
                    "status": "success",
                    "message": f"Successfully imported {events_created} events",
                    "events_created": events_created,
                }
            )
        except Exception as e:
            return JsonResponse(
                {"status": "error",
                    "message": f"Error importing ICS file: {str(e)}"},
                status=500,
            )
