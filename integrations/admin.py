from django.contrib import admin
from integrations.models import ProviderAssociation, GradeLink

@admin.register(ProviderAssociation)
class ProviderAssociationAdmin(admin.ModelAdmin):
    list_display = ('source_content_type', 'source_object_id', 'target_content_type', 'target_object_id', 'association_type', 'created_at')
    list_filter = ('source_content_type', 'target_content_type', 'association_type')
    search_fields = ('source_object_id', 'target_object_id', 'association_type')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(GradeLink)
class GradeLinkAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'lms_assignment_id', 'git_repository_id', 'grade', 'graded_at')
    list_filter = ('graded_at', 'lms_course_id')
    search_fields = ('student_id', 'lms_assignment_id', 'git_repository_id')
    readonly_fields = ('created_at', 'updated_at')
