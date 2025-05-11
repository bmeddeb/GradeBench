from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.template.response import TemplateResponse

from lms.canvas.models import (
    CanvasCourse,
    CanvasEnrollment,
    CanvasAssignment,
    CanvasRubric,
    CanvasRubricCriterion,
    CanvasRubricRating,
)
from lms.canvas.admin.models import Canvas

# Register Canvas as the main model


@admin.register(Canvas)
class CanvasAdmin(admin.ModelAdmin):
    model = Canvas

    # Override the changelist template
    change_list_template = "admin/lms/canvas/change_list.html"

    # Override changelist view to not query the database
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["canvas_models"] = [
            {"name": "Courses", "url": reverse("admin:lms_canvascourse_changelist")},
            {
                "name": "Enrollments",
                "url": reverse("admin:lms_canvasenrollment_changelist"),
            },
            {
                "name": "Assignments",
                "url": reverse("admin:lms_canvasassignment_changelist"),
            },
            {"name": "Rubrics", "url": reverse("admin:lms_canvasrubric_changelist")},
            {
                "name": "Rubric Criteria",
                "url": reverse("admin:lms_canvasrubriccriterion_changelist"),
            },
            {
                "name": "Rubric Ratings",
                "url": reverse("admin:lms_canvasrubricrating_changelist"),
            },
        ]
        context = dict(
            self.admin_site.each_context(request),
            title="Canvas Management",
            app_label=self.model._meta.app_label,
            opts=self.model._meta,
            **extra_context,
        )
        return TemplateResponse(request, self.change_list_template, context)

    # No add, change, or delete permissions for the proxy model
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# Register models with standard ModelAdmin classes


@admin.register(CanvasCourse)
class CanvasCourseAdmin(admin.ModelAdmin):
    list_display = ("name", "course_code", "canvas_id", "created_at")
    list_filter = ("is_public", "workflow_state")
    search_fields = ("name", "course_code", "canvas_id")

    def get_model_perms(self, request):
        """
        Hide this model from the main admin index page
        """
        return {}


@admin.register(CanvasEnrollment)
class CanvasEnrollmentAdmin(admin.ModelAdmin):
    list_display = ("user_name", "course", "role", "enrollment_state")
    list_filter = ("role", "enrollment_state", "course")
    search_fields = ("user_name", "email", "canvas_id")

    def get_model_perms(self, request):
        """
        Hide this model from the main admin index page
        """
        return {}


@admin.register(CanvasAssignment)
class CanvasAssignmentAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "canvas_id",
        "course",
        "due_at",
        "points_possible",
        "grading_type",
    )
    list_filter = ("course", "grading_type", "published")
    search_fields = ("name", "canvas_id")
    date_hierarchy = "due_at"

    def get_model_perms(self, request):
        """
        Hide this model from the main admin index page
        """
        return {}


@admin.register(CanvasRubric)
class CanvasRubricAdmin(admin.ModelAdmin):
    list_display = ("title", "canvas_id", "points_possible", "created_at")
    search_fields = ("title", "canvas_id")

    def get_model_perms(self, request):
        """
        Hide this model from the main admin index page
        """
        return {}


@admin.register(CanvasRubricCriterion)
class CanvasRubricCriterionAdmin(admin.ModelAdmin):
    list_display = (
        "description",
        "rubric",
        "points",
        "criterion_use_range",
        "canvas_id",
    )
    list_filter = ("rubric", "criterion_use_range")
    search_fields = ("description", "canvas_id")

    def get_model_perms(self, request):
        """
        Hide this model from the main admin index page
        """
        return {}


@admin.register(CanvasRubricRating)
class CanvasRubricRatingAdmin(admin.ModelAdmin):
    list_display = ("description", "criterion", "points", "canvas_id")
    list_filter = ("criterion",)
    search_fields = ("description", "canvas_id")

    def get_model_perms(self, request):
        """
        Hide this model from the main admin index page
        """
        return {}
