# GradeBench Roadmap & Requirements

## 1. User Management System

### User Types (Using Django Groups)
- **Professors**: Course administrators with full access
- **TA**: Teaching assistants with grading privileges
- **Students**: Organized into teams
- **Others**: Potential observers, administrators, etc.

### User Model Extensions
- **Base UserProfile**:
  - Common fields for all users (profile picture, contact info)
  - Django User model integration for auth

- **Professor/TA Extensions**:
  - Multiple GitHub token storage
  - Token rotation mechanism
  - Rate limit tracking
  - Canvas LMS integration credentials (future)

- **Student Extensions**:
  - Team associations
  - Repository associations
  - Taiga project associations

### Team Management
- Team creation and management
- Team membership control
- Team-repository associations
- Team-project associations

## 2. GitHub Integration

### Token Management
- **Multiple Token Support**:
  - Store multiple tokens per user
  - Track token usage and rate limits
  - Implement token rotation mechanism

- **Token Validation**:
  - Real-time status checking
  - Rate limit checking (remaining calls, reset time)
  - Regular validation scheduling

### API Integration
- **Service Layer**:
  - Abstract API calls behind service interfaces
  - Support both httpx direct calls and RepoMetrics library
  - Async implementation for non-blocking operations

- **Features to Implement**:
  - Repository listing and management
  - Commit history analysis
  - Code review tracking
  - Issue/PR tracking
  - Repository statistics

## 3. Taiga Integration (Future)

### Connection Management
- Token storage and validation
- Project associations

### Project Tracking
- User story management
- Sprint tracking
- Task assignments

## 4. Canvas LMS Integration (Future)

### Course Mirroring
- Course structure synchronization
- Student roster integration
- Assignment mapping

### Grade Synchronization
- Push grades to Canvas
- Pull assignment structures

## 5. UI/UX Components

### Profile Page
- **Status Cards**:
  - User profile card with basic info
  - GitHub connection status card with:
    - Token validity
    - Rate limit information (remaining calls, reset time)
    - Multiple token management
  - Taiga connection status (future)

### Dashboard
- Summary views based on user type
- Activity feeds
- Repository and team views

## Implementation Plan (Short-term Focus)

### Phase 1: User Model Enhancements
1. Update UserProfile model to support user types via Django Groups
2. Extend model to support multiple GitHub tokens
3. Implement team data structure and associations

### Phase 2: GitHub Token Management
1. Create service for token validation and rate limit checking
2. Develop token rotation mechanism
3. Implement UI for token management in profile

### Phase 3: Team & Repository Management
1. Develop team management interface
2. Implement repository-team associations
3. Create repository analysis views

## Database Schema Adjustments

### UserProfile Extensions
```python
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # Other common fields...
```

### GitHub Token Model
```python
class GitHubToken(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='github_tokens')
    access_token = models.CharField(max_length=255)
    name = models.CharField(max_length=100, help_text="User-friendly name for this token")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True)
    last_checked = models.DateTimeField(null=True, blank=True)
    calls_remaining = models.IntegerField(null=True, blank=True)
    rate_limit_reset = models.DateTimeField(null=True, blank=True)
```

### Team Management
```python
class Team(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
class TeamMembership(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='team_memberships')
    role = models.CharField(max_length=50, choices=[('leader', 'Team Leader'), ('member', 'Team Member')])
    joined_at = models.DateTimeField(auto_now_add=True)
```

### Repository Tracking
```python
class GitHubRepository(models.Model):
    name = models.CharField(max_length=255)
    full_name = models.CharField(max_length=255, unique=True)  # owner/repo format
    teams = models.ManyToManyField(Team, related_name='repositories', blank=True)
    is_private = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    last_synced = models.DateTimeField(null=True, blank=True)
    description = models.TextField(blank=True, null=True)
```