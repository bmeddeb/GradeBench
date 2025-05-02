# GradeBench Architecture & Roadmap

## 1. User and Student Management System

### User Types (Using Django Groups)
- **Professors**: Course administrators with full access
- **TA**: Teaching assistants with grading privileges
- **Students**: Not Django users, but managed through the Student model
- **Others**: Admin users, observers, etc.

### User Model Extensions
- **Base UserProfile**:
  - Common fields for all users (profile picture, contact info)
  - Django User model integration for authentication
  - GitHub OAuth connection

- **Staff Profiles**:
  - Abstract StaffProfile model with shared functionality
  - ProfessorProfile with department, office info
  - TAProfile with supervisor (professor) reference
  - GitHub token management (many-to-many)
  - Canvas LMS integration credentials

### Student Model (Central Integration Point)
- **Core Student Entity**:
  - Not tied to Django authentication
  - Contains student identification (name, email, student ID)
  - Cross-platform identity fields (github_username, taiga_username, canvas_user_id)
  - Created and managed by professors/TAs

### Team Management
- Team model with platform-specific identifiers
- Direct relationship to students (one team to many students)
- Direct relationships to repositories and projects

## 2. GitHub Integration

### Token Management
- **GitHub Token Model**:
  - EncryptedCharField for secure token storage
  - Rate limit tracking (remaining calls, reset time)
  - Last used timestamp

### GitHub Models
- **Collaborator**: Links to Student model (one-to-one)
- **Repository**: Tracks GitHub repositories
- **Branch**: Tracks branches in repositories
- **Commit**: Records commit history with collaborator attribution
- **PullRequest**: Tracks PRs with state management (open, closed, merged)
- **Issue**: Tracks GitHub issues with state management
- **Comment**: Tracks comments on PRs, issues, and repositories
- **CodeReview**: Tracks PR reviews

### API Integration
- **Service Layer** (in progress):
  - Abstract API calls behind service interfaces
  - Async implementation for non-blocking operations
  - Use of GitHub OAuth for authentication

## 3. Taiga Integration

### Project Management Models
- **Project**: Maps to Taiga projects, linked to Team
- **Member**: Links Student to Taiga user (one-to-one)
- **Sprint**: Tracks Taiga sprints/milestones
- **UserStory**: Tracks user stories in sprints
- **Task**: Tracks individual tasks in user stories
- **TaskEvent & TaskAssignmentEvent**: Tracks task history

## 4. Canvas LMS Integration

### Canvas Models
- **CanvasIntegration**: Stores API configuration and credentials
- **CanvasCourse**: Tracks course information
- **CanvasEnrollment**: Tracks student enrollments in courses
- **CanvasAssignment**: Tracks course assignments
- **CanvasSubmission**: Tracks student submissions
- **CanvasRubric/CanvasRubricCriterion/CanvasRubricRating**: Tracks grading rubrics

## 5. UI/UX Components

### User Interface
- **Profile Pages**:
  - User profile with basic info and GitHub connection
  - GitHub token management for staff
  - Canvas API connection management

- **Canvas Integration UI**:
  - Setup page for Canvas API connections
  - Dashboard for course overview
  - Course details page
  - Student roster and detail pages
  - Assignment management

### Dashboard
- Core dashboard with navigation
- Canvas-specific dashboard
- Secure token display with toggle visibility

## 6. Architecture Highlights

### Cross-Domain Integration
- **Student as Central Entity**: 
  - The Student model serves as the central integration point
  - Platform-specific IDs stored on Student (github_username, taiga_username, canvas_user_id)
  - One-to-one relationships from domain-specific models back to Student

### Security Features
- **Token Encryption**:
  - All tokens and API keys stored using Django's encrypted model fields
  - Token visibility toggle in UI for security
  - Secure OAuth flow for GitHub integration

### Async Operations
- **AsyncModelMixin**:
  - Common mixin for async database operations
  - Consistent async interfaces for models
  - Properly handled sync_to_async operations

## Current Implementation Status

### Completed
- Core user management and profiles
- Student model with cross-domain linking
- Canvas LMS integration foundation
- GitHub and Taiga model structures
- Bootstrap-based UI foundation

### In Progress
- Canvas course synchronization
- Repository analysis and visualization
- Enhanced team management
- Calendar integration

### Future Work
- Grading integration between Canvas and GitHub
- Advanced analytics for student contributions
- Full Taiga integration with Canvas assignments
- Mobile-responsive UI enhancements