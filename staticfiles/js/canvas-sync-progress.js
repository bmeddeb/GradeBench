/**
 * Canvas Sync Progress Tracking
 * 
 * This JavaScript file provides functionality to track and display the 
 * progress of Canvas API synchronization operations.
 */

// Sync Progress UI Elements
let syncProgressModal = null;
let syncProgressBar = null;
let syncProgressText = null;
let syncProgressStatus = null;
let courseIdParam = '';

/**
 * Initialize the progress modal and UI elements
 */
function initSyncProgressUI() {
    // If the modal already exists, remove it so we create a fresh one without the "View details" button
    const existingModal = document.getElementById('syncProgressModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Create modal HTML - Removed "View Details" button as requested
    const modalHtml = `
    <div class="modal fade" id="syncProgressModal" tabindex="-1" aria-labelledby="syncProgressModalLabel" aria-hidden="true">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="syncProgressModalLabel">Syncing Canvas Data</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <div class="progress mb-3">
                        <div id="syncProgressBar" class="progress-bar progress-bar-striped progress-bar-animated"
                            role="progressbar" style="width: 0%;" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100">0%</div>
                    </div>
                    <p id="syncProgressText" class="mb-2">Starting sync...</p>
                    <p id="syncProgressStatus" class="text-muted small">Initializing...</p>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary btn-block w-100" data-bs-dismiss="modal">Close</button>
                </div>
            </div>
        </div>
    </div>`;
    
    // Append modal to body
    const modalContainer = document.createElement('div');
    modalContainer.innerHTML = modalHtml;
    document.body.appendChild(modalContainer);
    
    // Initialize modal and UI elements
    syncProgressModal = new bootstrap.Modal(document.getElementById('syncProgressModal'));
    syncProgressBar = document.getElementById('syncProgressBar');
    syncProgressText = document.getElementById('syncProgressText');
    syncProgressStatus = document.getElementById('syncProgressStatus');

    // Remove view details button if it somehow still exists (for backward compatibility)
    const viewDetailsBtn = document.getElementById('viewDetailsBtn');
    if (viewDetailsBtn) {
        viewDetailsBtn.remove();
    }
}

/**
 * Poll for sync progress updates
 * @param {number|null} courseId - The course ID being synced, or null for all courses
 */
function pollSyncProgress(courseId = null) {
    courseIdParam = courseId || '';
    const url = `/canvas/sync_progress/?course_id=${courseIdParam}`;
    
    // Count for handling empty responses
    let emptyResponseCount = 0;
    const MAX_EMPTY_RESPONSES = 5;
    
    const pollInterval = setInterval(() => {
        fetch(url)
            .then(response => response.json())
            .then(data => {
                // Check if we have valid progress data
                if (!data || Object.keys(data).length === 0) {
                    emptyResponseCount++;
                    console.log(`Empty progress data received. Count: ${emptyResponseCount}`);
                    
                    // If we've received too many empty responses, assume something went wrong
                    if (emptyResponseCount >= MAX_EMPTY_RESPONSES) {
                        clearInterval(pollInterval);
                        updateProgressUI({
                            status: 'error',
                            message: 'Progress tracking failed',
                            error: 'No progress data received from server',
                            current: 0,
                            total: 1
                        });
                        syncCompleted({
                            status: 'error',
                            message: 'Progress tracking failed',
                            error: 'No progress data received from server'
                        });
                    }
                    return;
                }
                
                // Reset counter when we receive valid data
                emptyResponseCount = 0;
                updateProgressUI(data);
                
                // If the sync is complete or failed, stop polling
                if (data.status === 'completed' || data.status === 'error') {
                    clearInterval(pollInterval);
                    syncCompleted(data);
                }
            })
            .catch(error => {
                console.error('Error checking sync progress:', error);
                // Don't stop polling on errors - the server might just be busy
                emptyResponseCount++;
                
                if (emptyResponseCount >= MAX_EMPTY_RESPONSES) {
                    clearInterval(pollInterval);
                    updateProgressUI({
                        status: 'error',
                        message: 'Progress tracking failed',
                        error: 'Server communication error',
                        current: 0,
                        total: 1
                    });
                    syncCompleted({
                        status: 'error',
                        message: 'Progress tracking failed',
                        error: 'Server communication error'
                    });
                }
            });
    }, 1000); // Poll every second
    
    return pollInterval;
}

/**
 * Update the progress UI based on the progress data
 * @param {Object} data - The progress data from the server
 */
function updateProgressUI(data) {
    if (!data || Object.keys(data).length === 0) {
        // No progress data yet
        return;
    }
    
    // Calculate percentage
    let percentage = 0;
    if (data.total > 0) {
        percentage = Math.round((data.current / data.total) * 100);
    }
    
    // Update progress bar
    syncProgressBar.style.width = `${percentage}%`;
    syncProgressBar.setAttribute('aria-valuenow', percentage);
    syncProgressBar.innerText = `${percentage}%`;
    
    // Update progress text and status
    syncProgressText.innerText = data.message || 'Syncing...';
    
    // Set color based on status
    if (data.status === 'error') {
        syncProgressBar.classList.remove('bg-primary', 'bg-success');
        syncProgressBar.classList.add('bg-danger');
    } else if (data.status === 'completed') {
        syncProgressBar.classList.remove('bg-primary', 'bg-danger');
        syncProgressBar.classList.add('bg-success');
    } else {
        syncProgressBar.classList.remove('bg-success', 'bg-danger');
        syncProgressBar.classList.add('bg-primary');
    }
    
    // Update status text based on current operation
    let statusText = '';
    switch (data.status) {
        case 'pending':
            statusText = 'Preparing to sync...';
            break;
        case 'fetching_course':
            statusText = 'Fetching course information...';
            break;
        case 'fetching_enrollments':
            statusText = 'Fetching student and instructor enrollments...';
            break;
        case 'fetching_users':
            statusText = 'Fetching user details and email addresses...';
            break;
        case 'fetching_assignments':
            statusText = 'Fetching assignments...';
            break;
        case 'fetching_submissions':
            statusText = 'Fetching assignment submissions...';
            break;
        case 'processing_submissions':
            statusText = 'Processing assignment submissions...';
            break;
        case 'saving_data':
            statusText = 'Saving data to database...';
            break;
        case 'completed':
            statusText = 'Sync completed successfully!';
            break;
        case 'error':
            statusText = `Error: ${data.error || 'Unknown error'}`;
            break;
        default:
            statusText = `Status: ${data.status}`;
    }
    
    syncProgressStatus.innerText = statusText;
}

/**
 * Handle sync completion
 * @param {Object} data - The final progress data
 */
function syncCompleted(data) {
    // Change the progress bar to green or red
    if (data.status === 'completed') {
        syncProgressBar.classList.remove('progress-bar-animated');
        syncProgressText.innerText = 'Sync completed successfully!';
        
        // Show success notification if modal is closed
        if (!document.getElementById('syncProgressModal').classList.contains('show')) {
            showNotification('Sync completed successfully!', 'success');
        }
        
        // Add option to auto-refresh the page after a short delay
        setTimeout(() => {
            // Only refresh if we're still on a Canvas page
            if (window.location.pathname.includes('/canvas/')) {
                window.location.reload();
            }
        }, 1500);
    } else if (data.status === 'error') {
        syncProgressBar.classList.remove('progress-bar-animated');
        syncProgressText.innerText = 'Sync failed!';
        syncProgressStatus.innerText = data.error || 'An unknown error occurred';
        
        // Show error notification if modal is closed
        if (!document.getElementById('syncProgressModal').classList.contains('show')) {
            showNotification(`Sync failed: ${data.error || 'Unknown error'}`, 'danger');
        }
    }
}

/**
 * Start a sync operation with progress tracking
 * @param {string} url - The URL to send the sync request to
 * @param {Object} data - The data to send with the request
 * @param {number|null} courseId - The course ID being synced, or null for all courses
 */
function startSyncWithProgress(url, data, courseId = null) {
    // Initialize the progress UI
    initSyncProgressUI();
    
    // Show the progress modal
    syncProgressModal.show();
    
    // Reset progress UI
    syncProgressBar.style.width = '0%';
    syncProgressBar.setAttribute('aria-valuenow', 0);
    syncProgressBar.innerText = '0%';
    syncProgressText.innerText = 'Starting sync...';
    syncProgressStatus.innerText = 'Initializing...';
    syncProgressBar.classList.remove('bg-success', 'bg-danger');
    syncProgressBar.classList.add('bg-primary', 'progress-bar-animated');
    
    // Send the sync request
    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'started') {
            // Start polling for progress
            pollSyncProgress(courseId);
        } else if (data.error) {
            // Handle specific error message
            updateProgressUI({
                status: 'error',
                message: 'Failed to start sync: ' + data.error,
                error: data.error,
                current: 0,
                total: 1
            });
        } else {
            // Handle generic error
            updateProgressUI({
                status: 'error',
                message: 'Failed to start sync operation',
                error: 'The server returned an unexpected response',
                current: 0,
                total: 1
            });
        }
    })
    .catch(error => {
        console.error('Error starting sync:', error);
        updateProgressUI({
            status: 'error',
            message: 'Failed to start sync',
            error: error.toString(),
            current: 0,
            total: 1
        });
    });
}

/**
 * Get the CSRF token from cookies
 */
function getCsrfToken() {
    const name = 'csrftoken';
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

/**
 * Show a notification toast
 * @param {string} message - The message to display
 * @param {string} type - The type of notification (success, danger, warning, info)
 */
function showNotification(message, type = 'info') {
    // Create toast container if it doesn't exist
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }
    
    // Create toast
    const toastId = `toast-${Date.now()}`;
    const toast = document.createElement('div');
    toast.id = toastId;
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    // Set toast content
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    // Add toast to container
    toastContainer.appendChild(toast);
    
    // Initialize and show toast
    const bsToast = new bootstrap.Toast(toast, {
        autohide: true,
        delay: 5000
    });
    bsToast.show();
    
    // Remove toast from DOM after it's hidden
    toast.addEventListener('hidden.bs.toast', function () {
        toast.remove();
    });
}

/**
 * Check if a sync is in progress on page load and show the progress modal
 */
function checkSyncInProgress() {
    // Get course ID from URL if present
    const pathParts = window.location.pathname.split('/');
    const courseIndex = pathParts.indexOf('course');
    const courseId = courseIndex !== -1 && pathParts.length > courseIndex + 1 ? pathParts[courseIndex + 1] : null;
    
    fetch(`/canvas/sync_progress/?course_id=${courseId || ''}`)
        .then(response => response.json())
        .then(data => {
            if (data && Object.keys(data).length > 0 && 
                data.status !== 'completed' && data.status !== 'error') {
                // Initialize the progress UI
                initSyncProgressUI();
                
                // Show the progress modal
                syncProgressModal.show();
                
                // Update the UI with current progress
                updateProgressUI(data);
                
                // Start polling for progress
                pollSyncProgress(courseId);
            }
        })
        .catch(error => {
            console.error('Error checking sync progress:', error);
        });
}

// Page-specific functions that are currently duplicated in template files
/**
 * Sync the courses selected in the modal
 */
function syncSelectedCourses() {
    const selected = Array.from(document.querySelectorAll('.course-checkbox:checked')).map(cb => cb.value);
    if (selected.length === 0) {
        alert('Please select at least one course.');
        return;
    }

    // Hide the modal
    const syncModal = bootstrap.Modal.getInstance(document.getElementById('syncCoursesModal'));
    if (syncModal) {
        syncModal.hide();
    }

    // Start sync with progress tracking
    startSyncWithProgress(
        '/canvas/sync_selected_courses/',
        {course_ids: selected}
    );
}

/**
 * Sync all courses by selecting all checkboxes and then syncing selected
 */
function syncAllCourses() {
    selectAllCourses(true);
    syncSelectedCourses();
}

/**
 * Sync the current course (used on course detail page)
 */
function syncCurrentCourse() {
    // Start a simple loading animation for the button
    const syncButton = document.getElementById('syncCourseBtn');
    if (syncButton) {
        syncButton.innerHTML = '<i class="fa fa-spinner fa-spin"></i>';
        syncButton.disabled = true;
    }

    // Get course ID from the URL
    const pathParts = window.location.pathname.split('/');
    const courseId = pathParts[pathParts.indexOf('course') + 1];

    // Start sync with progress tracking
    startSyncWithProgress(
        '/canvas/sync_selected_courses/',
        {course_ids: [courseId]},
        courseId
    );

    // Reset button after starting the sync
    if (syncButton) {
        setTimeout(() => {
            syncButton.innerHTML = '<i class="fa fa-refresh"></i>';
            syncButton.disabled = false;
        }, 1000);
    }
}

/**
 * Load courses for the modal
 */
function loadCoursesForModal() {
    document.getElementById('coursesLoading').style.display = 'block';
    document.getElementById('coursesList').style.display = 'none';
    document.getElementById('coursesError').style.display = 'none';
    fetch('/canvas/list_available_courses/')
        .then(response => response.json())
        .then(data => {
            if (data.courses) {
                const list = document.getElementById('coursesCheckboxList');
                list.innerHTML = '';
                data.courses.forEach(course => {
                    const li = document.createElement('li');
                    li.innerHTML = `<label><input type="checkbox" class="course-checkbox" value="${course.id}"> ${course.name} (${course.course_code})</label>`;
                    list.appendChild(li);
                });
                document.getElementById('coursesLoading').style.display = 'none';
                document.getElementById('coursesList').style.display = 'block';
            } else {
                document.getElementById('coursesLoading').style.display = 'none';
                document.getElementById('coursesError').innerText = data.error || 'Failed to load courses.';
                document.getElementById('coursesError').style.display = 'block';
            }
        })
        .catch(() => {
            document.getElementById('coursesLoading').style.display = 'none';
            document.getElementById('coursesError').innerText = 'Failed to load courses.';
            document.getElementById('coursesError').style.display = 'block';
        });
}

/**
 * Set selection state for all course checkboxes
 */
function selectAllCourses(select) {
    document.querySelectorAll('.course-checkbox').forEach(cb => cb.checked = select);
}

/**
 * Initialize event handlers for all Canvas pages
 */
function initCanvasEventHandlers() {
    // Sync courses modal setup
    var syncCoursesModal = document.getElementById('syncCoursesModal');
    if (syncCoursesModal) {
        syncCoursesModal.addEventListener('show.bs.modal', function() {
            loadCoursesForModal();
        });
    }

    // Sync current course button
    var syncCourseBtn = document.getElementById('syncCourseBtn');
    if (syncCourseBtn) {
        syncCourseBtn.addEventListener('click', syncCurrentCourse);
    }
}

// When DOM is loaded, check if a sync is in progress and initialize event handlers
document.addEventListener('DOMContentLoaded', function() {
    checkSyncInProgress();
    initCanvasEventHandlers();
});