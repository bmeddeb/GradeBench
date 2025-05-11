# lms/canvas/views.py

from django.shortcuts import render, get_object_or_404
from lms.canvas.models import CanvasCourse, CalendarEvent


def course_calendar(request, course_id):
    course = get_object_or_404(CanvasCourse, course_id=course_id)
    events = course.calendar_events.all()
    return render(
        request,
        "canvas/calendar.html",
        {
            "course": course,
            "events": events,
        },
    )
