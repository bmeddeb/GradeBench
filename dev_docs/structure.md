# GradeBench Application Structure

This document outlines the structure and organization of the GradeBench application, explaining the rationale behind our approach to structuring the codebase.

## Overview

GradeBench integrates with multiple external systems that serve different purposes:

- **Git Platforms**: Code repository management (GitHub, potentially GitLab, Bitbucket)
- **Project Management Tools**: Project tracking and organization (Taiga, potentially Jira, Trello)
- **Learning Management Systems**: Course management (Canvas, potentially Blackboard, Moodle)

## Project Structure

We've organized the codebase into domain-specific packages that reflect the functional differences between these systems:

```
gradebench/
├─ core/                      # Core functionality and shared components
│  ├─ __init__.py
│  ├─ models.py               # Core models shared across the application
│  ├─ async_utils.py          # Utilities for async operations
│  ├─ views.py
│  └─ ...
├─ git_providers/             # Git repository platform integrations
│  ├─ __init__.py
│  ├─ common/                 # Shared code for all git providers
│  │  ├─ __init__.py
│  │  ├─ models.py            # Abstract base models for git providers
│  │  ├─ views.py             # Common view functionality
│  │  └─ utils.py             # Utility functions specific to git operations
│  ├─ github/                 # GitHub specific implementation
│  │  ├─ __init__.py
│  │  ├─ models.py
│  │  ├─ views.py
│  │  └─ api.py               # GitHub API client
│  └─ ...                     # Other git platforms (GitLab, Bitbucket, etc.)
├─ project_mgmt/              # Project management tool integrations
│  ├─ __init__.py
│  ├─ common/                 # Shared code for all project management tools
│  │  ├─ __init__.py
│  │  ├─ models.py
│  │  └─ ...
│  ├─ taiga/                  # Taiga specific implementation
│  │  ├─ __init__.py
│  │  ├─ models.py
│  │  └─ ...
│  └─ ...                     # Other project management tools (Jira, etc.)
├─ lms/                       # Learning Management System integrations
│  ├─ __init__.py
│  ├─ common/                 # Shared code for all LMS platforms
│  │  ├─ __init__.py
│  │  ├─ models.py
│  │  └─ ...
│  ├─ canvas/                 # Canvas specific implementation
│  │  ├─ __init__.py
│  │  ├─ models.py
│  │  └─ ...
│  └─ ...                     # Other LMS platforms (Blackboard, Moodle, etc.)
├─ integrations/              # Cross-domain integrations and connections
│  ├─ __init__.py
│  ├─ models.py               # Models for linking different domains
│  ├─ services.py             # Services that coordinate across domains
│  └─ ...
```

## Rationale

### Domain-Based Organization

We've organized the codebase by domains (git, project management, LMS) rather than by technical function because:

1. Each domain has unique functionality and requirements
2. This structure allows for cleaner separation of concerns
3. Each domain can evolve independently
4. New providers within a domain can share common code

### Common Patterns

Within each domain, we follow consistent patterns:

1. **Base Models**: Abstract base classes define the interface for each domain
2. **Common Utilities**: Shared functionality is placed in the domain's `common/` package
3. **Provider Implementations**: Specific providers implement the interfaces defined in the common layer

### Async Support

Since GradeBench is built with async support:

1. All ORM and Django sync operations are wrapped in `sync_to_async`
2. Views use `async def` methods consistently
3. Common async utilities are defined in `core/async_utils.py`

## Domain Interfaces

### Git Providers Interface

Git providers must implement:
- Repository management
- Commit tracking
- Code review integration
- User authentication

### Project Management Interface

Project management tools must implement:
- Project structure (epics, user stories, tasks)
- Sprint/milestone tracking
- Team member management
- Status reporting

### LMS Interface

Learning management systems must implement:
- Course structure
- Assignment management
- Grade recording
- Student roster management

## Integration Layer

The `integrations` package connects the different domains:
- Links repositories to projects
- Maps students to repositories and projects
- Connects assignments to repositories and projects
- Provides cross-domain services

## Adding New Providers

To add a new provider:

1. Identify which domain it belongs to
2. Create a new package in the appropriate domain directory
3. Implement the abstract base classes defined in that domain's `common` package
4. Register the provider in the appropriate registry
5. Create migrations for any new models

## Django App Configuration

Each domain directory is registered as a Django app in `settings.py`:

```python
INSTALLED_APPS = [
    # Django built-ins
    'django.contrib.admin',
    'django.contrib.auth',
    # ...
    
    # GradeBench apps
    'gradebench.core',
    'gradebench.git_providers',
    'gradebench.project_mgmt',
    'gradebench.lms',
    'gradebench.integrations',
]
```

Each domain app has its own `AppConfig` in its `__init__.py` file.

## Migrations

Each domain has its own migrations directory:
- `git_providers/migrations/`
- `project_mgmt/migrations/`
- `lms/migrations/`
- `integrations/migrations/`

## Consistent URL Structure

URLs follow a consistent pattern:
- `/git/{provider}/{resource}/`
- `/project/{provider}/{resource}/`
- `/lms/{provider}/{resource}/`
- `/integrations/{resource}/`

## Future Considerations

1. **Plugin Architecture**: Moving toward a more formal plugin architecture for 3rd party extensions
2. **API Versioning**: Adding API versioning for stable external interfaces
3. **Multi-tenancy**: Supporting multiple organizations with isolated data
