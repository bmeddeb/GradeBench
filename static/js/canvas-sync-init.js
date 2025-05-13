/**
 * canvas-sync-init.js
 * Initialization for Canvas sync UI event handlers
 */

document.addEventListener('DOMContentLoaded', function() {
    // Handle Sync Selected button in modal
    window.syncSelectedCourses = function() {
        const selected = Array.from(document.querySelectorAll('.course-checkbox:checked')).map(cb => cb.value);
        if (!selected.length) {
            alert('Please select at least one course.');
            return;
        }
        const modalEl = document.getElementById('syncCoursesModal');
        const modal = bootstrap.Modal.getInstance(modalEl);
        if (modal) modal.hide();
        startSyncWithProgress('/canvas/sync_selected_courses/', { course_ids: selected });
    };

    // Handle Sync All button in modal
    window.syncAllCourses = function() {
        const modalEl = document.getElementById('syncCoursesModal');
        const modal = bootstrap.Modal.getInstance(modalEl);
        if (modal) modal.hide();
        startSyncWithProgress('/canvas/sync_selected_courses/', { course_ids: 'all' });
    };

    // Load courses into modal when it is shown
    const syncCoursesModalEl = document.getElementById('syncCoursesModal');
    if (syncCoursesModalEl) {
        syncCoursesModalEl.addEventListener('show.bs.modal', loadCoursesForModal);
    }

    // Handle individual course sync buttons on courses list
    document.querySelectorAll('.sync-course-btn').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const courseId = this.getAttribute('data-course-id');
            startSyncWithProgress('/canvas/sync_selected_courses/', { course_ids: [courseId] }, courseId);
        });
    });

    // Handle Sync All button on courses list when no courses are yet synced
    const syncCoursesBtn = document.getElementById('syncCoursesBtn');
    if (syncCoursesBtn) {
        syncCoursesBtn.addEventListener('click', function() {
            startSyncWithProgress('/canvas/sync_selected_courses/', { course_ids: 'all' });
        });
    }

    // Handle sync button on course detail page
    const syncDetailBtn = document.getElementById('syncCourseBtn');
    if (syncDetailBtn) {
        syncDetailBtn.addEventListener('click', function() {
            const courseId = this.getAttribute('data-course-id');
            startSyncWithProgress('/canvas/sync_selected_courses/', { course_ids: [courseId] }, courseId);
        });
    }

    // Select/deselect all courses in modal
    window.selectAllCourses = function(select) {
        document.querySelectorAll('.course-checkbox').forEach(cb => cb.checked = select);
    };

    // Begin polling if sync is in progress
    checkSyncInProgress();
});