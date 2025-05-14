from django.db import models
from core.models import Team, Student
from core.async_utils import AsyncModelMixin


class Collaborator(models.Model, AsyncModelMixin):
    # Relationship to Student model
    student = models.OneToOneField(
        Student, on_delete=models.CASCADE, related_name="github_collaborator"
    )

    github_id = models.IntegerField(unique=True)
    username = models.CharField(max_length=255)
    email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.username


class Repository(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField()
    team = models.ForeignKey(
        Team, on_delete=models.CASCADE, related_name="repositories"
    )
    created_at_record = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Branch(models.Model):
    name = models.CharField(max_length=255)
    repository = models.ForeignKey(
        Repository, on_delete=models.CASCADE, related_name="branches"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Commit(models.Model):
    sha = models.CharField(max_length=255, unique=True, db_index=True)
    short_sha = models.CharField(max_length=7, db_index=True)
    message = models.TextField()
    summary = models.TextField()
    date = models.DateTimeField()
    additions = models.IntegerField(default=0)
    deletions = models.IntegerField(default=0)
    files_changed = models.IntegerField(default=0)
    url = models.URLField(blank=True)
    is_merged = models.BooleanField(default=False)

    # Author information
    author_name = models.CharField(max_length=255)
    author_email = models.EmailField()
    author_time = models.DateTimeField()

    # Committer information
    committer_name = models.CharField(max_length=255)
    committer_email = models.EmailField()
    committer_time = models.DateTimeField()

    # Relationships
    repository = models.ForeignKey(
        Repository, on_delete=models.CASCADE, related_name="commits"
    )
    collaborator = models.ForeignKey(
        Collaborator, on_delete=models.CASCADE, related_name="commits"
    )
    branch = models.ForeignKey(
        Branch, on_delete=models.SET_NULL, null=True, blank=True, related_name="commits"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.sha

    def save(self, *args, **kwargs):
        if self.sha and not self.short_sha:
            self.short_sha = self.sha[:7]
        if self.message and not self.summary:
            self.summary = self.message.splitlines()[0].strip()
        super().save(*args, **kwargs)

    @property
    def parents(self):
        return Commit.objects.filter(
            id__in=self.parent_relationships.values_list('parent_commit', flat=True)
        )

    @property
    def children(self):
        return Commit.objects.filter(
            id__in=self.child_relationships.values_list('commit', flat=True)
        )


class CommitParent(models.Model):
    """Model to track parent-child relationships between commits"""
    commit = models.ForeignKey(
        Commit,
        on_delete=models.CASCADE,
        related_name='parent_relationships'
    )
    parent_commit = models.ForeignKey(
        Commit,
        on_delete=models.CASCADE,
        related_name='child_relationships'
    )
    order = models.PositiveSmallIntegerField(
        default=0,
        help_text="Order of this parent in the commit's parent list (for merge commits)"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('commit', 'parent_commit')
        ordering = ['commit', 'order']

    def __str__(self):
        return f"{self.commit.sha} ← {self.parent_commit.sha}"


class PullRequestState(models.TextChoices):
    OPEN = "open", "Open"
    CLOSED = "closed", "Closed"
    MERGED = "merged", "Merged"


class PullRequest(models.Model):
    title = models.CharField(max_length=255)
    state = models.CharField(
        max_length=20, choices=PullRequestState.choices, default=PullRequestState.OPEN
    )
    created_at = models.DateTimeField()
    repository = models.ForeignKey(
        Repository, on_delete=models.CASCADE, related_name="pull_requests"
    )
    collaborator = models.ForeignKey(
        Collaborator,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pull_requests",
    )
    branch = models.ForeignKey(
        Branch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pull_requests",
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class CodeReview(models.Model):
    state = models.CharField(max_length=50)
    body = models.TextField(blank=True)
    submitted_at = models.DateTimeField()
    pull_request = models.ForeignKey(
        PullRequest, on_delete=models.CASCADE, related_name="code_reviews"
    )
    reviewer = models.ForeignKey(
        Collaborator, on_delete=models.CASCADE, related_name="reviews"
    )
    created_at = models.DateTimeField(auto_now_add=True)


class IssueState(models.TextChoices):
    OPEN = "open", "Open"
    CLOSED = "closed", "Closed"


class Issue(models.Model):
    title = models.CharField(max_length=255)
    state = models.CharField(
        max_length=20, choices=IssueState.choices, default=IssueState.OPEN
    )
    created_at = models.DateTimeField()
    repository = models.ForeignKey(
        Repository, on_delete=models.CASCADE, related_name="issues"
    )
    collaborator = models.ForeignKey(
        Collaborator, on_delete=models.CASCADE, related_name="issues"
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class Comment(models.Model):
    body = models.TextField()
    created_at = models.DateTimeField()
    comment_type = models.CharField(max_length=50)
    author = models.ForeignKey(
        Collaborator, on_delete=models.CASCADE, related_name="comments"
    )
    pull_request = models.ForeignKey(
        PullRequest,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="comments",
    )
    issue = models.ForeignKey(
        Issue, on_delete=models.SET_NULL, null=True, blank=True, related_name="comments"
    )
    repository = models.ForeignKey(
        Repository, on_delete=models.CASCADE, related_name="comments"
    )
    recorded_at = models.DateTimeField(auto_now_add=True)
