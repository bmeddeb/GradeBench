from django.db import models
from core.async_utils import AsyncModelMixin


class GitProvider(models.Model, AsyncModelMixin):
    """
    Abstract base model for all Git providers.
    
    This defines the common interface that all Git providers must implement.
    """
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        abstract = True
    
    async def authenticate(self, **kwargs):
        """
        Authenticate with the Git provider.
        
        Args:
            **kwargs: Provider-specific authentication parameters
            
        Returns:
            bool: True if authentication was successful
        """
        raise NotImplementedError("Subclasses must implement authenticate()")
    
    async def get_repositories(self, **kwargs):
        """
        Fetch repositories from the Git provider.
        
        Args:
            **kwargs: Provider-specific parameters
            
        Returns:
            list: List of repository information
        """
        raise NotImplementedError("Subclasses must implement get_repositories()")
    
    async def get_commits(self, repository, **kwargs):
        """
        Fetch commits for a specific repository.
        
        Args:
            repository: Repository identifier
            **kwargs: Provider-specific parameters
            
        Returns:
            list: List of commit information
        """
        raise NotImplementedError("Subclasses must implement get_commits()")
    
    async def get_branches(self, repository, **kwargs):
        """
        Fetch branches for a specific repository.
        
        Args:
            repository: Repository identifier
            **kwargs: Provider-specific parameters
            
        Returns:
            list: List of branch information
        """
        raise NotImplementedError("Subclasses must implement get_branches()")
