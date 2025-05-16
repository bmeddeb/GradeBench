# Alert Component

This document outlines how to use the alert component in the GradeBench application.

## 1. Overview

The alert component provides a standardized way to display Bootstrap 5 alert messages for notifications, warnings, errors, and other important information.

## 2. Files and Structure

The component consists of one main file:

- `/templates/components/alert.html`: Reusable Django template component

## 3. Using the Component in Templates

### 3.1 Basic Usage with Content Block

Include the alert component in your template with the basic parameters:

```html
{% include 'components/alert.html' with type="info" title="Information" %}
    {% block alert_content %}
        <p>This is an informational alert message.</p>
    {% endblock %}
```

### 3.2 Content Parameter Alternative

For simpler usage, you can also provide content as a parameter:

```html
{% with alert_content="<p>This is an informational alert message.</p>" %}
    {% include 'components/alert.html' with type="info" title="Information" content=alert_content %}
{% endwith %}
```

### 3.3 Component Parameters

The following parameters can be passed to the component:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| type | String | info | Bootstrap contextual class (info, success, warning, danger) |
| title | String | None | Title displayed in the alert header |
| icon | String | None | Font Awesome icon class (without 'fa-' prefix) |
| dismissible | Boolean | false | Whether the alert can be dismissed with a close button |
| content | String | None | HTML content for the alert (alternative to using block) |

## 4. Alert Types

Bootstrap 5 provides several contextual classes for different types of alerts:

| Type | Color | Typical Use Case |
|------|-------|------------------|
| primary | Blue | Primary actions or information |
| secondary | Gray | Secondary information |
| success | Green | Success messages or confirmations |
| danger | Red | Error messages or critical warnings |
| warning | Yellow | Warning messages or cautions |
| info | Light blue | Informational messages |
| light | White | Low-emphasis alerts |
| dark | Dark gray | High-emphasis dark alerts |

## 5. Examples

### 5.1 Success Alert with Icon

```html
{% include 'components/alert.html' with type="success" title="Success" icon="check-circle" %}
    {% block alert_content %}
        <p>The operation completed successfully!</p>
        <p class="mb-0">You can now proceed to the next step.</p>
    {% endblock %}
```

### 5.2 Danger Alert with Dismissible Button

```html
{% include 'components/alert.html' with type="danger" title="Error" icon="exclamation-circle" dismissible=True %}
    {% block alert_content %}
        <p>An error occurred while processing your request.</p>
        <p class="mb-0">Please try again later or contact support if the problem persists.</p>
    {% endblock %}
```

### 5.3 Warning Alert with Links

```html
{% include 'components/alert.html' with type="warning" title="Warning" icon="exclamation-triangle" %}
    {% block alert_content %}
        <p>Your subscription will expire in 5 days.</p>
        <hr>
        <p class="mb-0">Please <a href="#" class="alert-link">renew your subscription</a> to avoid service interruption.</p>
    {% endblock %}
```

### 5.4 Info Alert with List

```html
{% include 'components/alert.html' with type="info" title="Getting Started" icon="info-circle" %}
    {% block alert_content %}
        <p>Follow these steps to complete your profile:</p>
        <ul>
            <li>Upload a profile picture</li>
            <li>Fill out your contact information</li>
            <li>Set your notification preferences</li>
            <li>Complete the onboarding tutorial</li>
        </ul>
    {% endblock %}
```

### 5.5 Alert with Content Parameter

```html
{% with alert_message="<p>Your password has been reset successfully. You can now <a href='/login' class='alert-link'>log in</a> with your new password.</p>" %}
    {% include 'components/alert.html' with 
       type="success" 
       title="Password Reset" 
       icon="check-circle" 
       content=alert_message 
    %}
{% endwith %}
```

## 6. Handling Alert Events

If you use dismissible alerts, you may want to handle the dismiss event with JavaScript:

```javascript
// Get the alert element
const alertElement = document.querySelector('.alert')

// Initialize Bootstrap alert
const alert = new bootstrap.Alert(alertElement)

// Handle alert close event
alertElement.addEventListener('closed.bs.alert', function () {
  // Code to run after the alert has been closed
  console.log('Alert was closed')
})
```

## 7. Best Practices

1. **Color Consistency**: Use the appropriate contextual class for the type of message
   - Success (green) for successful operations
   - Danger (red) for errors and critical issues
   - Warning (yellow) for cautions and non-critical issues
   - Info (blue) for general information
   
2. **Icons**: Include icons to enhance visual recognition
   - check-circle for success messages
   - exclamation-circle for error messages
   - exclamation-triangle for warnings
   - info-circle for informational messages

3. **Dismissible Alerts**: Make non-critical alerts dismissible, but keep important error messages visible

4. **Alert Placement**: Place alerts where they're most visible and contextually relevant
   - At the top of forms for form-related messages
   - At the top of the page for system-wide messages
   - Near the relevant content for context-specific messages
   
5. **Content Structure**: For complex alerts, use paragraphs, lists, and dividers to structure content

6. **Accessibility**: Ensure alerts are accessible with proper ARIA roles and attributes