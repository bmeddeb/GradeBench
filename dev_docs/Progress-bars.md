# Unified Progress Bar Component

This document outlines how to use the unified progress bar component in the GradeBench application.

## 1. Overview

The progress bar component provides a standardized way to display progress for long-running operations like syncing, pushing group memberships, or other background tasks.

## 2. Files and Structure

The component consists of three main files:

- `/static/css/components/progress.css`: Styling for the progress bar
- `/static/js/progress.js`: JavaScript functionality for the progress bar
- `/templates/components/progress.html`: Reusable Django template component

## 3. Using the Component in Templates

### 3.1 Include Required Files

First, make sure to include the CSS and JavaScript files in your template:

```html
{% block extra_head %}
<link rel="stylesheet" href="{% static 'css/components/progress.css' %}">
{% endblock %}

{% block extra_js %}
<script src="{% static 'js/progress.js' %}"></script>
{% endblock %}
```

### 3.2 Add the Component to Your Template

Include the component in your template where you want the progress bar to appear:

```html
{% include "components/progress.html" with 
   id_prefix="unique-id"
   title="Operation Title" 
   context_class="primary"
%}
```

### 3.3 Component Parameters

The following parameters can be passed to the component:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| id_prefix | String | Required | Unique prefix for all HTML IDs in the component |
| show_title | Boolean | true | Whether to show the title section |
| show_details | Boolean | true | Whether to show the details section |
| title | String | "Progress" | Title text |
| context_class | String | "primary" | Bootstrap contextual class (primary, success, danger, etc.) |
| animated | Boolean | true | Whether to animate the progress bar |
| striped | Boolean | true | Whether to show stripes in the progress bar |
| height | String | "20px" | Height of the progress bar |

## 4. JavaScript Usage

### 4.1 Initialize the Progress Bar

Create an instance of the progress bar in your JavaScript:

```javascript
document.addEventListener('DOMContentLoaded', function() {
  // Create a progress bar instance
  const progressBar = window.createProgressBar('unique-id', {
    // Configuration options (optional)
    pollInterval: 1000,
    maxPollInterval: 5000,
    hideOnComplete: false,
    completedCallback: function(data) {
      // Code to run on completion
    },
    errorCallback: function(data) {
      // Code to run on error
    }
  });
  
  // Start the progress bar polling
  progressBar.start('/api/progress-endpoint/');
});
```

### 4.2 Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| pollInterval | Number | 1000 | How often to poll for updates (ms) |
| maxPollInterval | Number | 5000 | Maximum poll interval (ms) |
| autoStart | Boolean | false | Whether to start polling immediately |
| hideOnComplete | Boolean | false | Whether to hide the component when complete |
| fadeOutDelay | Number | 3000 | How long to wait before fading out (ms) |
| completedCallback | Function | null | Function to call when complete |
| errorCallback | Function | null | Function to call on error |

### 4.3 Expected API Response Format

The component expects the polled endpoint to return JSON with the following structure:

```json
{
  "status": "in_progress", // Can be: pending, in_progress, processing, completed, success, error
  "message": "Processing item 3 of 10...", // Optional message to display
  "current": 3, // Current progress count
  "total": 10, // Total items to process
  "error": "Error details" // Only present for error status
}
```

### 4.4 Methods

The progress bar instance provides the following methods:

| Method | Parameters | Description |
|--------|------------|-------------|
| start | url, data (optional) | Start polling the given URL for progress updates |
| stop | none | Stop polling for updates |
| reset | none | Reset the progress bar to initial state |
| updateProgress | data | Manually update the progress with provided data |
| handleCompletion | data | Manually trigger completion state |
| handleError | data | Manually trigger error state |
| fadeOut | none | Fade out and hide the progress component |

## 5. Example Implementation

```html
<!-- In your template -->
<div class="card">
  <div class="card-header">
    <h4 class="card-title">Operation Title</h4>
  </div>
  <div class="card-body">
    {% include "components/progress.html" with
       id_prefix="operation"
       title="Operation in Progress"
       context_class="primary"
    %}

    <div class="d-flex justify-content-end mt-4">
      <button id="startBtn" class="btn btn-primary">Start Operation</button>
    </div>
  </div>
</div>

<script>
  document.addEventListener('DOMContentLoaded', function() {
    // Create progress bar instance
    const progressBar = window.createProgressBar('operation');
    
    // Set up start button
    document.getElementById('startBtn').addEventListener('click', function() {
      this.disabled = true;
      
      // Start progress tracking
      progressBar.start('/api/operation/progress/');
      
      // Start the operation
      fetch('/api/operation/start/', {
        method: 'POST',
        headers: {
          'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest'
        }
      });
    });
  });
</script>
```

## 6. Django View Example

Here's an example of a Django view that returns progress updates:

```python
class OperationProgressView(View):
    def get(self, request):
        # Get operation status from session or cache
        operation_id = request.GET.get('operation_id')
        progress = cache.get(f'operation_progress_{operation_id}', {
            'status': 'pending',
            'current': 0,
            'total': 0,
            'message': 'Operation starting...'
        })
        
        return JsonResponse(progress)
```

## 7. Benefits of This Approach

1. Consistent UI/UX: All progress indicators have the same look and behavior
2. Accessibility: Proper ARIA roles and labels for screen readers
3. Maintainability: Single source of truth for progress bar code
4. Flexibility: Configurable options for different use cases
5. Reusability: Django template component approach makes it easy to include in any template
6. Separation of Concerns: HTML, CSS, and JavaScript are properly separated
7. Responsive Design: Works on mobile and desktop
8. High Contrast Support: CSS includes media queries for forced-colors mode