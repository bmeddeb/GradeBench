from django.contrib import admin
from .models import UserProfile, GitHubToken, ProfessorProfile, TAProfile, Team, Student, CalendarEvent


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'github_username', 'timezone', 'created_at', 'updated_at']
    list_filter = ['timezone', 'created_at', 'updated_at']
    search_fields = ['user__username', 'user__email', 'github_username', 'phone_number']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'profile_picture', 'bio')
        }),
        ('Contact Information', {
            'fields': ('phone_number',)
        }),
        ('GitHub Integration', {
            'fields': ('github_username', 'github_access_token', 'github_avatar_url')
        }),
        ('Settings', {
            'fields': ('timezone',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(GitHubToken)
class GitHubTokenAdmin(admin.ModelAdmin):
    list_display = ['name', 'scope', 'rate_limit_remaining', 'last_used', 'is_rate_limited']
    list_filter = ['scope', 'last_used', 'created_at']
    search_fields = ['name', 'scope']
    readonly_fields = ['created_at', 'updated_at', 'is_rate_limited']
    fieldsets = (
        ('Token Information', {
            'fields': ('name', 'token', 'scope')
        }),
        ('Rate Limiting', {
            'fields': ('rate_limit_remaining', 'rate_limit_reset', 'is_rate_limited')
        }),
        ('Usage', {
            'fields': ('last_used',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ProfessorProfile)
class ProfessorProfileAdmin(admin.ModelAdmin):
    list_display = ['user_profile', 'department', 'office_location']
    list_filter = ['department']
    search_fields = ['user_profile__user__username', 'user_profile__user__email', 'department']
    filter_horizontal = ['github_tokens']
    fieldsets = (
        ('Profile', {
            'fields': ('user_profile',)
        }),
        ('Department Information', {
            'fields': ('department', 'office_location', 'office_hours')
        }),
        ('External Integrations', {
            'fields': ('github_tokens', 'lms_access_token', 'lms_refresh_token', 'lms_token_expires')
        }),
    )


@admin.register(TAProfile)
class TAProfileAdmin(admin.ModelAdmin):
    list_display = ['user_profile', 'supervisor', 'hours_per_week']
    list_filter = ['hours_per_week', 'supervisor']
    search_fields = ['user_profile__user__username', 'user_profile__user__email', 'expertise_areas']
    filter_horizontal = ['github_tokens']
    fieldsets = (
        ('Profile', {
            'fields': ('user_profile',)
        }),
        ('TA Information', {
            'fields': ('supervisor', 'hours_per_week', 'expertise_areas')
        }),
        ('External Integrations', {
            'fields': ('github_tokens', 'lms_access_token', 'lms_refresh_token', 'lms_token_expires')
        }),
    )


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = [
        'name', 
        'canvas_course', 
        'canvas_group_id', 
        'canvas_group_set_id',
        'canvas_group_set_name',
        'github_organization', 
        'github_repo_name',
        'taiga_project',
        'last_synced_at',
        'created_at'
    ]
    list_filter = ['canvas_course', 'canvas_group_set_name', 'created_at', 'last_synced_at']
    search_fields = ['name', 'description', 'github_organization', 'github_repo_name', 'taiga_project']
    readonly_fields = ['created_at', 'updated_at', 'last_synced_at']
    # Uncomment the line below to show all fields in a single list:
    # fields = '__all__'
    fieldsets = (
        ('Team Information', {
            'fields': ('name', 'description')
        }),
        ('Canvas Integration', {
            'fields': ('canvas_course', 'canvas_group_id', 'canvas_group_set_id', 'canvas_group_set_name')
        }),
        ('GitHub Integration', {
            'fields': ('github_organization', 'github_repo_name', 'github_team_id')
        }),
        ('Taiga Integration', {
            'fields': ('taiga_project', 'taiga_project_id')
        }),
        ('Sync Information', {
            'fields': ('last_synced_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = [
        'full_name', 
        'email', 
        'student_id', 
        'team', 
        'github_username',
        'taiga_username',
        'canvas_user_id',
        'created_by',
        'created_at',
        'updated_at'
    ]
    list_filter = ['team', 'created_at', 'created_by']
    search_fields = ['first_name', 'last_name', 'email', 'student_id', 'github_username', 'taiga_username', 'canvas_user_id']
    readonly_fields = ['created_at', 'updated_at', 'full_name', 'display_name']
    fieldsets = (
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'email', 'student_id', 'full_name', 'display_name')
        }),
        ('Team', {
            'fields': ('team',)
        }),
        ('Platform Identifiers', {
            'fields': ('github_username', 'taiga_username', 'canvas_user_id')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def full_name(self, obj):
        return obj.full_name
    full_name.short_description = 'Full Name'


@admin.register(CalendarEvent)
class CalendarEventAdmin(admin.ModelAdmin):
    list_display = ['summary', 'dtstart', 'dtend', 'location', 'source', 'user']
    list_filter = ['source', 'all_day', 'dtstart', 'created_at']
    search_fields = ['summary', 'description', 'location', 'uid']
    readonly_fields = ['created_at', 'updated_at', 'uid']
    date_hierarchy = 'dtstart'
    fieldsets = (
        ('Event Information', {
            'fields': ('uid', 'summary', 'description', 'location')
        }),
        ('Time Information', {
            'fields': ('dtstart', 'dtend', 'all_day', 'rrule')
        }),
        ('Source Information', {
            'fields': ('source', 'user', 'last_modified')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
