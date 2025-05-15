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