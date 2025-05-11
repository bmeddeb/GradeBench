from django.db import models
from core.async_utils import AsyncModelMixin


class ProjectProvider(models.Model, AsyncModelMixin):
    """
    Abstract base model for all project management providers.

    This defines the common interface that all project management providers must implement.
    """

    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True

    async def authenticate(self, **kwargs):
        """
        Authenticate with the project management provider.

        Args:
            **kwargs: Provider-specific authentication parameters

        Returns:
            bool: True if authentication was successful
        """
        raise NotImplementedError("Subclasses must implement authenticate()")

    async def get_projects(self, **kwargs):
        """
        Fetch projects from the provider.

        Args:
            **kwargs: Provider-specific parameters

        Returns:
            list: List of project information
        """
        raise NotImplementedError("Subclasses must implement get_projects()")

    async def get_user_stories(self, project, **kwargs):
        """
        Fetch user stories for a specific project.

        Args:
            project: Project identifier
            **kwargs: Provider-specific parameters

        Returns:
            list: List of user story information
        """
        raise NotImplementedError("Subclasses must implement get_user_stories()")

    async def get_sprints(self, project, **kwargs):
        """
        Fetch sprints for a specific project.

        Args:
            project: Project identifier
            **kwargs: Provider-specific parameters

        Returns:
            list: List of sprint information
        """
        raise NotImplementedError("Subclasses must implement get_sprints()")
