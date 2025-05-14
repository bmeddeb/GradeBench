/**
 * Canvas Group Management - Drag and Drop with SortableJS
 * Implements student assignment to groups via drag and drop.
 */

// Function to extract course ID from URL
function getCourseIdFromURL() {
    const path = window.location.pathname;
    const regex = /\/canvas\/course\/(\d+)/;
    const match = path.match(regex);

    if (match && match[1]) {
        return match[1];
    }

    console.error('Could not extract course ID from URL path:', path);
    return null;
}

document.addEventListener('DOMContentLoaded', function() {
    // Verify SortableJS is available
    if (typeof Sortable === 'undefined') {
        console.error('SortableJS is not loaded. Drag and drop will not work.');

        if (typeof $ !== 'undefined' && typeof $.notify === 'function') {
            $.notify({
                message: 'SortableJS is not loaded. Drag and drop will not work.'
            }, {
                type: 'danger',
                placement: { from: 'top', align: 'center' },
                z_index: 2000,
                delay: 5000
            });
        }
        return;  // Exit early if SortableJS isn't available
    }

    // Track changes to student assignments across groups
    let hasUnsavedChanges = false;
    let originalAssignments = {};  // Store original student assignments for comparison
    let currentCategoryId = null;

    // Track which lists have sortable instances
    const sortableInstances = {};

    // Get DOM elements
    const saveChangesBanner = document.getElementById('saveChangesBanner');
    const saveChangesBtn = document.getElementById('saveChangesBtn');
    const discardChangesBtn = document.getElementById('discardChangesBtn');

    // Listen for group data loaded event
    document.addEventListener('groupDataLoaded', function(e) {
        const categoryId = e.detail.categoryId;
        currentCategoryId = categoryId;

        // Remove all previous sortable instances to avoid duplicates
        removeSortableInstances();

        // Initialize sortable with a slight delay to ensure DOM is ready
        setTimeout(() => {
            initSortables(categoryId);
            captureOriginalAssignments();
        }, 250);
    });

    // Initialize Sortable.js for all group lists and the unassigned list
    function initSortables(categoryId) {
        // Find all member lists in this category's tab
        const tabContent = document.getElementById(`groupset-${categoryId}-content`);
        if (!tabContent) return;

        // Get all group member lists
        const memberLists = tabContent.querySelectorAll('.members-list');

        // Create a Sortable instance for each members list
        memberLists.forEach(list => {
            try {
                // Check if this is a group card list or unassigned list
                const cardElement = list.closest('.card');
                if (!cardElement) {
                    return;
                }

                // Check if it's an unassigned list
                if (cardElement.classList.contains('unassigned-students-card')) {
                    // Skip - we'll handle the unassigned list separately
                    return;
                }

                // It's a group card
                const groupId = cardElement.dataset.groupId;
                if (!groupId) {
                    console.warn('Group card is missing data-group-id attribute', cardElement);
                    return;
                }

                const sortable = new Sortable(list, {
                    group: `category-${categoryId}`,  // Group name to allow dragging between lists
                    animation: 150,                    // Animation speed in ms
                    chosenClass: 'sortable-chosen',    // Class for chosen item
                    dragClass: 'sortable-drag',        // Class for dragging item
                    ghostClass: 'sortable-ghost',      // Class for drop placeholder
                    forceFallback: false,              // Force fallback
                    fallbackClass: 'sortable-fallback',// Class for fallback
                    scroll: true,                      // Enable scrolling in lists
                    bubbleScroll: true,                // Bubble scroll through parents
                    scrollSensitivity: 80,             // Scroll sensitivity in px
                    scrollSpeed: 10,                   // Scroll speed in px/s

                    // Element is dragged from one list to another
                    onAdd: function(evt) {
                        const studentId = evt.item.dataset.studentId;
                        const newGroupId = groupId;
                        const fromElement = evt.from.closest('.card');
                        const oldGroupId = fromElement ? fromElement.dataset.groupId : null;

                        // Mark unsaved changes and show banner
                        if (!hasUnsavedChanges) {
                            hasUnsavedChanges = true;
                            showSaveChangesBanner();
                        }
                    }
                });

                sortableInstances[`group-${groupId}`] = sortable;
            } catch (err) {
                console.error('Error creating Sortable instance for group list:', err);
            }
        });

        // Get the unassigned students list
        const unassignedList = tabContent.querySelector('.unassigned-list');

        if (unassignedList) {
            try {
                // Create Sortable instance for the unassigned list
                const sortable = new Sortable(unassignedList, {
                    group: `category-${categoryId}`,  // Group name to allow dragging between lists
                    animation: 150,                    // Animation speed in ms
                    chosenClass: 'sortable-chosen',    // Class for chosen item
                    dragClass: 'sortable-drag',        // Class for dragging item
                    ghostClass: 'sortable-ghost',      // Class for drop placeholder
                    forceFallback: false,              // Force fallback
                    fallbackClass: 'sortable-fallback',// Class for fallback
                    scroll: true,                      // Enable scrolling in lists
                    bubbleScroll: true,                // Bubble scroll through parents
                    scrollSensitivity: 80,             // Scroll sensitivity in px
                    scrollSpeed: 10,                   // Scroll speed in px/s

                    // Element is dragged from one list to another
                    onAdd: function(evt) {
                        const studentId = evt.item.dataset.studentId;
                        const fromElement = evt.from.closest('.card');
                        let oldGroupId = null;

                        // Try to get the group ID from the card element
                        if (fromElement && !fromElement.classList.contains('unassigned-students-card')) {
                            oldGroupId = fromElement.dataset.groupId;
                        }

                        // Mark unsaved changes and show banner
                        if (!hasUnsavedChanges) {
                            hasUnsavedChanges = true;
                            showSaveChangesBanner();
                        }
                    }
                });

                // Store the instance
                sortableInstances['unassigned'] = sortable;
            } catch (err) {
                console.error('Error creating Sortable instance for unassigned list:', err);
            }
        }
    }

    // Remove all Sortable instances to avoid duplicate event handlers
    function removeSortableInstances() {
        for (const key in sortableInstances) {
            if (sortableInstances[key]) {
                try {
                    sortableInstances[key].destroy();
                } catch (err) {
                    console.warn(`Error destroying sortable instance ${key}:`, err);
                }
                delete sortableInstances[key];
            }
        }
    }

    // Capture the original student assignments for comparison
    function captureOriginalAssignments() {
        originalAssignments = {};

        // If no category is loaded yet, return
        if (!currentCategoryId) return;

        const tabContent = document.getElementById(`groupset-${currentCategoryId}-content`);
        if (!tabContent) return;

        // Get all student items in groups
        const groupCards = tabContent.querySelectorAll('.group-card');
        groupCards.forEach(card => {
            const groupId = card.dataset.groupId;
            const studentItems = card.querySelectorAll('.student-item');

            studentItems.forEach(item => {
                const studentId = item.dataset.studentId;
                originalAssignments[studentId] = groupId;
            });
        });

        // Get all unassigned students
        const unassignedStudents = tabContent.querySelectorAll('.unassigned-list .student-item');
        unassignedStudents.forEach(item => {
            const studentId = item.dataset.studentId;
            originalAssignments[studentId] = null; // null means unassigned
        });
    }

    // Get the current student assignments
    function getCurrentAssignments() {
        const currentAssignments = {};

        // If no category is loaded yet, return empty object
        if (!currentCategoryId) return currentAssignments;

        const tabContent = document.getElementById(`groupset-${currentCategoryId}-content`);
        if (!tabContent) return currentAssignments;

        // Get all student items in groups
        const groupCards = tabContent.querySelectorAll('.group-card');
        groupCards.forEach(card => {
            const groupId = card.dataset.groupId;
            const studentItems = card.querySelectorAll('.student-item');

            studentItems.forEach(item => {
                const studentId = item.dataset.studentId;
                currentAssignments[studentId] = groupId;
            });
        });

        // Get all unassigned students
        const unassignedStudents = tabContent.querySelectorAll('.unassigned-list .student-item');
        unassignedStudents.forEach(item => {
            const studentId = item.dataset.studentId;
            currentAssignments[studentId] = null; // null means unassigned
        });

        return currentAssignments;
    }

    // Compare current assignments with original to detect changes
    function checkForChanges() {
        const currentAssignments = getCurrentAssignments();

        for (const studentId in currentAssignments) {
            // If student wasn't in original assignments, it's a change
            if (!(studentId in originalAssignments)) {
                return true;
            }

            // If student's group changed, it's a change
            if (currentAssignments[studentId] !== originalAssignments[studentId]) {
                return true;
            }
        }

        // Check if any students from original assignments are missing in current
        for (const studentId in originalAssignments) {
            if (!(studentId in currentAssignments)) {
                return true;
            }
        }

        return false;
    }

    // Show the save changes banner
    function showSaveChangesBanner() {
        if (saveChangesBanner) {
            saveChangesBanner.classList.add('visible');
        }
    }

    // Hide the save changes banner
    function hideSaveChangesBanner() {
        if (saveChangesBanner) {
            saveChangesBanner.classList.remove('visible');
        }
    }

    // Save changes to the server
    async function saveChanges() {
        if (!currentCategoryId) return;

        const currentAssignments = getCurrentAssignments();
        const changes = [];

        // Determine which assignments changed
        for (const studentId in currentAssignments) {
            // Skip if no change
            if (studentId in originalAssignments &&
                currentAssignments[studentId] === originalAssignments[studentId]) {
                continue;
            }

            changes.push({
                student_id: studentId,
                new_group_id: currentAssignments[studentId],
                old_group_id: originalAssignments[studentId] || null
            });
        }

        if (changes.length === 0) {
            hasUnsavedChanges = false;
            hideSaveChangesBanner();
            return;
        }

        try {
            // Show saving notification
            if (typeof $ !== 'undefined' && typeof $.notify === 'function') {
                $.notify({
                    message: `Saving ${changes.length} student assignment changes...`
                }, {
                    type: 'info',
                    placement: { from: 'top', align: 'center' },
                    z_index: 2000,
                    delay: 2000
                });
            }

            // Get course ID from URL
            const courseId = getCourseIdFromURL();
            if (!courseId) {
                throw new Error('Could not determine course ID from URL');
            }

            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

            const response = await fetch(`/canvas/course/${courseId}/group_set/${currentCategoryId}/batch_assign/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({
                    changes: changes
                })
            });

            const data = await response.json();

            if (data.success) {
                // Show success notification
                if (typeof $ !== 'undefined' && typeof $.notify === 'function') {
                    $.notify({
                        message: `Successfully saved ${changes.length} student assignments!`
                    }, {
                        type: 'success',
                        placement: { from: 'top', align: 'center' },
                        z_index: 2000,
                        delay: 3000
                    });
                }

                // Update original assignments to match current state
                captureOriginalAssignments();

                // Reset flags and hide banner
                hasUnsavedChanges = false;
                hideSaveChangesBanner();
            } else {
                throw new Error(data.error || 'Unknown error saving changes');
            }
        } catch (error) {
            console.error('Error saving changes:', error);

            // Show error notification
            if (typeof $ !== 'undefined' && typeof $.notify === 'function') {
                $.notify({
                    message: `Error saving changes: ${error.message}`
                }, {
                    type: 'danger',
                    placement: { from: 'top', align: 'center' },
                    z_index: 2000,
                    delay: 5000
                });
            } else {
                alert(`Error saving changes: ${error.message}`);
            }
        }
    }

    // Discard changes and reset to original state
    function discardChanges() {
        if (!currentCategoryId || !hasUnsavedChanges) return;

        // Show notification
        if (typeof $ !== 'undefined' && typeof $.notify === 'function') {
            $.notify({
                message: 'Discarding changes...'
            }, {
                type: 'info',
                placement: { from: 'top', align: 'center' },
                z_index: 2000,
                delay: 2000
            });
        }

        // Reload the group set data to reset to original state
        loadGroupSetData(currentCategoryId);

        // Reset flags and hide banner
        hasUnsavedChanges = false;
        hideSaveChangesBanner();
    }

    // Event listeners for banner buttons
    if (saveChangesBtn) {
        saveChangesBtn.addEventListener('click', saveChanges);
    }

    if (discardChangesBtn) {
        discardChangesBtn.addEventListener('click', discardChanges);
    }

    // Listen for tab changes
    const groupSetTabs = document.querySelectorAll('#groupSetTabs .nav-link');
    groupSetTabs.forEach(tab => {
        tab.addEventListener('show.bs.tab', function(e) {
            // If there are unsaved changes, ask user before switching tabs
            if (hasUnsavedChanges && currentCategoryId) {
                if (!confirm('You have unsaved changes. Switching tabs will discard these changes. Continue?')) {
                    e.preventDefault();
                    return;
                }

                // Reset flags and hide banner
                hasUnsavedChanges = false;
                hideSaveChangesBanner();
            }
        });
    });

    // Make global randomAssignStudents function available
    window.randomAssignStudents = async function(categoryId) {
        if (!categoryId) return;

        // Check if there are any groups in this category
        const tabContent = document.getElementById(`groupset-${categoryId}-content`);
        if (tabContent) {
            const groupCards = tabContent.querySelectorAll('.group-card');
            if (!groupCards || groupCards.length === 0) {
                // Show error notification if there are no groups
                if (typeof $ !== 'undefined' && typeof $.notify === 'function') {
                    $.notify({
                        title: '<strong>No Groups Available</strong>',
                        message: 'Please create at least one group before randomly assigning students.',
                        icon: 'fa fa-exclamation-triangle'
                    }, {
                        type: 'warning',
                        placement: { from: 'top', align: 'center' },
                        z_index: 2000,
                        delay: 5000
                    });
                }
                return;
            }
        }

        try {
            // Create a confirmation dialog using Bootstrap
            // Keep track of this modal so we only create one at a time
            let modalElement = null;

            // Function to safely remove modal from DOM
            const safeRemoveModal = () => {
                if (modalElement && document.body.contains(modalElement)) {
                    // Try to dispose of bootstrap modal properly
                    try {
                        const bsModal = bootstrap.Modal.getInstance(modalElement);
                        if (bsModal) {
                            bsModal.dispose();
                        }
                    } catch (e) {
                        console.warn('Error disposing bootstrap modal:', e);
                    }
                    
                    // Now remove from DOM
                    try {
                        document.body.removeChild(modalElement);
                    } catch (e) {
                        console.warn('Error removing modal element:', e);
                    }
                    
                    // Clear reference
                    modalElement = null;
                }
            };

            // Clean up any existing modals first
            safeRemoveModal();

            // Create the confirmation modal
            modalElement = document.createElement('div');
            modalElement.className = 'modal fade';
            modalElement.id = 'randomAssignConfirmModal';
            modalElement.setAttribute('tabindex', '-1');
            modalElement.setAttribute('aria-labelledby', 'randomAssignConfirmModalLabel');
            modalElement.setAttribute('aria-hidden', 'true');
            
            modalElement.innerHTML = `
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="randomAssignConfirmModalLabel">Confirm Random Assignment</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <p>This will randomly assign all unassigned students to groups.</p>
                            <p>Do you want to proceed?</p>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-primary" id="confirmRandomAssignBtn">Proceed</button>
                        </div>
                    </div>
                </div>
            `;
            
            // Add modal to body
            document.body.appendChild(modalElement);
            
            // Create Bootstrap modal instance
            const bsModal = new bootstrap.Modal(modalElement);
            
            // Show the modal
            bsModal.show();
            
            // Handle hidden.bs.modal event - this runs when modal is fully hidden
            modalElement.addEventListener('hidden.bs.modal', function(e) {
                safeRemoveModal();
            });
            
            // Add event listener to the confirm button
            const confirmBtn = document.getElementById('confirmRandomAssignBtn');
            if (confirmBtn) {
                confirmBtn.addEventListener('click', function() {
                    // Hide confirm modal and proceed with random assignment
                    bsModal.hide();
                    
                    // Wait for confirm modal to be fully hidden before starting assignment
                    setTimeout(() => {
                        // Start random assignment
                        performRandomAssignment(categoryId);
                    }, 300);
                });
            }
        } catch (error) {
            console.error('Error showing confirmation dialog:', error);
            // Fallback to simple confirm
            if (confirm('This will randomly assign all unassigned students to groups. Proceed?')) {
                performRandomAssignment(categoryId);
            }
        }
    };

    // Separate function to actually perform the random assignment
    async function performRandomAssignment(categoryId) {
        let progressModalElement = null;
        let bsProgressModal = null;
        
        try {
            // Function to safely remove progress modal
            const safeRemoveProgressModal = () => {
                if (progressModalElement && document.body.contains(progressModalElement)) {
                    try {
                        if (bsProgressModal) {
                            bsProgressModal.dispose();
                        }
                    } catch (e) {
                        console.warn('Error disposing bootstrap progress modal:', e);
                    }
                    
                    try {
                        document.body.removeChild(progressModalElement);
                    } catch (e) {
                        console.warn('Error removing progress modal element:', e);
                    }
                    
                    progressModalElement = null;
                    bsProgressModal = null;
                }
            };
            
            // Clean up any existing modals first
            safeRemoveProgressModal();
            
            // Create progress modal
            progressModalElement = document.createElement('div');
            progressModalElement.className = 'modal fade';
            progressModalElement.id = 'randomAssignProgressModal';
            progressModalElement.setAttribute('tabindex', '-1');
            progressModalElement.setAttribute('aria-labelledby', 'randomAssignProgressModalLabel');
            progressModalElement.setAttribute('aria-hidden', 'true');
            progressModalElement.setAttribute('data-bs-backdrop', 'static');
            progressModalElement.setAttribute('data-bs-keyboard', 'false');
            
            progressModalElement.innerHTML = `
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="randomAssignProgressModalLabel">Random Assignment in Progress</h5>
                        </div>
                        <div class="modal-body text-center">
                            <div class="spinner-border text-primary mb-3" role="status">
                                <span class="visually-hidden">Assigning students...</span>
                            </div>
                            <p>Randomly assigning students to groups...</p>
                            <p class="text-muted small">This may take a few moments. Please don't close this window.</p>
                        </div>
                    </div>
                </div>
            `;
            
            // Add modal to body
            document.body.appendChild(progressModalElement);
            
            // Create Bootstrap modal instance
            bsProgressModal = new bootstrap.Modal(progressModalElement);
            
            // Show the modal
            bsProgressModal.show();
            
            // Handle hidden.bs.modal event to clean up
            progressModalElement.addEventListener('hidden.bs.modal', function(e) {
                safeRemoveProgressModal();
            });

            // Get course ID from URL
            const courseId = getCourseIdFromURL();
            if (!courseId) {
                throw new Error('Could not determine course ID from URL');
            }

            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

            const response = await fetch(`/canvas/course/${courseId}/group_set/${categoryId}/random_assign/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            const data = await response.json();

            // Hide progress modal
            try {
                if (bsProgressModal) {
                    bsProgressModal.hide();
                }
            } catch (e) {
                console.warn('Error hiding progress modal:', e);
                safeRemoveProgressModal();
            }

            if (data.success) {
                // Show success notification
                if (typeof $ !== 'undefined' && typeof $.notify === 'function') {
                    $.notify({
                        message: `Successfully assigned ${data.assigned_count} students randomly!`
                    }, {
                        type: 'success',
                        placement: { from: 'top', align: 'center' },
                        z_index: 2000,
                        delay: 3000
                    });
                }

                // Reload the view to show the new assignments
                if (typeof loadGroupSetData === 'function') {
                    loadGroupSetData(categoryId);
                } else {
                    window.location.reload();
                }

                // Reset flags and hide banner if it was showing
                hasUnsavedChanges = false;
                hideSaveChangesBanner();
            } else {
                throw new Error(data.error || 'Unknown error during random assignment');
            }
        } catch (error) {
            console.error('Error during random assignment:', error);

            // Ensure progress modal is closed
            if (bsProgressModal) {
                try {
                    bsProgressModal.hide();
                } catch (e) {
                    console.warn('Error hiding progress modal:', e);
                    safeRemoveProgressModal();
                }
            }

            // Show error notification
            if (typeof $ !== 'undefined' && typeof $.notify === 'function') {
                $.notify({
                    message: `Error during random assignment: ${error.message}`
                }, {
                    type: 'danger',
                    placement: { from: 'top', align: 'center' },
                    z_index: 2000,
                    delay: 5000
                });
            } else {
                console.error(`Error during random assignment: ${error.message}`);
                alert(`Error during random assignment: ${error.message}`);
            }
        }
    }
});