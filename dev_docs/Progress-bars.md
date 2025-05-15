 Unified Progress Bar Component Design

  Here's my design for a unified progress bar component for the Canvas app:

  1. File Structure

  /static/
    /css/
      /components/
        progress.css     # Unified progress bar styles
    /js/
      progress.js        # Core progress bar functionality
    /templates/
      components/
        progress.html    # Reusable Django template component

  2. Template Component (progress.html)

  {% comment %}
  Progress Bar Component
  Parameters:
  - id_prefix: String (required) - Prefix for all HTML IDs
  - show_title: Boolean (default: true) - Whether to show the title section
  - show_details: Boolean (default: true) - Whether to show the details section
  - title: String (default: "Progress") - Title text
  - context_class: String (default: "primary") - Bootstrap contextual class (primary, success, danger, etc.)
  - animated: Boolean (default: true) - Whether to animate the progress bar
  - striped: Boolean (default: true) - Whether to show stripes in the progress bar
  - height: String (default: "20px") - Height of the progress bar
  {% endcomment %}

  <div id="{{ id_prefix }}-container" class="progress-component mb-3">
    {% if show_title %}
    <div id="{{ id_prefix }}-header" class="progress-header mb-2">
      <div class="d-flex align-items-center">
        <i id="{{ id_prefix }}-icon" class="fa fa-sync-alt me-2 {% if animated %}fa-spin{% endif %}"></i>
        <h6 id="{{ id_prefix }}-title" class="mb-0">{{ title|default:"Progress" }}</h6>
      </div>
      <p id="{{ id_prefix }}-message" class="progress-message mb-1 mt-1">Initializing...</p>
    </div>
    {% endif %}

    <div class="progress" style="height: {{ height|default:'20px' }};">
      <div id="{{ id_prefix }}-bar" 
           class="progress-bar bg-{{ context_class|default:'primary' }} 
                  {% if striped %}progress-bar-striped{% endif %} 
                  {% if animated %}progress-bar-animated{% endif %}"
           role="progressbar" 
           aria-valuenow="0" 
           aria-valuemin="0" 
           aria-valuemax="100" 
           style="width: 0%">
        <span id="{{ id_prefix }}-percentage">0%</span>
      </div>
    </div>

    {% if show_details %}
    <div id="{{ id_prefix }}-details" class="progress-details mt-1 d-flex justify-content-between">
      <span id="{{ id_prefix }}-status" class="progress-status">Waiting to start...</span>
      <span class="progress-counts">
        <span id="{{ id_prefix }}-current">0</span> of <span id="{{ id_prefix }}-total">0</span>
      </span>
    </div>
    {% endif %}

    <div id="{{ id_prefix }}-success" class="alert alert-success mt-3" style="display: none;" role="alert">
      <h5 class="alert-heading"><i class="fa fa-check-circle me-2"></i>Success</h5>
      <p id="{{ id_prefix }}-success-message" class="mb-0">Operation completed successfully!</p>
    </div>

    <div id="{{ id_prefix }}-error" class="alert alert-danger mt-3" style="display: none;" role="alert">
      <h5 class="alert-heading"><i class="fa fa-exclamation-circle me-2"></i>Error</h5>
      <p id="{{ id_prefix }}-error-message" class="mb-0">An error occurred.</p>
      <div id="{{ id_prefix }}-error-details" class="small mt-2" style="display: none;"></div>
    </div>
  </div>

  3. CSS Component (progress.css)

  /**
   * GradeBench Progress Component Styles
   * Unified progress bar styling with accessibility enhancements
   */

  /* Progress Container */
  .progress-component {
    background-color: var(--gb-light);
    border-radius: var(--gb-border-radius-sm);
    padding: var(--gb-space-md);
    border: 1px solid var(--gb-border-color);
    transition: all var(--gb-transition-normal);
  }

  /* Progress Header */
  .progress-header {
    display: flex;
    flex-direction: column;
  }

  .progress-header i {
    color: var(--gb-primary);
    font-size: 1.1rem;
  }

  .progress-header h6 {
    font-weight: var(--gb-font-weight-bold);
    color: var(--gb-dark);
  }

  /* Progress Message */
  .progress-message {
    color: var(--gb-text-muted);
    font-size: 0.95rem;
  }

  /* Progress Bar - Enhanced for accessibility */
  .progress {
    background-color: var(--gb-light-gray);
    border-radius: var(--gb-border-radius-pill);
    overflow: hidden;
    box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.1);
  }

  .progress-bar {
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
    transition: width 0.3s ease;
    font-weight: var(--gb-font-weight-bold);
    font-size: 0.85rem;
  }

  /* Progress bar sizes */
  .progress.progress-sm {
    height: 10px;
  }

  .progress.progress-lg {
    height: 25px;
  }

  /* Progress Details */
  .progress-details {
    font-size: 0.875rem;
    color: var(--gb-text-muted);
  }

  .progress-status {
    font-style: italic;
  }

  .progress-counts {
    font-weight: var(--gb-font-weight-semibold);
  }

  /* State-specific styles */
  .progress-component.is-completed .progress-header i {
    color: var(--gb-success);
  }

  .progress-component.is-error .progress-header i {
    color: var(--gb-danger);
  }

  /* Animation for the completed state */
  @keyframes progress-success-pulse {
    0% { box-shadow: 0 0 0 0 rgba(var(--gb-success-rgb), 0.4); }
    70% { box-shadow: 0 0 0 10px rgba(var(--gb-success-rgb), 0); }
    100% { box-shadow: 0 0 0 0 rgba(var(--gb-success-rgb), 0); }
  }

  .progress-component.is-completed {
    animation: progress-success-pulse 2s 1;
  }

  /* High contrast mode support */
  @media (forced-colors: active) {
    .progress-bar {
      /* Force high contrast when needed */
      border: 1px solid CanvasText;
    }

    .progress-component.is-completed .progress-bar {
      background-color: Highlight !important;
    }

    .progress-component.is-error .progress-bar {
      background-color: Mark !important;
    }
  }

  4. JavaScript Component (progress.js)

  /**
   * Unified Progress Bar Component
   * 
   * This JavaScript module provides a standardized way to create and manage
   * progress bars across the Canvas app for tracking operations like syncing,
   * pushing group memberships, and other long-running processes.
   */

  // Use an immediately invoked function expression (IIFE) for encapsulation
  (function() {
    /**
     * ProgressBar class for managing progress UI and state
     */
    class ProgressBar {
      /**
       * Create a new ProgressBar instance
       * 
       * @param {string} idPrefix - Prefix for HTML IDs associated with this progress bar
       * @param {Object} options - Configuration options
       */
      constructor(idPrefix, options = {}) {
        // Store the ID prefix for accessing DOM elements
        this.idPrefix = idPrefix;

        // Default options
        this.options = {
          pollInterval: 1000,      // How often to poll for updates (ms)
          maxPollInterval: 5000,   // Maximum poll interval (ms)
          autoStart: false,        // Whether to start polling immediately
          hideOnComplete: false,   // Whether to hide the component when complete
          fadeOutDelay: 3000,      // How long to wait before fading out (ms)
          completedCallback: null, // Function to call when complete
          errorCallback: null,     // Function to call on error
          ...options               // Override with provided options
        };

        // Initialize internal state
        this.state = {
          isPolling: false,
          currentInterval: this.options.pollInterval,
          pollTimer: null,
          current: 0,
          total: 0
        };

        // Find DOM elements
        this.elements = {
          container: document.getElementById(`${idPrefix}-container`),
          bar: document.getElementById(`${idPrefix}-bar`),
          title: document.getElementById(`${idPrefix}-title`),
          message: document.getElementById(`${idPrefix}-message`),
          icon: document.getElementById(`${idPrefix}-icon`),
          status: document.getElementById(`${idPrefix}-status`),
          percentage: document.getElementById(`${idPrefix}-percentage`),
          current: document.getElementById(`${idPrefix}-current`),
          total: document.getElementById(`${idPrefix}-total`),
          success: document.getElementById(`${idPrefix}-success`),
          successMessage: document.getElementById(`${idPrefix}-success-message`),
          error: document.getElementById(`${idPrefix}-error`),
          errorMessage: document.getElementById(`${idPrefix}-error-message`),
          errorDetails: document.getElementById(`${idPrefix}-error-details`)
        };

        // Start polling if autoStart is set
        if (this.options.autoStart) {
          this.start();
        }
      }

      /**
       * Start polling for progress updates
       * 
       * @param {string} url - URL to poll for progress updates
       * @param {Object} data - Optional data to include in the request
       */
      start(url, data = {}) {
        // Store URL and data
        this.pollUrl = url;
        this.pollData = data;

        // Set polling state
        this.state.isPolling = true;
        this.state.currentInterval = this.options.pollInterval;

        // Show the container
        if (this.elements.container) {
          this.elements.container.style.display = 'block';
        }

        // Reset state
        this.reset();

        // Start polling
        this.poll();
      }

      /**
       * Stop polling for progress updates
       */
      stop() {
        this.state.isPolling = false;
        if (this.state.pollTimer) {
          clearTimeout(this.state.pollTimer);
          this.state.pollTimer = null;
        }
      }

      /**
       * Reset the progress bar to initial state
       */
      reset() {
        // Reset progress bar
        if (this.elements.bar) {
          this.elements.bar.style.width = '0%';
          this.elements.bar.setAttribute('aria-valuenow', 0);
          this.elements.bar.classList.remove('bg-success', 'bg-danger');
          this.elements.bar.classList.add('bg-primary', 'progress-bar-animated');
        }

        // Reset messages
        if (this.elements.message) this.elements.message.textContent = 'Initializing...';
        if (this.elements.status) this.elements.status.textContent = 'Waiting to start...';
        if (this.elements.percentage) this.elements.percentage.textContent = '0%';
        if (this.elements.current) this.elements.current.textContent = '0';
        if (this.elements.total) this.elements.total.textContent = '0';

        // Hide completion/error messages
        if (this.elements.success) this.elements.success.style.display = 'none';
        if (this.elements.error) this.elements.error.style.display = 'none';

        // Reset container classes
        if (this.elements.container) {
          this.elements.container.classList.remove('is-completed', 'is-error');
        }

        // Reset icon
        if (this.elements.icon) {
          this.elements.icon.className = 'fa fa-sync-alt me-2 fa-spin';
        }
      }

      /**
       * Poll for progress updates
       */
      poll() {
        if (!this.state.isPolling || !this.pollUrl) return;

        // Build fetch options
        const options = {
          method: 'GET',
          headers: {
            'X-Requested-With': 'XMLHttpRequest'
          }
        };

        // Make the request
        fetch(this.pollUrl, options)
          .then(response => {
            if (!response.ok) {
              throw new Error(`Network response error: ${response.status}`);
            }
            return response.json();
          })
          .then(data => {
            // Update the UI with the progress data
            this.update(data);

            // Check if the operation is completed or failed
            if (data.status === 'completed' || data.status === 'success') {
              this.handleCompletion(data);
            } else if (data.status === 'error') {
              this.handleError(data);
            } else {
              // Continue polling with adaptive interval
              this.continuePolling();
            }
          })
          .catch(error => {
            console.error('Error polling for progress:', error);

            // Continue polling but with an increased interval
            this.state.currentInterval = Math.min(
              this.state.currentInterval * 1.5,
              this.options.maxPollInterval
            );

            this.continuePolling();
          });
      }

      /**
       * Schedule the next poll
       */
      continuePolling() {
        if (this.state.isPolling) {
          this.state.pollTimer = setTimeout(() => {
            this.poll();
          }, this.state.currentInterval);
        }
      }

      /**
       * Update the UI with progress data
       * 
       * @param {Object} data - Progress data from the server
       */
      update(data) {
        // Store current and total
        if (data.current !== undefined) this.state.current = data.current;
        if (data.total !== undefined) this.state.total = data.total;

        // Calculate percentage
        const percent = this.state.total > 0
          ? Math.min(Math.floor((this.state.current / this.state.total) * 100), 100)
          : 0;

        // Update progress bar
        if (this.elements.bar) {
          this.elements.bar.style.width = `${percent}%`;
          this.elements.bar.setAttribute('aria-valuenow', percent);
        }

        // Update percentage text
        if (this.elements.percentage) {
          this.elements.percentage.textContent = `${percent}%`;
        }

        // Update message
        if (this.elements.message && data.message) {
          this.elements.message.textContent = data.message;
        }

        // Update status
        if (this.elements.status) {
          let statusText = '';

          switch (data.status) {
            case 'pending':
              statusText = 'Preparing...';
              break;
            case 'in_progress':
              statusText = 'In progress...';
              break;
            case 'processing':
              statusText = 'Processing...';
              break;
            case 'completed':
            case 'success':
              statusText = 'Completed';
              break;
            case 'error':
              statusText = 'Error';
              break;
            default:
              statusText = data.status || 'Processing...';
          }

          this.elements.status.textContent = statusText;
        }

        // Update counts
        if (this.elements.current) {
          this.elements.current.textContent = this.state.current;
        }

        if (this.elements.total) {
          this.elements.total.textContent = this.state.total;
        }
      }

      /**
       * Handle successful completion
       * 
       * @param {Object} data - Completion data from the server
       */
      handleCompletion(data) {
        // Stop polling
        this.stop();

        // Update progress bar to show completion
        if (this.elements.bar) {
          this.elements.bar.style.width = '100%';
          this.elements.bar.setAttribute('aria-valuenow', 100);
          this.elements.bar.classList.remove('bg-primary', 'progress-bar-animated');
          this.elements.bar.classList.add('bg-success');
        }

        // Update container classes
        if (this.elements.container) {
          this.elements.container.classList.add('is-completed');
        }

        // Update icon
        if (this.elements.icon) {
          this.elements.icon.className = 'fa fa-check-circle me-2';
        }

        // Show success message
        if (this.elements.success) {
          this.elements.success.style.display = 'block';

          if (this.elements.successMessage && data.message) {
            this.elements.successMessage.textContent = data.message;
          }
        }

        // Call the completion callback if defined
        if (typeof this.options.completedCallback === 'function') {
          this.options.completedCallback(data);
        }

        // Handle auto-hide if enabled
        if (this.options.hideOnComplete) {
          setTimeout(() => {
            this.fadeOut();
          }, this.options.fadeOutDelay);
        }
      }

      /**
       * Handle error state
       * 
       * @param {Object} data - Error data from the server
       */
      handleError(data) {
        // Stop polling
        this.stop();

        // Update progress bar to show error
        if (this.elements.bar) {
          this.elements.bar.classList.remove('bg-primary', 'progress-bar-animated');
          this.elements.bar.classList.add('bg-danger');
        }

        // Update container classes
        if (this.elements.container) {
          this.elements.container.classList.add('is-error');
        }

        // Update icon
        if (this.elements.icon) {
          this.elements.icon.className = 'fa fa-exclamation-circle me-2';
        }

        // Show error message
        if (this.elements.error) {
          this.elements.error.style.display = 'block';

          if (this.elements.errorMessage) {
            this.elements.errorMessage.textContent = data.message || 'An error occurred.';
          }

          if (this.elements.errorDetails && data.error) {
            this.elements.errorDetails.style.display = 'block';
            this.elements.errorDetails.textContent = data.error;
          }
        }

        // Call the error callback if defined
        if (typeof this.options.errorCallback === 'function') {
          this.options.errorCallback(data);
        }
      }

      /**
       * Fade out the progress component
       */
      fadeOut() {
        if (this.elements.container) {
          this.elements.container.style.opacity = '1';

          let opacity = 1;
          const fadeInterval = setInterval(() => {
            if (opacity <= 0.1) {
              clearInterval(fadeInterval);
              this.elements.container.style.display = 'none';
              this.elements.container.style.opacity = '1';
            } else {
              opacity -= 0.1;
              this.elements.container.style.opacity = opacity;
            }
          }, 50);
        }
      }

      /**
       * Manually update the progress with provided data
       * 
       * @param {Object} data - Progress data to update the UI with
       */
      updateProgress(data) {
        this.update(data);
      }
    }

    // Expose ProgressBar class to the global scope
    window.GradeBenchProgress = ProgressBar;

    // Also expose a helper function to create progress bars
    window.createProgressBar = (idPrefix, options) => {
      return new ProgressBar(idPrefix, options);
    };
  })();

  5. Usage Example in a Template

  {% extends 'canvas/base.html' %}
  {% load static %}

  {% block title %}Syncing Canvas Groups{% endblock %}

  {% block extra_head %}
  <link rel="stylesheet" href="{% static 'css/components/progress.css' %}">
  {% endblock %}

  {% block canvas_content %}
  <div class="card">
    <div class="card-header">
      <h4 class="card-title">Canvas Groups Synchronization</h4>
      <p class="card-category">Sync groups with Canvas</p>
    </div>
    <div class="card-body">
      <!-- Include progress component -->
      {% include "components/progress.html" with
         id_prefix="sync"
         title="Synchronizing Groups"
         context_class="primary"
      %}

      <div class="d-flex justify-content-end mt-4" id="action-buttons">
        <button id="cancelBtn" class="btn btn-secondary btn-round me-2" disabled>Cancel</button>
        <button id="startBtn" class="btn btn-primary btn-round">Start Sync</button>
      </div>
    </div>
  </div>
  {% endblock %}

  {% block extra_js %}
  <script src="{% static 'js/progress.js' %}"></script>
  <script>
    document.addEventListener('DOMContentLoaded', function() {
      // Get course ID from meta tag
      const courseId = document.querySelector('meta[name="course-id"]').content;

      // Create a progress bar instance
      const progressBar = window.createProgressBar('sync', {
        pollInterval: 1000,
        maxPollInterval: 5000,
        hideOnComplete: false,
        completedCallback: function(data) {
          // Enable refresh button
          document.getElementById('startBtn').textContent = 'Refresh Page';
          document.getElementById('startBtn').classList.remove('btn-primary');
          document.getElementById('startBtn').classList.add('btn-success');
          document.getElementById('startBtn').disabled = false;
          document.getElementById('startBtn').addEventListener('click', function() {
            window.location.reload();
          });
        },
        errorCallback: function(data) {
          // Enable retry button
          document.getElementById('startBtn').textContent = 'Retry';
          document.getElementById('startBtn').disabled = false;
        }
      });

      // Set up start button
      document.getElementById('startBtn').addEventListener('click', function() {
        // Disable buttons
        this.disabled = true;

        // Start progress tracking
        progressBar.start(`/canvas/course/${courseId}/sync_groups/progress/`);

        // Start the sync operation
        fetch(`/canvas/course/${courseId}/sync_groups/`, {
          method: 'POST',
          headers: {
            'X-CSRFToken': getCSRFToken(),
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
          }
        }).catch(error => {
          console.error('Error starting sync:', error);
        });
      });

      // Helper function to get CSRF token
      function getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
      }
    });
  </script>
  {% endblock %}

  6. Benefits of This Approach

  1. Consistent UI/UX: All progress indicators will have the same look and behavior
  2. Accessibility: Proper ARIA roles and labels for screen readers
  3. Maintainability: Single source of truth for progress bar code
  4. Flexibility: Configurable options for different use cases
  5. Reusability: Django template component approach makes it easy to include in any template
  6. Separation of Concerns: HTML, CSS, and JavaScript are properly separated
  7. Responsive Design: Works on mobile and desktop
  8. High Contrast Support: CSS includes media queries for forced-colors mode

  This component also improves the current implementation by:
  - Adding better error handling
  - Providing detailed status information
  - Offering customization options
  - Enhancing visual feedback
  - Standardizing the API for different operations
