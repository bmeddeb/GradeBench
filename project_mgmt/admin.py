from django.contrib import admin
from project_mgmt.taiga.models import (
    Project, Member, Sprint, UserStory, Task, TaskEvent, TaskAssignmentEvent
)

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'team', 'created_at')
    search_fields = ('name', 'slug')
    list_filter = ('team',)

@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('student', 'project', 'role_name', 'created_at')
    list_filter = ('project', 'role_name')
    search_fields = ('student__user_profile__user__username', 'role_name')

@admin.register(Sprint)
class SprintAdmin(admin.ModelAdmin):
    list_display = ('name', 'project', 'start_date', 'end_date', 'total_points', 'closed_points')
    list_filter = ('project',)
    search_fields = ('name',)
    date_hierarchy = 'start_date'

@admin.register(UserStory)
class UserStoryAdmin(admin.ModelAdmin):
    list_display = ('ref', 'name', 'sprint', 'closed', 'total_points', 'created_date')
    list_filter = ('sprint', 'closed')
    search_fields = ('ref', 'name', 'description')
    date_hierarchy = 'created_date'

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('ref', 'name', 'user_story', 'assigned_to', 'is_closed', 'created_date')
    list_filter = ('user_story__sprint', 'is_closed')
    search_fields = ('ref', 'name')
    date_hierarchy = 'created_date'

@admin.register(TaskEvent)
class TaskEventAdmin(admin.ModelAdmin):
    list_display = ('task', 'created_at', 'status_before', 'status_after')
    list_filter = ('status_before', 'status_after')
    search_fields = ('task__name',)
    date_hierarchy = 'created_at'

@admin.register(TaskAssignmentEvent)
class TaskAssignmentEventAdmin(admin.ModelAdmin):
    list_display = ('task', 'created_at', 'assigned_to_before', 'assigned_to_after')
    search_fields = ('task__name',)
    date_hierarchy = 'created_at'
