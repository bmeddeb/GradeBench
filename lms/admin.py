from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.template.response import TemplateResponse

from lms.canvas.models import (
    CanvasCourse, CanvasEnrollment, CanvasAssignment, Rubric, 
    RubricCriterion, RubricRating, RubricAssociation, RubricAssessment
)
from lms.canvas.admin.models import Canvas

# Register Canvas as the main model
@admin.register(Canvas)
class CanvasAdmin(admin.ModelAdmin):
    model = Canvas
    
    # Override the changelist template
    change_list_template = 'admin/lms/canvas/change_list.html'
    
    # Override changelist view to not query the database
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['canvas_models'] = [
            {
                'name': 'Courses',
                'url': reverse('admin:lms_canvascourse_changelist')
            },
            {
                'name': 'Enrollments',
                'url': reverse('admin:lms_canvasenrollment_changelist')
            },
            {
                'name': 'Assignments',
                'url': reverse('admin:lms_canvasassignment_changelist')
            },
            {
                'name': 'Rubrics',
                'url': reverse('admin:lms_rubric_changelist')
            },
            {
                'name': 'Rubric Criteria',
                'url': reverse('admin:lms_rubriccriterion_changelist')
            },
            {
                'name': 'Rubric Ratings',
                'url': reverse('admin:lms_rubricrating_changelist')
            },
            {
                'name': 'Rubric Associations',
                'url': reverse('admin:lms_rubricassociation_changelist')
            },
            {
                'name': 'Rubric Assessments',
                'url': reverse('admin:lms_rubricassessment_changelist')
            },
        ]
        context = dict(
            self.admin_site.each_context(request),
            title="Canvas Management",
            app_label=self.model._meta.app_label,
            opts=self.model._meta,
            **extra_context
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
    list_display = ('name', 'course_id', 'term', 'team', 'created_at')
    list_filter = ('team', 'term')
    search_fields = ('name', 'course_id')
    
    def get_model_perms(self, request):
        """
        Hide this model from the main admin index page
        """
        return {}

@admin.register(CanvasEnrollment)
class CanvasEnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'role')
    list_filter = ('role', 'course')
    search_fields = ('student__user_profile__user__username',)
    
    def get_model_perms(self, request):
        """
        Hide this model from the main admin index page
        """
        return {}

@admin.register(CanvasAssignment)
class CanvasAssignmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'assignment_id', 'course', 'due_at', 'max_score')
    list_filter = ('course',)
    search_fields = ('name', 'assignment_id')
    date_hierarchy = 'due_at'
    
    def get_model_perms(self, request):
        """
        Hide this model from the main admin index page
        """
        return {}

@admin.register(Rubric)
class RubricAdmin(admin.ModelAdmin):
    list_display = ('title', 'rubric_id', 'points_possible', 'reusable', 'created_at')
    list_filter = ('reusable', 'read_only')
    search_fields = ('title', 'rubric_id')
    
    def get_model_perms(self, request):
        """
        Hide this model from the main admin index page
        """
        return {}

@admin.register(RubricCriterion)
class RubricCriterionAdmin(admin.ModelAdmin):
    list_display = ('description', 'rubric', 'points', 'criterion_use_range')
    list_filter = ('rubric', 'criterion_use_range')
    search_fields = ('description', 'criterion_id')
    
    def get_model_perms(self, request):
        """
        Hide this model from the main admin index page
        """
        return {}

@admin.register(RubricRating)
class RubricRatingAdmin(admin.ModelAdmin):
    list_display = ('description', 'criterion', 'points')
    list_filter = ('criterion',)
    search_fields = ('description', 'rating_id')
    
    def get_model_perms(self, request):
        """
        Hide this model from the main admin index page
        """
        return {}

@admin.register(RubricAssociation)
class RubricAssociationAdmin(admin.ModelAdmin):
    list_display = ('rubric', 'course', 'assignment', 'use_for_grading', 'purpose')
    list_filter = ('use_for_grading', 'purpose')
    search_fields = ('rubric__title',)
    
    def get_model_perms(self, request):
        """
        Hide this model from the main admin index page
        """
        return {}

@admin.register(RubricAssessment)
class RubricAssessmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'rubric', 'assessor', 'score', 'created_at')
    list_filter = ('assessment_type',)
    search_fields = ('student__user_profile__user__username',)
    date_hierarchy = 'created_at'
    
    def get_model_perms(self, request):
        """
        Hide this model from the main admin index page
        """
        return {}
