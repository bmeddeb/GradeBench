from django.contrib import admin
from git_providers.github.models import (
    Collaborator, Repository, Branch, Commit, PullRequest, 
    CodeReview, Issue, Comment
)

@admin.register(Collaborator)
class CollaboratorAdmin(admin.ModelAdmin):
    list_display = ('username', 'github_id', 'email', 'created_at')
    search_fields = ('username', 'email')

@admin.register(Repository)
class RepositoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'team', 'created_at')
    list_filter = ('team',)
    search_fields = ('name', 'description')

@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'repository', 'created_at')
    list_filter = ('repository',)
    search_fields = ('name',)

@admin.register(Commit)
class CommitAdmin(admin.ModelAdmin):
    list_display = ('sha', 'collaborator', 'repository', 'date', 'additions', 'deletions')
    list_filter = ('repository', 'is_merged')
    search_fields = ('sha', 'message')
    date_hierarchy = 'date'

@admin.register(PullRequest)
class PullRequestAdmin(admin.ModelAdmin):
    list_display = ('title', 'repository', 'state', 'collaborator', 'created_at')
    list_filter = ('repository', 'state')
    search_fields = ('title',)

@admin.register(CodeReview)
class CodeReviewAdmin(admin.ModelAdmin):
    list_display = ('pull_request', 'reviewer', 'state', 'submitted_at')
    list_filter = ('state',)
    search_fields = ('body',)

@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    list_display = ('title', 'repository', 'state', 'collaborator', 'created_at')
    list_filter = ('repository', 'state')
    search_fields = ('title',)

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'comment_type', 'repository', 'created_at')
    list_filter = ('comment_type', 'repository')
    search_fields = ('body',)
