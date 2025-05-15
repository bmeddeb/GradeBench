# Modal Component

This document outlines how to use the modal component in the GradeBench application.

## 1. Overview

The modal component provides a standardized way to display Bootstrap 5 modal dialogs for collecting user input, showing detailed information, or confirming actions.

## 2. Files and Structure

The component consists of one main file:

- `/templates/components/modal.html`: Reusable Django template component

## 3. Using the Component in Templates

### 3.1 Basic Usage

Include the modal component in your template with the required parameters:

```html
{% include 'components/modal.html' with id="example-modal" title="Modal Title" %}
    {% block modal_body %}
        <p>This is the modal content.</p>
    {% endblock %}
```

### 3.2 Content Parameter Alternative

For simpler usage, you can also provide content as a parameter instead of using a block:

```html
{% with modal_content="<p>This is the modal content.</p>" %}
    {% include 'components/modal.html' with id="example-modal" title="Modal Title" content=modal_content %}
{% endwith %}
```

### 3.3 Component Parameters

The following parameters can be passed to the component:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| id | String | Required | Unique identifier for the modal |
| title | String | Required | Modal title displayed in the header |
| size | String | None | Modal size: 'sm', 'lg', or 'xl' |
| close_text | String | None | Text for the close button |
| save_text | String | None | Text for the primary action button |
| save_id | String | None | ID for the primary action button |
| fullscreen | Boolean | false | Whether the modal should be fullscreen |
| centered | Boolean | false | Whether to vertically center the modal |
| scrollable | Boolean | false | Whether the modal body should be scrollable |
| backdrop | String | None | Controls modal backdrop: 'static' or 'true' |
| keyboard | Boolean | true | Whether Escape key closes the modal |
| content | String | None | HTML content for the modal body (alternative to block) |

## 4. JavaScript Integration

### 4.1 Showing the Modal

```javascript
// Initialize and show the modal
const myModal = new bootstrap.Modal(document.getElementById('example-modal'))
myModal.show()
```

### 4.2 Handling Modal Events

```javascript
// Get the modal element
const modalElement = document.getElementById('example-modal')

// Event listeners for Bootstrap modal events
modalElement.addEventListener('show.bs.modal', function () {
  // Code to run when modal is about to be shown
})

modalElement.addEventListener('shown.bs.modal', function () {
  // Code to run when modal has been fully shown
})

modalElement.addEventListener('hide.bs.modal', function () {
  // Code to run when modal is about to be hidden
})

modalElement.addEventListener('hidden.bs.modal', function () {
  // Code to run when modal has been fully hidden
})
```

### 4.3 Handling Save Button Clicks

```javascript
// Handle save button click
document.getElementById('saveButton').addEventListener('click', function() {
  // Perform save action
  
  // Close the modal programmatically
  const myModal = bootstrap.Modal.getInstance(document.getElementById('example-modal'))
  myModal.hide()
})
```

## 5. Examples

### 5.1 Confirmation Modal

```html
{% include 'components/modal.html' with 
   id="confirm-delete" 
   title="Confirm Deletion" 
   close_text="Cancel" 
   save_text="Delete" 
   save_id="confirmDeleteBtn" 
%}
    {% block modal_body %}
        <p>Are you sure you want to delete this item? This action cannot be undone.</p>
    {% endblock %}
```

```javascript
// Show the confirmation modal when delete button is clicked
document.getElementById('deleteBtn').addEventListener('click', function() {
  const modal = new bootstrap.Modal(document.getElementById('confirm-delete'))
  modal.show()
})

// Handle confirm delete button
document.getElementById('confirmDeleteBtn').addEventListener('click', function() {
  // Perform delete action
  deleteItem(itemId)
  
  // Hide the modal
  const modal = bootstrap.Modal.getInstance(document.getElementById('confirm-delete'))
  modal.hide()
})
```

### 5.2 Form Modal

```html
{% include 'components/modal.html' with 
   id="edit-user" 
   title="Edit User" 
   close_text="Cancel" 
   save_text="Save Changes" 
   save_id="saveUserBtn" 
   size="lg" 
%}
    {% block modal_body %}
        <form id="userForm">
            <div class="mb-3">
                <label for="userName" class="form-label">Name</label>
                <input type="text" class="form-control" id="userName" name="name">
            </div>
            <div class="mb-3">
                <label for="userEmail" class="form-label">Email</label>
                <input type="email" class="form-control" id="userEmail" name="email">
            </div>
            <div class="mb-3">
                <label for="userRole" class="form-label">Role</label>
                <select class="form-select" id="userRole" name="role">
                    <option value="student">Student</option>
                    <option value="instructor">Instructor</option>
                    <option value="admin">Administrator</option>
                </select>
            </div>
        </form>
    {% endblock %}
```

### 5.3 Static Backdrop Modal

```html
{% include 'components/modal.html' with 
   id="processing-modal" 
   title="Processing" 
   backdrop="static" 
   keyboard=False 
   centered=True 
%}
    {% block modal_body %}
        <div class="text-center py-4">
            <div class="spinner-border text-primary mb-3" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p>Please wait while we process your request. Do not close this window.</p>
        </div>
    {% endblock %}
```

### 5.4 Fullscreen Modal

```html
{% include 'components/modal.html' with 
   id="preview-document" 
   title="Document Preview" 
   fullscreen=True 
   close_text="Close" 
%}
    {% block modal_body %}
        <div class="document-preview">
            <!-- Document preview content -->
        </div>
    {% endblock %}
```

## 6. Best Practices

1. **Unique IDs**: Always provide unique IDs for modals to avoid conflicts
2. **Static Backdrop**: Use `backdrop="static"` for operations that shouldn't be interrupted
3. **Form Validation**: Validate forms before closing modals when collecting important data
4. **Loading States**: Disable buttons during async operations
5. **Accessibility**: Ensure modals are keyboard navigable and screen-reader friendly
6. **Mobile Considerations**: Test modals on mobile devices; consider using fullscreen for complex forms
7. **Error Handling**: Display errors within the modal when possible rather than closing it