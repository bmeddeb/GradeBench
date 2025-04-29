from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import (
    BaseUserProfile,
    GitHubToken,
    ProfessorProfile,
    TAProfile,
    Team,
    Repository,
    StudentProfile,
)

# Define inline admin classes
class BaseUserProfileInline(admin.StackedInline):
    model = BaseUserProfile
    can_delete = False
    verbose_name_plural = 'User Profile'


class ProfessorProfileInline(admin.StackedInline):
    model = ProfessorProfile
    can_delete = False
    verbose_name_plural = 'Professor Profile'
    fk_name = 'user_profile'


class TAProfileInline(admin.StackedInline):
    model = TAProfile
    can_delete = False
    verbose_name_plural = 'TA Profile'
    fk_name = 'user_profile'


class StudentProfileInline(admin.StackedInline):
    model = StudentProfile
    can_delete = False
    verbose_name_plural = 'Student Profile'
    fk_name = 'user_profile'


# Define the User admin with inlines
class UserAdmin(BaseUserAdmin):
    inlines = (BaseUserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_user_type')
    
    def get_user_type(self, obj):
        if obj.groups.filter(name='Professors').exists():
            return 'Professor'
        elif obj.groups.filter(name='TAs').exists():
            return 'TA'
        elif obj.groups.filter(name='Students').exists():
            return 'Student'
        else:
            return 'Other'
    
    get_user_type.short_description = 'User Type'
    
    def get_inlines(self, request, obj=None):
        if not obj:  # Adding a new user
            return (BaseUserProfileInline,)
        
        inlines = [BaseUserProfileInline]
        # Add appropriate profile inline based on user groups
        if obj.groups.filter(name='Professors').exists():
            inlines.append(ProfessorProfileInline)
        elif obj.groups.filter(name='TAs').exists():
            inlines.append(TAProfileInline)
        elif obj.groups.filter(name='Students').exists():
            inlines.append(StudentProfileInline)
        
        return inlines


# Register your models here
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(GitHubToken)
admin.site.register(Team)
admin.site.register(Repository)

@admin.register(BaseUserProfile)
class BaseUserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'updated_at')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')


@admin.register(ProfessorProfile)
class ProfessorProfileAdmin(admin.ModelAdmin):
    list_display = ('get_name', 'department', 'office_location')
    search_fields = ('user_profile__user__username', 'user_profile__user__email', 
                     'user_profile__user__first_name', 'user_profile__user__last_name', 
                     'department')
    
    def get_name(self, obj):
        return obj.user_profile.user.get_full_name()
    
    get_name.short_description = 'Name'


@admin.register(TAProfile)
class TAProfileAdmin(admin.ModelAdmin):
    list_display = ('get_name', 'supervisor', 'hours_per_week')
    search_fields = ('user_profile__user__username', 'user_profile__user__email', 
                     'user_profile__user__first_name', 'user_profile__user__last_name')
    
    def get_name(self, obj):
        return obj.user_profile.user.get_full_name()
    
    get_name.short_description = 'Name'


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('get_name', 'student_id', 'team', 'github_username')
    search_fields = ('user_profile__user__username', 'user_profile__user__email', 
                     'user_profile__user__first_name', 'user_profile__user__last_name', 
                     'student_id', 'github_username')
    list_filter = ('team',)
    
    def get_name(self, obj):
        return obj.user_profile.user.get_full_name()
    
    get_name.short_description = 'Name'
