/**
 * Canvas Sync Progress Tracking
 *
 * This JavaScript file provides functionality to track and display the
 * progress of Canvas API synchronization operations using an inline progress bar
 * and course status list.
 */

// Use an immediately invoked function expression (IIFE) to avoid global variable conflicts
(function() {
    // Private variables for this module
    let syncProgressBar = null;
    let syncProgressText = null;
    let syncProgressStatus = null;
    let syncPercentage = null;
    let courseIdParam = '';
    let batchIdParam = '';
    let courseStatusList = null;

    /**
     * Initialize the progress UI
     */
    function initSyncProgressUI() {
        // No need to create elements - they are already in the template
        syncProgressBar = document.getElementById('syncProgressBar');
        syncProgressText = document.getElementById('syncStatusMessage');
        syncProgressStatus = document.getElementById('syncProgressStatus');
        syncPercentage = document.getElementById('syncPercentage');
        courseStatusList = document.getElementById('courseStatusList');

        // Make sure the progress container is visible
        const syncProgress = document.getElementById('syncProgress');
        if (syncProgress) {
            syncProgress.style.display = 'block';
        }

        // Reset progress UI
        syncProgressBar.style.width = '0%';
        syncProgressBar.setAttribute('aria-valuenow', 0);
        syncPercentage.innerText = '0%';
        syncProgressText.innerText = 'Starting sync...';
        syncProgressStatus.innerText = 'Initializing...';
        syncProgressBar.classList.remove('bg-success', 'bg-danger', 'progress-bar-striped', 'progress-bar-animated');
        syncProgressBar.classList.add('bg-primary', 'progress-bar-striped', 'progress-bar-animated');

        // Make sure the course status list container is visible if it exists
        if (courseStatusList) {
            courseStatusList.style.display = 'block';
            courseStatusList.innerHTML = ''; // Clear any previous course status items
        }
    }

    /**
     * Poll for sync progress updates
     * @param {number|null} courseId - The course ID being synced, or null for all courses
     * @param {string|null} batchId - The batch ID for multiple course syncs, or null for single course
     */
    function pollSyncProgress(courseId = null, batchId = null) {
        courseIdParam = courseId || '';
        batchIdParam = batchId || '';

        // If we have a batchId, poll batch progress instead of regular progress
        const url = batchId
            ? `/canvas/sync_batch_progress/?batch_id=${batchIdParam}`
            : `/canvas/sync_progress/?course_id=${courseIdParam}`;

        // Count for handling empty responses
        let emptyResponseCount = 0;
        const MAX_EMPTY_RESPONSES = 5;

        // Make sure the progress UI is initialized
        if (!syncProgressBar) {
            initSyncProgressUI();
        }

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

                            if (batchId) {
                                // Clear course status list
                                if (courseStatusList) {
                                    courseStatusList.innerHTML = '<div class="alert alert-danger">Progress tracking failed. No data received from server.</div>';
                                }
                            }

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

                    // Update main progress UI
                    updateProgressUI(data);

                    // If this is a batch operation, update the course status list
                    if (batchId && data.course_statuses) {
                        console.log('DEBUGGING - Received course_statuses:', JSON.stringify(data.course_statuses, null, 2));
                        updateCourseStatusList(data.course_statuses);
                    }

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
        if (!data || Object.keys(data).length === 0 || !syncProgressBar) {
            // No progress data yet or UI not initialized
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
        syncPercentage.innerText = `${percentage}%`;

        // Update progress text and status
        syncProgressText.innerText = data.message || 'Syncing...';

        // Set color based on status
        if (data.status === 'error') {
            syncProgressBar.classList.remove('bg-primary', 'bg-success', 'progress-bar-animated');
            syncProgressBar.classList.add('bg-danger');
            // Keep the striped pattern for error state
            if (!syncProgressBar.classList.contains('progress-bar-striped')) {
                syncProgressBar.classList.add('progress-bar-striped');
            }
        } else if (data.status === 'completed') {
            syncProgressBar.classList.remove('bg-primary', 'bg-danger', 'progress-bar-animated');
            syncProgressBar.classList.add('bg-success');
            // Keep the striped pattern for completed state
            if (!syncProgressBar.classList.contains('progress-bar-striped')) {
                syncProgressBar.classList.add('progress-bar-striped');
            }
        } else {
            syncProgressBar.classList.remove('bg-success', 'bg-danger');
            syncProgressBar.classList.add('bg-primary');
            // Ensure both animation classes are present for in-progress state
            if (!syncProgressBar.classList.contains('progress-bar-striped')) {
                syncProgressBar.classList.add('progress-bar-striped');
            }
            if (!syncProgressBar.classList.contains('progress-bar-animated')) {
                syncProgressBar.classList.add('progress-bar-animated');
            }
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
            case 'in_progress':
                statusText = 'Sync in progress...';
                break;
            default:
                statusText = `Status: ${data.status}`;
        }

        syncProgressStatus.innerText = statusText;
    }

    /**
     * Update the course status list UI based on course status data
     * @param {Object} courseStatuses - The course status data from the server
     */
    function updateCourseStatusList(courseStatuses) {
        console.log('Updating course status list with full data:', JSON.stringify(courseStatuses, null, 2));

        if (!courseStatusList) {
            // Create the course status list container if it doesn't exist
            courseStatusList = document.createElement('div');
            courseStatusList.id = 'courseStatusList';
            courseStatusList.className = 'course-status-list mt-4';

            // Find where to append it - typically after the main progress bar
            const syncProgress = document.getElementById('syncProgress');
            if (syncProgress && syncProgress.parentNode) {
                syncProgress.parentNode.insertBefore(courseStatusList, syncProgress.nextSibling);
            } else {
                // Fallback - append to body
                document.body.appendChild(courseStatusList);
            }
        }

        // Clear existing content
        courseStatusList.innerHTML = '';

        // Add header
        const header = document.createElement('h6');
        header.className = 'mt-3 mb-2';
        header.textContent = 'Course Status:';
        courseStatusList.appendChild(header);

        // Create course status items
        Object.entries(courseStatuses).forEach(([courseId, status]) => {
            console.log(`DEBUGGING - Course ${courseId} status object:`, JSON.stringify(status, null, 2));

            const courseItem = document.createElement('div');
            courseItem.className = 'course-status-item';

            // Status indicator color
            let statusClass = 'status-pending';
            let statusText = 'Pending';

            if (status.status === 'in_progress') {
                statusClass = 'status-progress';
                statusText = 'In Progress';
            } else if (status.status === 'success' || status.status === 'completed') {
                statusClass = 'status-success';
                statusText = 'Completed';
            } else if (status.status === 'error') {
                statusClass = 'status-error';
                statusText = 'Error';
            } else if (status.status === 'queued') {
                statusClass = 'status-pending';
                statusText = 'Queued';
            }

            // Add animation classes for in-progress status
            let animationClasses = '';
            if (status.status === 'in_progress') {
                animationClasses = 'progress-bar-striped progress-bar-animated';
            }

            // Ensure progress value is valid, default to at least 5% for in-progress items
            // to provide visual feedback even when the server hasn't reported progress yet
            let progressValue = 0;
            if (status.status === 'completed' || status.status === 'success') {
                progressValue = 100;
            } else if (status.status === 'in_progress') {
                progressValue = status.progress !== undefined ? Math.max(5, Number(status.progress)) : 5;
            } else if (status.status === 'error') {
                progressValue = status.progress !== undefined ? Number(status.progress) : 100;
            } else {
                progressValue = status.progress !== undefined ? Number(status.progress) : 0;
            }

            // Get a proper display name for the course
            // Check all possible properties where the name might be stored
            let courseName = '';

            // Log all properties to help debug
            console.log('DEBUGGING - Available properties:', Object.keys(status));

            if (typeof status === 'string') {
                // Handle case where the status might just be a string
                courseName = status;
            } else {
                // Try all possible name properties in order of preference
                if (status.name && typeof status.name === 'string' && status.name.trim() !== '' && !status.name.startsWith('Course ')) {
                    // Found a valid name that's not just "Course ID"
                    courseName = status.name;
                } else if (status.course_code && status.name) {
                    // If we have both code and name, make sure they're not the same before combining
                    const name = status.name;
                    const code = status.course_code;

                    if (name !== code && !name.includes(code)) {
                        courseName = `${code}: ${name}`;
                    } else {
                        courseName = name;
                    }
                } else if (status.course_name && typeof status.course_name === 'string') {
                    courseName = status.course_name;
                } else if (status.course_code && typeof status.course_code === 'string') {
                    courseName = status.course_code;
                } else if (status.display_name && typeof status.display_name === 'string') {
                    courseName = status.display_name;
                } else if (status.title && typeof status.title === 'string') {
                    courseName = status.title;
                } else if (status.course && status.course.name) {
                    // Try to get from a nested course object
                    const name = status.course.name;
                    const code = status.course.course_code;

                    if (code && name !== code && !name.includes(code)) {
                        courseName = `${code}: ${name}`;
                    } else {
                        courseName = name;
                    }
                } else {
                    // Last resort fallback to course ID, but make it clear it's an ID
                    courseName = `Course ID: ${courseId}`;
                }
            }

            console.log(`DEBUGGING - Selected course name: "${courseName}" for course ID: ${courseId}`);

            courseItem.innerHTML = `
                <div class="course-status-header">
                    <div class="status-indicator ${statusClass}"></div>
                    <div class="course-name">${courseName}</div>
                    <div class="course-status">${statusText}</div>
                </div>
                <div class="course-progress-bar">
                    <div class="progress-inner ${statusClass} ${animationClasses}" style="width: ${progressValue}%"></div>
                </div>
                <div class="course-message">${status.message || ''}</div>
            `;

            courseStatusList.appendChild(courseItem);
        });

        // Make sure the course status list is visible
        courseStatusList.style.display = 'block';
    }

    /**
     * Handle sync completion
     * @param {Object} data - The final progress data
     */
    function syncCompleted(data) {
        if (!syncProgressBar) return;

        // Change the progress bar to green or red
        if (data.status === 'completed') {
            syncProgressBar.classList.remove('progress-bar-animated');
            syncProgressText.innerText = 'Sync completed successfully!';

            // Show success notification
            showNotification('Sync completed successfully!', 'success');

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

            // Show error notification
            showNotification(`Sync failed: ${data.error || 'Unknown error'}`, 'danger');
        }

        // Re-enable the sync button
        const syncButton = document.getElementById('syncCoursesBtn');
        if (syncButton) {
            syncButton.disabled = false;
            syncButton.classList.remove('disabled');
            syncButton.innerHTML = '<i class="fa fa-sync"></i> Sync Courses';
        }

        // Re-enable individual course sync buttons
        const courseSyncButtons = document.querySelectorAll('.sync-course-btn');
        courseSyncButtons.forEach(btn => {
            btn.disabled = false;
            btn.classList.remove('disabled');
            btn.innerHTML = '<i class="fa fa-refresh"></i> Sync';
        });

        // Re-enable modal sync button
        const syncSelectedBtn = document.getElementById('syncSelectedBtn');
        if (syncSelectedBtn) {
            syncSelectedBtn.disabled = false;
            syncSelectedBtn.classList.remove('disabled');
            syncSelectedBtn.innerHTML = 'Sync Selected';
        }

        // Keep the course status list visible - don't hide it

        // Hide progress bar after a delay
        setTimeout(() => {
            const syncProgress = document.getElementById('syncProgress');
            if (syncProgress) {
                // Fade out the progress container
                syncProgress.style.opacity = '1';
                let opacity = 1;
                const fadeInterval = setInterval(() => {
                    if (opacity <= 0.1) {
                        clearInterval(fadeInterval);
                        syncProgress.style.display = 'none';
                        syncProgress.style.opacity = '1';
                    } else {
                        opacity -= 0.1;
                        syncProgress.style.opacity = opacity;
                    }
                }, 50);
            }
        }, 3000);
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

        // Disable the sync button while syncing
        const syncButton = document.getElementById('syncCoursesBtn');
        if (syncButton) {
            syncButton.disabled = true;
            syncButton.classList.add('disabled');
            syncButton.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Syncing...';
        }

        // Disable the selected courses sync button
        const syncSelectedBtn = document.getElementById('syncSelectedBtn');
        if (syncSelectedBtn) {
            syncSelectedBtn.disabled = true;
            syncSelectedBtn.classList.add('disabled');
            syncSelectedBtn.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Syncing...';
        }

        // Disable the specific course sync button if applicable
        if (courseId) {
            const courseSyncButtons = document.querySelectorAll('.sync-course-btn');
            courseSyncButtons.forEach(btn => {
                if (btn.getAttribute('data-course-id') === courseId.toString()) {
                    btn.disabled = true;
                    btn.classList.add('disabled');
                    btn.innerHTML = '<i class="fa fa-spinner fa-spin"></i>';
                }
            });

            // Also check for the course detail page sync button
            const detailSyncBtn = document.getElementById('syncCourseBtn');
            if (detailSyncBtn && detailSyncBtn.getAttribute('data-course-id') === courseId.toString()) {
                detailSyncBtn.disabled = true;
                detailSyncBtn.classList.add('disabled');
                detailSyncBtn.innerHTML = '<i class="fa fa-spinner fa-spin"></i>';
            }
        }

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
                // Start polling for progress using batch_id if available
                if (data.batch_id) {
                    pollSyncProgress(null, data.batch_id);
                } else {
                    // Fall back to regular course progress
                    pollSyncProgress(courseId);
                }
            } else if (data.error) {
                // Handle specific error message
                updateProgressUI({
                    status: 'error',
                    message: 'Failed to start sync: ' + data.error,
                    error: data.error,
                    current: 0,
                    total: 1
                });

                // Re-enable all buttons
                enableAllButtons();
            } else {
                // Handle generic error
                updateProgressUI({
                    status: 'error',
                    message: 'Failed to start sync operation',
                    error: 'The server returned an unexpected response',
                    current: 0,
                    total: 1
                });

                // Re-enable all buttons
                enableAllButtons();
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

            // Re-enable all buttons
            enableAllButtons();
        });
    }

    /**
     * Helper function to re-enable all sync buttons
     */
    function enableAllButtons() {
        // Re-enable the sync courses button
        const syncButton = document.getElementById('syncCoursesBtn');
        if (syncButton) {
            syncButton.disabled = false;
            syncButton.classList.remove('disabled');
            syncButton.innerHTML = '<i class="fa fa-sync"></i> Sync Courses';
        }

        // Re-enable the selected courses sync button
        const syncSelectedBtn = document.getElementById('syncSelectedBtn');
        if (syncSelectedBtn) {
            syncSelectedBtn.disabled = false;
            syncSelectedBtn.classList.remove('disabled');
            syncSelectedBtn.innerHTML = 'Sync Selected';
        }

        // Re-enable all course sync buttons
        const courseSyncButtons = document.querySelectorAll('.sync-course-btn');
        courseSyncButtons.forEach(btn => {
            btn.disabled = false;
            btn.classList.remove('disabled');
            btn.innerHTML = '<i class="fa fa-refresh"></i> Sync';
        });

        // Re-enable the course detail sync button
        const detailSyncBtn = document.getElementById('syncCourseBtn');
        if (detailSyncBtn) {
            detailSyncBtn.disabled = false;
            detailSyncBtn.classList.remove('disabled');
            detailSyncBtn.innerHTML = '<i class="fa fa-refresh"></i>';
        }
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
     * Check if a sync is in progress on page load and show the progress
     */
    function checkSyncInProgress() {
        // Get course ID from URL if present
        const pathParts = window.location.pathname.split('/');
        const courseIndex = pathParts.indexOf('course');
        const courseId = courseIndex !== -1 && pathParts.length > courseIndex + 1 ? pathParts[courseIndex + 1] : null;

        // First check for regular sync progress
        fetch(`/canvas/sync_progress/?course_id=${courseId || ''}`)
            .then(response => response.json())
            .then(data => {
                if (data && Object.keys(data).length > 0 &&
                    data.status !== 'completed' && data.status !== 'error') {
                    // Initialize the progress UI
                    initSyncProgressUI();

                    // Update the UI with current progress
                    updateProgressUI(data);

                    // Start polling for progress
                    pollSyncProgress(courseId);

                    // Disable relevant buttons
                    disableButtons(courseId);
                } else {
                    // Check for batch sync progress
                    // We can't know the batch ID from URL, so we'll have to iterate through
                    // session storage or just display a loading indicator if we detect a sync
                    // is in progress from the session

                    // Since we don't have easy access to session data, let's just avoid
                    // showing duplicate progress bars if one from sync_progress already showed
                }
            })
            .catch(error => {
                console.error('Error checking sync progress:', error);
            });
    }

    /**
     * Helper function to disable buttons during sync
     * @param {number|null} courseId - The course ID being synced, if any
     */
    function disableButtons(courseId) {
        // Disable the sync button while syncing
        const syncButton = document.getElementById('syncCoursesBtn');
        if (syncButton) {
            syncButton.disabled = true;
            syncButton.classList.add('disabled');
            syncButton.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Syncing...';
        }

        // Disable the specific course sync button if applicable
        if (courseId) {
            const courseSyncButtons = document.querySelectorAll('.sync-course-btn');
            courseSyncButtons.forEach(btn => {
                if (btn.getAttribute('data-course-id') === courseId.toString()) {
                    btn.disabled = true;
                    btn.classList.add('disabled');
                    btn.innerHTML = '<i class="fa fa-spinner fa-spin"></i>';
                }
            });

            const detailSyncBtn = document.getElementById('syncCourseBtn');
            if (detailSyncBtn && detailSyncBtn.getAttribute('data-course-id') === courseId.toString()) {
                detailSyncBtn.disabled = true;
                detailSyncBtn.classList.add('disabled');
                detailSyncBtn.innerHTML = '<i class="fa fa-spinner fa-spin"></i>';
            }
        }
    }

    // Expose public functions to the global scope
    window.startSyncWithProgress = startSyncWithProgress;
    window.checkSyncInProgress = checkSyncInProgress;

    // When DOM is loaded, check if a sync is in progress
    document.addEventListener('DOMContentLoaded', checkSyncInProgress);

    // FIRST_EDIT: Add modal support functions
    function loadCoursesForModal() {
        const loading = document.getElementById('coursesLoading');
        const listContainer = document.getElementById('coursesList');
        const errorContainer = document.getElementById('coursesError');
        if (loading && listContainer && errorContainer) {
            loading.classList.remove('initially-hidden');
            listContainer.classList.add('initially-hidden');
            errorContainer.classList.add('initially-hidden');
        }

        fetch('/canvas/list_available_courses/')
            .then(response => response.json())
            .then(data => {
                const list = document.getElementById('coursesCheckboxList');
                list.innerHTML = '';
                if (data.courses) {
                    data.courses.forEach(course => {
                        const li = document.createElement('li');
                        li.innerHTML = `<label><input type=\"checkbox\" class=\"course-checkbox\" value=\"${course.id}\"> ${course.name} (${course.course_code})</label>`;
                        list.appendChild(li);
                    });
                    loading.classList.add('initially-hidden');
                    listContainer.classList.remove('initially-hidden');
                } else {
                    loading.classList.add('initially-hidden');
                    errorContainer.innerText = data.error || 'Failed to load courses.';
                    errorContainer.classList.remove('initially-hidden');
                }
            })
            .catch(() => {
                if (loading) loading.classList.add('initially-hidden');
                if (errorContainer) {
                    errorContainer.innerText = 'Failed to load courses.';
                    errorContainer.classList.remove('initially-hidden');
                }
            });
    }

    function selectAllCourses(select) {
        document.querySelectorAll('.course-checkbox').forEach(cb => cb.checked = select);
    }

    // Expose modal functions to global scope
    window.loadCoursesForModal = loadCoursesForModal;
    window.selectAllCourses = selectAllCourses;

    // Wire up modal show event to load courses
    document.addEventListener('DOMContentLoaded', function() {
        const syncCoursesModal = document.getElementById('syncCoursesModal');
        if (syncCoursesModal) {
            syncCoursesModal.addEventListener('show.bs.modal', loadCoursesForModal);
        }
    });

})(); // End of IIFE