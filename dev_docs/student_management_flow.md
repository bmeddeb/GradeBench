q# Student Management Flow

This document outlines the process for managing students in GradeBench under the new decoupled Student model architecture.

## Overview

In the new architecture, students are managed as data entities rather than system users. Professors and TAs manage student records and their associations with courses, teams, and platform identities.

## Student Creation Sources

### 1. Canvas API Import

Professors can import students directly from Canvas courses they teach:

```
Professor -> Import from Canvas -> Select Course -> Import Students
```

**Process Flow:**
1. Professor authenticates with Canvas (if not already done)
2. Professor selects a Canvas course to import from
3. GradeBench fetches all student enrollments from the Canvas API
4. System creates or updates `Student` records based on Canvas data
5. System creates `CanvasEnrollment` records linking students to the course
6. System shows results of the import process (new/updated students)

**Implementation Example:**
```python
async def import_students_from_canvas(course_id, professor):
    """Import students from Canvas for a specific course"""
    # Fetch enrolled students from Canvas API
    canvas_api = CanvasAPI(professor.lms_access_token)
    canvas_enrollments = await canvas_api.get_enrollments(course_id)
    
    # Get or create the Canvas course in our system
    canvas_course, _ = await CanvasCourse.objects.aget_or_create(
        course_id=course_id,
        defaults={
            'name': canvas_enrollments[0]['course']['name'] if canvas_enrollments else "Unknown Course",
            'team': professor.team
        }
    )
    
    # Track results
    created_count = 0
    updated_count = 0
    
    # Process each enrollment
    for enrollment in canvas_enrollments:
        if enrollment['type'] == 'StudentEnrollment':
            # Create or update the Student record
            student, created = await Student.objects.aget_or_create(
                email=enrollment['user']['email'],
                defaults={
                    'first_name': enrollment['user']['first_name'],
                    'last_name': enrollment['user']['last_name'],
                    'canvas_user_id': str(enrollment['user']['id']),
                    'created_by': professor.user
                }
            )
            
            if created:
                created_count += 1
            else:
                updated_count += 1
                # Update canvas_user_id if not already set
                if not student.canvas_user_id:
                    student.canvas_user_id = str(enrollment['user']['id'])
                    await student.asave()
            
            # Link student to the Canvas course
            await CanvasEnrollment.objects.aget_or_create(
                course=canvas_course,
                student=student,
                defaults={
                    'role': enrollment['type']
                }
            )
            
    return {
        'created': created_count,
        'updated': updated_count,
        'total': len(canvas_enrollments)
    }
```

### 2. Manual Creation

Professors or TAs can manually add students to the system:

```
Professor -> Courses -> Select Course -> Add Student -> Enter Details
```

**Process Flow:**
1. Professor navigates to a course page
2. Professor clicks "Add Student" button
3. Professor enters student details (name, email, student ID)
4. System creates a new `Student` record
5. System associates student with the current course
6. Student appears in the course roster

**Implementation Example:**
```python
async def create_student_manually(first_name, last_name, email, student_id, course_id, professor):
    """Create a student manually and associate with a course"""
    # Create the student
    student = await Student.objects.acreate(
        first_name=first_name,
        last_name=last_name,
        email=email,
        student_id=student_id,
        created_by=professor.user
    )
    
    # Get the course
    course = await CanvasCourse.objects.aget(id=course_id)
    
    # Associate student with course
    await CanvasEnrollment.objects.acreate(
        course=course,
        student=student,
        role='StudentEnrollment'
    )
    
    return student
```

### 3. CSV Import

Professors can import multiple students at once via CSV:

```
Professor -> Courses -> Select Course -> Import CSV -> Upload File
```

**Process Flow:**
1. Professor navigates to a course page
2. Professor clicks "Import CSV" button
3. System provides a CSV template with required fields
4. Professor uploads completed CSV file
5. System validates the CSV data
6. System creates or updates `Student` records for each row
7. System associates students with the current course
8. System shows import results (successful/failed imports)

**CSV Format:**
```
first_name,last_name,email,student_id
John,Doe,john.doe@example.com,12345
Jane,Smith,jane.smith@example.com,67890
```

**Implementation Example:**
```python
async def import_students_from_csv(csv_file, course_id, professor):
    """Import students from CSV file and associate with a course"""
    # Read CSV file
    reader = await sync_to_async(csv.DictReader)(csv_file)
    rows = await sync_to_async(list)(reader)
    
    # Get the course
    course = await CanvasCourse.objects.aget(id=course_id)
    
    # Track results
    results = {
        'created': 0,
        'updated': 0,
        'failed': 0,
        'errors': []
    }
    
    # Process each row
    for row in rows:
        try:
            # Validate required fields
            if not all(key in row and row[key] for key in ['first_name', 'last_name', 'email']):
                results['failed'] += 1
                results['errors'].append(f"Missing required fields for row: {row}")
                continue
                
            # Create or update student
            student, created = await Student.objects.aget_or_create(
                email=row['email'],
                defaults={
                    'first_name': row['first_name'],
                    'last_name': row['last_name'],
                    'student_id': row.get('student_id', ''),
                    'created_by': professor.user
                }
            )
            
            if created:
                results['created'] += 1
            else:
                results['updated'] += 1
            
            # Associate with course
            await CanvasEnrollment.objects.aget_or_create(
                course=course,
                student=student,
                defaults={
                    'role': 'StudentEnrollment'
                }
            )
            
        except Exception as e:
            results['failed'] += 1
            results['errors'].append(f"Error processing row {row}: {str(e)}")
    
    return results
```

## Team Association

Students can be associated with teams for group projects:

```
Professor -> Teams -> Select Team -> Add Students -> Select from Course
```

**Process Flow:**
1. Professor creates a team
2. Professor selects students from course roster to add to team
3. System updates the `team` field for selected students
4. System shows the updated team roster

**Implementation Example:**
```python
async def add_students_to_team(team_id, student_ids, professor):
    """Add multiple students to a team"""
    # Get the team
    team = await Team.objects.aget(id=team_id)
    
    # Verify professor has access to this team
    if team.created_by != professor.user:
        raise PermissionError("You don't have permission to modify this team")
    
    # Update team for each student
    updated_count = 0
    for student_id in student_ids:
        student = await Student.objects.aget(id=student_id)
        student.team = team
        await student.asave()
        updated_count += 1
    
    return {
        'team': team.name,
        'updated_count': updated_count
    }
```

## Platform Identity Linking

When information is fetched from external platforms, the system links it to the appropriate student record:

### GitHub Integration

```python
async def link_github_identity(student, github_data):
    """Link GitHub identity to a student"""
    # Create or update GitHub collaborator record
    collaborator, created = await Collaborator.objects.aget_or_create(
        student=student,
        defaults={
            'github_id': github_data['id'],
            'username': github_data['login'],
            'email': github_data.get('email', '')
        }
    )
    
    # Update student's GitHub username if not already set
    if not student.github_username:
        student.github_username = github_data['login']
        await student.asave()
    
    return collaborator
```

### Taiga Integration

```python
async def link_taiga_identity(student, taiga_data, project):
    """Link Taiga identity to a student"""
    # Create or update Taiga member record
    member, created = await Member.objects.aget_or_create(
        student=student,
        project=project,
        defaults={
            'role_name': taiga_data['role'],
            'color': taiga_data.get('color', '#000000')
        }
    )
    
    # Update student's Taiga username if not already set
    if not student.taiga_username:
        student.taiga_username = taiga_data['username']
        await student.asave()
    
    return member
```

## User Interface Considerations

### Course Roster View

- Display list of students in a course
- Show platform connections status (GitHub, Taiga, Canvas)
- Allow filtering by team
- Provide actions for adding/removing students

### Student Detail View

- Show student information
- Display all platform connections
- Show team membership
- List assignments and grades
- Provide actions for editing student details

### Import/Add Controls

- Canvas API import button
- Manual add student form
- CSV import form with template download

## Permissions and Access Control

- Only professors can import students from Canvas
- Professors can add/edit students in their courses
- TAs can be granted permission to manage students by professors
- Students themselves don't have system access

## Data Flow Diagrams

### Canvas API Import Flow

```
+----------------+      +---------------+      +------------------+
| Professor      |----->| Canvas API    |----->| Student Records  |
| selects course |      | fetch students|      | created/updated  |
+----------------+      +---------------+      +------------------+
                                                       |
                                                       v
                                             +------------------+
                                             | Course           |
                                             | Enrollments      |
                                             | created          |
                                             +------------------+
```

### Manual Student Creation Flow

```
+----------------+      +---------------+      +------------------+
| Professor      |----->| Student Form  |----->| Student Record   |
| adds student   |      | submission    |      | created          |
+----------------+      +---------------+      +------------------+
                                                       |
                                                       v
                                             +------------------+
                                             | Course           |
                                             | Enrollment       |
                                             | created          |
                                             +------------------+
```

### Platform Identity Linking Flow

```
+----------------+      +---------------+      +------------------+
| API Data       |----->| Match student |----->| Platform Identity|
| from GitHub/   |      | by email or   |      | record created   |
| Taiga/Canvas   |      | username      |      | or updated       |
+----------------+      +---------------+      +------------------+
                                                       |
                                                       v
                                             +------------------+
                                             | Student record   |
                                             | updated with     |
                                             | platform ID      |
                                             +------------------+
```

## Implementation Timeline

1. **Phase 1**: Core Student model implementation
   - Create the new Student model
   - Update platform-specific models
   - Implement basic CRUD operations

2. **Phase 2**: Data migration
   - Migrate existing StudentProfile data to Student model
   - Link platform identities to new Student records
   - Test data integrity

3. **Phase 3**: UI implementation
   - Update views to use new Student model
   - Implement import flows (Canvas, CSV)
   - Create student management interfaces

4. **Phase 4**: Testing and deployment
   - End-to-end testing of student flows
   - Performance testing
   - Deployment to production
