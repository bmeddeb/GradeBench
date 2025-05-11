# Canvas Group Management Module - Phase 3 Design

This document outlines the design and implementation plan for Phase 3 of the Canvas Group Management Module, which focuses on implementing interactive student assignment functionality.

## Requirements

Phase 3 focuses on implementing:
1. Drag-and-drop interface for assigning students to groups
2. Functionality to move students between groups
3. Random assignment of unassigned students to groups

## JavaScript Library Options

### 1. SortableJS
**Pros:**
- Lightweight, zero dependencies
- Great performance with large lists
- Handles nested lists well (ideal for groups within categories)
- Touch-friendly for mobile devices
- MIT licensed

**Cons:**
- Less integrated with existing jQuery codebase

### 2. jQuery UI Draggable/Droppable
**Pros:**
- Integrates seamlessly with existing jQuery code
- Well-documented with extensive examples
- Familiar API if you've worked with jQuery before
- Stable and mature

**Cons:**
- Heavier than newer alternatives
- Not as performant with large lists

### 3. interact.js
**Pros:**
- Lightweight and performant
- Good support for mobile gestures
- Modular structure

**Cons:**
- Different programming model than jQuery

## Implementation Approach

### Design Logic

1. **Container Structure:**
   - Unassigned students container (source)
   - Group containers (targets)
   - Allow transfers between all containers

2. **Data Flow:**
   - Client-side: Track moves in a change set
   - Server-side: Apply changes as a batch operation 
   - Push to Canvas API once changes are confirmed

3. **UI/UX Considerations:**
   - Visual feedback during drag operations
   - Confirmation dialogs for bulk operations
   - Progress indicators during sync

### Implementation Steps

1. **Enhance Templates:**
   ```html
   <!-- Add drag-and-drop attributes to student items -->
   <div class="student-item" draggable="true" data-student-id="{{ student.id }}">
     {{ student.full_name }}
   </div>
   
   <!-- Make groups droppable -->
   <div class="group-container" data-group-id="{{ group.id }}">
     <!-- Group content -->
   </div>
   ```

2. **JavaScript Implementation:**
   - Event tracking for drag start/end
   - AJAX endpoints for saving changes
   - Optimistic UI updates with rollback capability

3. **Backend Endpoints:**
   - `/course/<int:course_id>/group/<int:group_id>/add_student/`
   - `/course/<int:course_id>/group/<int:group_id>/remove_student/`
   - `/course/<int:course_id>/group_set/<int:category_id>/random_assign/`

4. **Canvas API Integration:**
   - Use existing `push_team_assignments_to_canvas` function
   - Add progress tracking for bulk operations

## Random Assignment Algorithm

For the random assignment feature:
1. Get all unassigned students
2. Get all groups in the category
3. Distribute students evenly using randomization
4. Update assignments in database and Canvas

## API Rate Limit Considerations

To respect Canvas API rate limits:
- Batch student assignment operations when possible
- Implement throttling for bulk operations
- Use efficient Canvas API calls to minimize requests

## Implementation Timeline

1. **Frontend Enhancements:**
   - Add drag-and-drop library integration
   - Implement visual feedback for drag operations
   - Add progress indicators

2. **Backend Endpoints:**
   - Implement API endpoints for student assignment
   - Add batch processing for assignment changes
   - Implement random assignment algorithm

3. **Testing:**
   - Unit tests for assignment logic
   - Integration tests for Canvas API interactions
   - Manual testing for drag-and-drop functionality

## Future Enhancements (Post-Phase 3)

1. Bulk import/export of group assignments
2. Group assignment templates or presets
3. Student preference-based group formation
4. Assignment validation based on Canvas rules