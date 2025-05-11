#!/usr/bin/env python
from core.models import Team, Student, TeamMembership
from lms.canvas.models import CanvasCourse, CanvasGroupCategory, CanvasGroup, CanvasGroupMembership
import os
import django
import sys

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gradebench.settings")
django.setup()

# Now import models after Django is set up


def print_header(title):
    print("\n" + "=" * 50)
    print(f" {title} ".center(50, "="))
    print("=" * 50)


def test_canvas_group_models():
    """Test the new Canvas group models"""
    print_header("Canvas Courses")
    courses = CanvasCourse.objects.all()
    print(f"Found {courses.count()} Canvas courses")

    for course in courses:
        print(f"  - {course.name} (ID: {course.canvas_id})")

        # Get group categories for this course
        categories = CanvasGroupCategory.objects.filter(course=course)
        print(f"    - Group Categories: {categories.count()}")

        for category in categories:
            print(f"      - {category.name} (ID: {category.canvas_id})")

            # Get groups in this category
            groups = CanvasGroup.objects.filter(category=category)
            print(f"        - Groups: {groups.count()}")

            for group in groups:
                # Get core team link if any
                team_link = "Linked to Team" if group.core_team else "No Team link"

                # Get memberships
                memberships = CanvasGroupMembership.objects.filter(group=group)

                print(
                    f"          - {group.name} (ID: {group.canvas_id}) - {team_link} - {memberships.count()} members")

                # If there's a linked team, check team memberships
                if group.core_team:
                    team_members = TeamMembership.objects.filter(
                        team=group.core_team)
                    print(
                        f"            - Team has {team_members.count()} members")

                    # Check if team memberships match group memberships
                    group_student_ids = set(
                        membership.student_id
                        for membership in memberships
                        if membership.student
                    )

                    team_student_ids = set(
                        membership.student_id
                        for membership in team_members
                    )

                    if group_student_ids == team_student_ids:
                        print("            - ✅ Team and group memberships match")
                    else:
                        missing_in_team = group_student_ids - team_student_ids
                        missing_in_group = team_student_ids - group_student_ids

                        if missing_in_team:
                            print(
                                f"            - ❌ {len(missing_in_team)} students in group but not in team")

                        if missing_in_group:
                            print(
                                f"            - ❌ {len(missing_in_group)} students in team but not in group")


if __name__ == "__main__":
    test_canvas_group_models()
