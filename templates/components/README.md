# GradeBench UI Components

## Styled Modal Component

The `modal.html` component provides a consistent, styled modal dialog that can be reused throughout the application. It features a colored header, rounded buttons, and customizable content.

### Usage

Include the component in your template and pass the required parameters:

```html
{% include "components/modal.html" with
   modal_id="myModal"
   title="My Modal Title"
   body="Modal content goes here"
%}
```

### Parameters

| Parameter | Description | Default | Example |
|-----------|-------------|---------|---------|
| `modal_id` | Unique ID for the modal (required) | - | `"syncCoursesModal"` |
| `title` | Modal title text (required) | - | `"Select Courses"` |
| `body` | HTML content for the modal body | - | `"<p>Select items</p>"` |
| `modal_size` | Size of the modal | - | `"lg"`, `"sm"`, or `"xl"` |
| `icon` | Font Awesome icon to show before title | - | `"refresh"` |
| `header_class` | CSS classes for header | `"bg-primary text-white"` | `"bg-success text-white"` |
| `primary_btn_text` | Text for the primary button | - | `"Save Changes"` |
| `primary_btn_id` | ID for the primary button | - | `"saveBtn"` |
| `cancel_btn_text` | Text for the cancel button | `"Close"` | `"Cancel"` |
| `hide_cancel` | Hide the cancel button | `false` | `true` |
| `show_footer_content` | Show content in footer | `false` | `true` |
| `footer_content` | HTML content for left side of footer | - | Loading spinner |

### Example

```html
<!-- Button to trigger the modal -->
<button type="button" class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#exampleModal">
  Open Modal
</button>

<!-- Include the modal component -->
{% include "components/modal.html" with
   modal_id="exampleModal"
   modal_size="lg"
   title="Example Modal"
   icon="cog"
   header_class="bg-primary text-white"
   body="<p>This is the modal content.</p>"
   primary_btn_text="Save"
   primary_btn_id="saveBtn"
%}

<!-- JavaScript to initialize and control the modal -->
<script>
document.addEventListener('DOMContentLoaded', function() {
  // Initialize the modal
  const modalElement = document.getElementById('exampleModal');
  const modal = new bootstrap.Modal(modalElement);

  // Handle the save button click
  document.getElementById('saveBtn').addEventListener('click', function() {
    // Do something
    modal.hide(); // Hide when done
  });
});
</script>
```

See `modal_example.html` for a complete example.