document.addEventListener('DOMContentLoaded', function() {
    // Add event listeners to the individual course sync buttons
    const syncButtons = document.querySelectorAll('.sync-course-btn');
    syncButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const courseId = this.getAttribute('data-course-id');
            syncCourse(courseId);
        });
    });

    // Custom function to sync a single course
    function syncCourse(courseId) {
        // Start sync with progress tracking
        startSyncWithProgress(
            '/canvas/sync_selected_courses/',
            {course_ids: [courseId]},
            courseId
        );
    }

    // Custom function to handle modal course selection
    window.syncSelectedCourses = function() {
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
            // No course ID for multiple course sync - will use batch tracking
        );
    };

    // Extend the initialization of the page
    // Add this to the DOMContentLoaded handler in the canvas-sync-progress.js file
    const syncCoursesBtn = document.getElementById('syncCoursesBtn');
    if (syncCoursesBtn) {
        syncCoursesBtn.addEventListener('click', function() {
            startSyncWithProgress(
                '/canvas/sync_selected_courses/',
                {course_ids: 'all'} // Special value to sync all courses
            );
        });
    }
});