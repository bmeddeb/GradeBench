from django.contrib import admin
from lms.canvas.models import (
    CanvasCourse, CanvasEnrollment, CanvasAssignment, Rubric, 
    RubricCriterion, RubricRating, RubricAssociation, RubricAssessment
)

@admin.register(CanvasCourse)
class CanvasCourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'course_id', 'term', 'team', 'created_at')
    list_filter = ('team', 'term')
    search_fields = ('name', 'course_id')

@admin.register(CanvasEnrollment)
class CanvasEnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'role')
    list_filter = ('role', 'course')
    search_fields = ('student__user_profile__user__username',)

@admin.register(CanvasAssignment)
class CanvasAssignmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'assignment_id', 'course', 'due_at', 'max_score')
    list_filter = ('course',)
    search_fields = ('name', 'assignment_id')
    date_hierarchy = 'due_at'

@admin.register(Rubric)
class RubricAdmin(admin.ModelAdmin):
    list_display = ('title', 'rubric_id', 'points_possible', 'reusable', 'created_at')
    list_filter = ('reusable', 'read_only')
    search_fields = ('title', 'rubric_id')

@admin.register(RubricCriterion)
class RubricCriterionAdmin(admin.ModelAdmin):
    list_display = ('description', 'rubric', 'points', 'criterion_use_range')
    list_filter = ('rubric', 'criterion_use_range')
    search_fields = ('description', 'criterion_id')

@admin.register(RubricRating)
class RubricRatingAdmin(admin.ModelAdmin):
    list_display = ('description', 'criterion', 'points')
    list_filter = ('criterion',)
    search_fields = ('description', 'rating_id')

@admin.register(RubricAssociation)
class RubricAssociationAdmin(admin.ModelAdmin):
    list_display = ('rubric', 'course', 'assignment', 'use_for_grading', 'purpose')
    list_filter = ('use_for_grading', 'purpose')
    search_fields = ('rubric__title',)

@admin.register(RubricAssessment)
class RubricAssessmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'rubric', 'assessor', 'score', 'created_at')
    list_filter = ('assessment_type',)
    search_fields = ('student__user_profile__user__username',)
    date_hierarchy = 'created_at'
