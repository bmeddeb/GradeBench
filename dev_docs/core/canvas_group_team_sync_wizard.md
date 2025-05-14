# Canvas Group to Core Team Synchronization Wizard

This document describes the design for the Canvas Group to Core Team synchronization wizard.

## Background

In GradeBench, Canvas groups need to be imported as Core Teams to integrate with other systems like GitHub repositories. This process should be user-driven with explicit control over which groups become teams.

## Implementation Progress

- [x] Analyze current model structure
- [x] Design database field additions
- [ ] Update Team model with new fields
- [ ] Create database migrations
- [ ] Design wizard interface mockups
- [ ] Implement backend service logic
- [ ] Create wizard templates
- [ ] Add GitHub integration
- [ ] Test end-to-end flow
- [ ] Deploy to production

## Core Team Model Changes

The Core Team model will be enhanced with these additional fields to track Canvas Group Set information:

```python
# Canvas group set (category) reference fields
canvas_group_set_id = models.PositiveIntegerField(
    null=True, 
    blank=True, 
    db_index=True,
    help_text="Canvas group category ID this team belongs to"
)

canvas_group_set_name = models.CharField(
    max_length=255,
    null=True,
    blank=True,
    help_text="Name of the Canvas group category this team belongs to"
)
```

## Wizard Interface Design

The synchronization process will follow a step-by-step wizard approach using the paper-dashboard-pro wizard template.

### Step 1: Course Selection
- Display all Canvas courses with filters for:
  - Term/semester
  - Active/inactive status
  - Search by course name/code
- Allow selection of one or multiple courses to continue
- Include course details (number of students, existing groups)
- "Next" button to proceed to Step 2

### Step 2: Group Set Selection
- For each selected course, display available group sets (categories)
- Allow filtering and multi-selection of group sets
- Show statistics for each group set:
  - Number of groups
  - Number already imported
  - Last sync date (if applicable)
- "Back" and "Next" buttons for navigation

### Step 3: Group Selection
- Display groups organized by course and group set
- Include checkboxes for selection with:
  - "Select All" option
  - "Select All in Group Set" option
  - "Select Only New" option (groups not yet imported)
- Show key information for each group:
  - Name
  - Number of members
  - Current import status (new/existing)
- "Back" and "Next" buttons

### Step 4: GitHub Configuration
- Table of selected groups with fields for GitHub configuration:
  - GitHub organization (text field)
  - Team description override (optional)
- Batch actions to apply the same GitHub org to multiple groups
- Option to validate GitHub organization names
- "Back" and "Next" buttons

### Step 5: Confirmation
- Summary of actions to be performed:
  - Number of new teams to create
  - Number of existing teams to update
  - GitHub organizations to use
- Preview of resulting Core Teams structure
- "Back" and "Process" buttons

### Step 6: Results
- Success/failure status for each team
- Details of any errors encountered
- Option to retry failed imports
- "Done" and "Start Over" buttons

## Implementation Details

1. **Backend Service**
   - [ ] Create a TeamSyncService class that handles the logic for each step
   - [ ] Implement methods for retrieving available courses, group sets, and groups
   - [ ] Add functions for Team creation/update with GitHub details

2. **Database Model Updates**
   - [ ] Add canvas_group_set_id and canvas_group_set_name to Team model
   - [ ] Create migrations for these changes
   - [ ] Update existing Teams with correct group set info
   - [ ] Add migration command for backfilling existing teams

3. **Frontend Views**
   - [ ] Create a new WizardView class that manages wizard state
   - [ ] Implement AJAX endpoints for each step's data needs
   - [ ] Use session to store in-progress selections

4. **Templates**
   - [ ] Create template for step 1 (course selection)
   - [ ] Create template for step 2 (group set selection)
   - [ ] Create template for step 3 (group selection)
   - [ ] Create template for step 4 (GitHub configuration)
   - [ ] Create template for step 5 (confirmation)
   - [ ] Create template for step 6 (results)
   - [ ] Implement client-side validation
   - [ ] Add JavaScript for dynamic UI updates

5. **GitHub Integration**
   - [ ] Add optional validation against GitHub API
   - [ ] Store GitHub organization info for future use
   - [ ] Implement background job for GitHub team creation

## Benefits

This wizard approach offers a structured, user-friendly process that guides users through the synchronization while providing flexibility and control at each step. Users have full visibility into what groups are being imported and can immediately configure GitHub integration details.

## Future Enhancements

- [ ] Add ability to save wizard progress and resume later
- [ ] Implement periodic synchronization to keep teams updated
- [ ] Add email notifications for completed imports
- [ ] Create dashboard for monitoring team synchronization status