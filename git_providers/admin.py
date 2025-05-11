from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.template.response import TemplateResponse

# Import our GitHub models and proxy model
from git_providers.github.models import (
    Collaborator,
    Repository,
    Branch,
    Commit,
    PullRequest,
    CodeReview,
    Issue,
    Comment,
)
from git_providers.github.admin.models import GitHub


# Register GitHub as the main model
@admin.register(GitHub)
class GitHubAdmin(admin.ModelAdmin):
    model = GitHub

    # Override the changelist template
    change_list_template = "admin/git_providers/github/change_list.html"

    # Override changelist view to not query the database
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["github_models"] = [
            {
                "name": "Collaborators",
                "url": reverse("admin:git_providers_collaborator_changelist"),
            },
            {
                "name": "Repositories",
                "url": reverse("admin:git_providers_repository_changelist"),
            },
            {
                "name": "Branches",
                "url": reverse("admin:git_providers_branch_changelist"),
            },
            {
                "name": "Commits",
                "url": reverse("admin:git_providers_commit_changelist"),
            },
            {
                "name": "Pull Requests",
                "url": reverse("admin:git_providers_pullrequest_changelist"),
            },
            {
                "name": "Code Reviews",
                "url": reverse("admin:git_providers_codereview_changelist"),
            },
            {"name": "Issues", "url": reverse("admin:git_providers_issue_changelist")},
            {
                "name": "Comments",
                "url": reverse("admin:git_providers_comment_changelist"),
            },
        ]
        context = dict(
            self.admin_site.each_context(request),
            title="GitHub Management",
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
@admin.register(Collaborator)
class CollaboratorAdmin(admin.ModelAdmin):
    list_display = ("username", "github_id", "email", "created_at")
    search_fields = ("username", "email")

    def get_model_perms(self, request):
        """
        Hide this model from the main admin index page
        """
        return {}


@admin.register(Repository)
class RepositoryAdmin(admin.ModelAdmin):
    list_display = ("name", "team", "created_at")
    list_filter = ("team",)
    search_fields = ("name", "description")

    def get_model_perms(self, request):
        """
        Hide this model from the main admin index page
        """
        return {}


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ("name", "repository", "created_at")
    list_filter = ("repository",)
    search_fields = ("name",)

    def get_model_perms(self, request):
        """
        Hide this model from the main admin index page
        """
        return {}


@admin.register(Commit)
class CommitAdmin(admin.ModelAdmin):
    list_display = (
        "sha",
        "collaborator",
        "repository",
        "date",
        "additions",
        "deletions",
    )
    list_filter = ("repository", "is_merged")
    search_fields = ("sha", "message")
    date_hierarchy = "date"

    def get_model_perms(self, request):
        """
        Hide this model from the main admin index page
        """
        return {}


@admin.register(PullRequest)
class PullRequestAdmin(admin.ModelAdmin):
    list_display = ("title", "repository", "state", "collaborator", "created_at")
    list_filter = ("repository", "state")
    search_fields = ("title",)

    def get_model_perms(self, request):
        """
        Hide this model from the main admin index page
        """
        return {}


@admin.register(CodeReview)
class CodeReviewAdmin(admin.ModelAdmin):
    list_display = ("pull_request", "reviewer", "state", "submitted_at")
    list_filter = ("state",)
    search_fields = ("body",)

    def get_model_perms(self, request):
        """
        Hide this model from the main admin index page
        """
        return {}


@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    list_display = ("title", "repository", "state", "collaborator", "created_at")
    list_filter = ("repository", "state")
    search_fields = ("title",)

    def get_model_perms(self, request):
        """
        Hide this model from the main admin index page
        """
        return {}


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("author", "comment_type", "repository", "created_at")
    list_filter = ("comment_type", "repository")
    search_fields = ("body",)

    def get_model_perms(self, request):
        """
        Hide this model from the main admin index page
        """
        return {}
