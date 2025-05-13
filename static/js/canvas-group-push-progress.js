/**
 * Canvas Group Memberships Push Progress Tracking
 *
 * This JavaScript file provides functionality to track and display the
 * progress of Canvas group memberships push operations.
 */

// Use an immediately invoked function expression (IIFE) to avoid global variable conflicts
(function() {
    // Private variables for this module
    let isPolling = true;
    let pollInterval = 1000; // Start with 1 second
    const MAX_POLL_INTERVAL = 5000; // Max 5 seconds between polls
    
    /**
     * Start polling for progress updates
     * @param {number} courseId - The course ID for which memberships are being pushed
     */
    function checkProgress(courseId) {
        if (!isPolling) return;
        
        $.ajax({
            url: `/canvas/course/${courseId}/push_group_memberships/progress/`,
            type: 'GET',
            dataType: 'json',
            success: function(data) {
                updateProgressUI(data);
                
                // Schedule next poll with adaptive interval
                if (isPolling) {
                    // If operation is still running, maintain polling
                    if (data.status === 'completed' || data.status === 'error') {
                        // Operation finished, stop polling
                        isPolling = false;
                    } else {
                        // Gradually increase polling interval for longer operations
                        pollInterval = Math.min(pollInterval * 1.2, MAX_POLL_INTERVAL);
                    }
                    setTimeout(() => checkProgress(courseId), pollInterval);
                }
            },
            error: function(xhr, status, error) {
                console.error('Error fetching progress:', error);
                // Keep polling despite errors, with increasing interval
                pollInterval = Math.min(pollInterval * 1.5, MAX_POLL_INTERVAL);
                setTimeout(() => checkProgress(courseId), pollInterval);
            }
        });
    }
    
    /**
     * Update the UI with progress data
     * @param {Object} data - The progress data from the server
     */
    function updateProgressUI(data) {
        // Update progress bar
        const percent = data.total > 0 ? Math.floor((data.current / data.total) * 100) : 0;
        $('#progressBar').css('width', percent + '%').attr('aria-valuenow', percent).text(percent + '%');
        
        // Update message
        $('#progressMessage').text(data.message || 'Processing...');
        
        // Update counts
        $('#currentCount').text(data.current || 0);
        $('#totalCount').text(data.total || 0);
        
        // Handle completed state
        if (data.status === 'completed') {
            $('#successMessage').text(data.message || 'Operation completed successfully!');
            $('#operationComplete').show();
            $('#progressDetails').hide();
            // Change progress bar style
            $('#progressBar').removeClass('progress-bar-animated').addClass('bg-success');
        }
        
        // Handle error state
        if (data.status === 'error') {
            $('#errorMessage').text(data.message || 'An error occurred during the operation.');
            if (data.error) {
                $('#errorMessage').append('<br><small class="text-muted">' + data.error + '</small>');
            }
            $('#operationError').show();
            $('#progressDetails').hide();
            // Change progress bar style
            $('#progressBar').removeClass('progress-bar-animated').addClass('bg-danger');
        }
    }
    
    // Expose relevant functions to the global scope
    window.pushMembershipsProgress = {
        startTracking: function(courseId) {
            isPolling = true;
            pollInterval = 1000;
            checkProgress(courseId);
        },
        stopTracking: function() {
            isPolling = false;
        }
    };
})();