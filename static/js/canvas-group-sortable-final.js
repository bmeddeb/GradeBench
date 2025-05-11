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

        // Show confirmation notification with buttons
        if (typeof $ !== 'undefined' && typeof $.notify === 'function') {
            // Create a custom notification with action buttons
            const confirmNotify = $.notify({
                title: '<strong>Confirm Random Assignment</strong>',
                message: 'This will randomly assign all unassigned students to groups. Proceed?',
                icon: 'fa fa-question-circle'
            }, {
                type: 'info',
                delay: 0, // No auto-close
                placement: { from: 'top', align: 'center' },
                z_index: 2000,
                template: '<div data-notify="container" class="col-xs-11 col-sm-4 alert alert-{0}" role="alert">' +
                    '<button type="button" aria-hidden="true" class="close" data-notify="dismiss">×</button>' +
                    '<span data-notify="icon"></span> ' +
                    '<span data-notify="title">{1}</span> ' +
                    '<span data-notify="message">{2}</span>' +
                    '<div class="progress" data-notify="progressbar">' +
                    '<div class="progress-bar progress-bar-{0}" role="progressbar" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100" style="width: 0%;"></div>' +
                    '</div>' +
                    '<div class="notify-actions" style="margin-top: 10px; text-align: right;">' +
                    '<button class="btn btn-sm btn-light cancel-btn">Cancel</button> ' +
                    '<button class="btn btn-sm btn-primary confirm-btn">Proceed</button>' +
                    '</div>' +
                    '</div>'
            });

            // Handle buttons in the notification
            const container = confirmNotify.$ele;
            container.find('.confirm-btn').on('click', async function() {
                confirmNotify.close();
                await performRandomAssignment(categoryId);
            });

            container.find('.cancel-btn').on('click', function() {
                confirmNotify.close();
            });

            return; // Exit the function - user will click button to proceed
        }

        // Fallback if notify isn't available (shouldn't happen)
        await performRandomAssignment(categoryId);
    };

    // Separate function to actually perform the random assignment
    async function performRandomAssignment(categoryId) {
        try {
            // Show loading notification
            if (typeof $ !== 'undefined' && typeof $.notify === 'function') {
                $.notify({
                    message: 'Randomly assigning students...'
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
            
            const response = await fetch(`/canvas/course/${courseId}/group_set/${categoryId}/random_assign/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            const data = await response.json();
            
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
            }
        }
    };
});