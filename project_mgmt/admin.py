from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.template.response import TemplateResponse

from project_mgmt.taiga.models import (
    Project, Member, Sprint, UserStory, Task, TaskEvent, TaskAssignmentEvent
)
from project_mgmt.taiga.admin.models import Taiga

# Register Taiga as the main model
@admin.register(Taiga)
class TaigaAdmin(admin.ModelAdmin):
    model = Taiga
    
    # Override the changelist template
    change_list_template = 'admin/project_mgmt/taiga/change_list.html'
    
    # Override changelist view to not query the database
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['taiga_models'] = [
            {
                'name': 'Projects',
                'url': reverse('admin:project_mgmt_project_changelist')
            },
            {
                'name': 'Members',
                'url': reverse('admin:project_mgmt_member_changelist')
            },
            {
                'name': 'Sprints',
                'url': reverse('admin:project_mgmt_sprint_changelist')
            },
            {
                'name': 'User Stories',
                'url': reverse('admin:project_mgmt_userstory_changelist')
            },
            {
                'name': 'Tasks',
                'url': reverse('admin:project_mgmt_task_changelist')
            },
            {
                'name': 'Task Events',
                'url': reverse('admin:project_mgmt_taskevent_changelist')
            },
            {
                'name': 'Task Assignment Events',
                'url': reverse('admin:project_mgmt_taskassignmentevent_changelist')
            },
        ]
        context = dict(
            self.admin_site.each_context(request),
            title="Taiga Management",
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
@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'team', 'created_at')
    search_fields = ('name', 'slug')
    list_filter = ('team',)
    
    def get_model_perms(self, request):
        """
        Hide this model from the main admin index page
        """
        return {}

@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('student', 'project', 'role_name', 'created_at')
    list_filter = ('project', 'role_name')
    search_fields = ('student__user_profile__user__username', 'role_name')
    
    def get_model_perms(self, request):
        """
        Hide this model from the main admin index page
        """
        return {}

@admin.register(Sprint)
class SprintAdmin(admin.ModelAdmin):
    list_display = ('name', 'project', 'start_date', 'end_date', 'total_points', 'closed_points')
    list_filter = ('project',)
    search_fields = ('name',)
    date_hierarchy = 'start_date'
    
    def get_model_perms(self, request):
        """
        Hide this model from the main admin index page
        """
        return {}

@admin.register(UserStory)
class UserStoryAdmin(admin.ModelAdmin):
    list_display = ('ref', 'name', 'sprint', 'closed', 'total_points', 'created_date')
    list_filter = ('sprint', 'closed')
    search_fields = ('ref', 'name', 'description')
    date_hierarchy = 'created_date'
    
    def get_model_perms(self, request):
        """
        Hide this model from the main admin index page
        """
        return {}

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('ref', 'name', 'user_story', 'assigned_to', 'is_closed', 'created_date')
    list_filter = ('user_story__sprint', 'is_closed')
    search_fields = ('ref', 'name')
    date_hierarchy = 'created_date'
    
    def get_model_perms(self, request):
        """
        Hide this model from the main admin index page
        """
        return {}

@admin.register(TaskEvent)
class TaskEventAdmin(admin.ModelAdmin):
    list_display = ('task', 'created_at', 'status_before', 'status_after')
    list_filter = ('status_before', 'status_after')
    search_fields = ('task__name',)
    date_hierarchy = 'created_at'
    
    def get_model_perms(self, request):
        """
        Hide this model from the main admin index page
        """
        return {}

@admin.register(TaskAssignmentEvent)
class TaskAssignmentEventAdmin(admin.ModelAdmin):
    list_display = ('task', 'created_at', 'assigned_to_before', 'assigned_to_after')
    search_fields = ('task__name',)
    date_hierarchy = 'created_at'
    
    def get_model_perms(self, request):
        """
        Hide this model from the main admin index page
        """
        return {}
