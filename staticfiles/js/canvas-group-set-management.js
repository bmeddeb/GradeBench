document.addEventListener('DOMContentLoaded', function() {
    // Initialize modal (used only for delete group set, not for delete group)
    let deleteModal = new bootstrap.Modal(document.getElementById('confirmDeleteModal'));
    let confirmDeleteButton = document.getElementById('confirmDeleteButton');
    let currentDeleteAction = null;

    // Initialize tabs with data loading
    const groupSetTabs = document.querySelectorAll('#groupSetTabs .nav-link');
    let activeTabLoaded = false;

    // Add click event to tabs
    groupSetTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const categoryId = this.getAttribute('data-category-id');
            loadGroupSetData(categoryId);

            // Update URL hash (for bookmarking and history)
            window.location.hash = `category-${categoryId}`;
        });
    });

    // Function to select a tab by category ID
    function selectTabByCategory(categoryId) {
        // Find the tab for this category
        const tab = document.querySelector(`#groupSetTabs .nav-link[data-category-id="${categoryId}"]`);
        if (tab) {
            // Get the Bootstrap tab instance
            const bsTab = new bootstrap.Tab(tab);
            // Show this tab
            bsTab.show();
            // Load data for this category
            loadGroupSetData(categoryId);
            return true;
        }
        return false;
    }

    // Check URL hash for category ID on page load
    const hashMatch = window.location.hash.match(/^#category-(\d+)$/);
    if (hashMatch && hashMatch[1]) {
        // Try to select the tab based on the hash
        const selectedCategory = hashMatch[1];
        if (selectTabByCategory(selectedCategory)) {
            // Successfully selected tab
            console.log(`Selected category ${selectedCategory} from URL hash`);
        } else {
            // Fallback to default tab
            const activeTab = document.querySelector('#groupSetTabs .nav-link.active');
            if (activeTab) {
                const categoryId = activeTab.getAttribute('data-category-id');
                loadGroupSetData(categoryId);
            }
        }
    } else {
        // No hash or invalid hash, load default tab
        if (groupSetTabs.length > 0) {
            const activeTab = document.querySelector('#groupSetTabs .nav-link.active');
            if (activeTab) {
                const categoryId = activeTab.getAttribute('data-category-id');
                loadGroupSetData(categoryId);
            }
        }
    }

    // Handle sync button
    const syncButton = document.getElementById('syncGroupsBtn');
    if (syncButton) {
        syncButton.addEventListener('click', function() {
            syncGroups();
        });
    }

    // Add event delegation for delete group set buttons
    document.addEventListener('click', function(e) {
        if (e.target && e.target.closest('.delete-group-set-btn')) {
            const btn = e.target.closest('.delete-group-set-btn');
            const categoryId = btn.getAttribute('data-category-id');
            const categoryName = btn.getAttribute('data-category-name');

            // Show confirmation modal
            document.getElementById('confirmDeleteModalBody').textContent =
                `Are you sure you want to delete the group set "${categoryName}"? This will delete all groups within this set.`;

            // Set up the delete action
            currentDeleteAction = () => deleteGroupSet(categoryId);
            deleteModal.show();
        }
    });

    // Set up confirm delete button
    if (confirmDeleteButton) {
        confirmDeleteButton.addEventListener('click', function() {
            if (currentDeleteAction) {
                // Hide modal
                deleteModal.hide();

                // Call the delete function
                currentDeleteAction();

                // Reset current action
                currentDeleteAction = null;
            }
        });
    }

    // Function to delete a group set
    function deleteGroupSet(categoryId) {
        // Create a POST request with CSRF token
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

        // Get the elements before hiding the modal
        const modal = document.getElementById('confirmDeleteModal');
        const modalBody = document.getElementById('confirmDeleteModalBody');
        const confirmButton = document.getElementById('confirmDeleteButton');
        const closeButton = modal.querySelector('.btn-close');
        const cancelButton = modal.querySelector('.btn-secondary');

        // Disable buttons and show spinner
        if (confirmButton) confirmButton.disabled = true;
        if (closeButton) closeButton.disabled = true;
        if (cancelButton) cancelButton.disabled = true;

        // Replace current text with a loading indicator
        const originalText = modalBody.innerHTML;
        modalBody.innerHTML = `
            <div class="text-center">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Deleting group set...</span>
                </div>
                <p class="mt-2">Deleting group set and updating Canvas...</p>
                <p class="text-muted small">This may take a moment to complete.</p>
            </div>
        `;

        // Get course ID from the page URL
        const courseId = document.querySelector('meta[name="course-id"]').content;

        fetch(`/canvas/course/${courseId}/group_set/${categoryId}/delete/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Show success message using notify instead of alert
                if (typeof $ !== 'undefined' && typeof $.notify === 'function') {
                    $.notify({
                        message: data.message
                    }, {
                        type: 'success',
                        placement: { from: 'top', align: 'center' },
                        z_index: 2000,
                        delay: 3000
                    });
                }

                // Reload the page
                window.location.reload();
            } else {
                // Restore original modal content
                if (modalBody) modalBody.innerHTML = originalText;

                // Re-enable buttons
                if (confirmButton) confirmButton.disabled = false;
                if (closeButton) closeButton.disabled = false;
                if (cancelButton) cancelButton.disabled = false;

                // Show error message
                if (typeof $ !== 'undefined' && typeof $.notify === 'function') {
                    $.notify({
                        message: `Error: ${data.error}`
                    }, {
                        type: 'danger',
                        placement: { from: 'top', align: 'center' },
                        z_index: 2000,
                        delay: 5000
                    });
                } else {
                    alert(`Error: ${data.error}`);
                }
            }
        })
        .catch(error => {
            console.error('Error deleting group set:', error);

            // Restore original modal content
            if (modalBody) modalBody.innerHTML = originalText;

            // Re-enable buttons
            if (confirmButton) confirmButton.disabled = false;
            if (closeButton) closeButton.disabled = false;
            if (cancelButton) cancelButton.disabled = false;

            // Show error message
            if (typeof $ !== 'undefined' && typeof $.notify === 'function') {
                $.notify({
                    message: 'An error occurred while deleting the group set. Please try again.'
                }, {
                    type: 'danger',
                    placement: { from: 'top', align: 'center' },
                    z_index: 2000,
                    delay: 5000
                });
            } else {
                alert('An error occurred while deleting the group set. Please try again.');
            }
        });
    }

    // Function to load group set data
    function loadGroupSetData(categoryId) {
        const container = document.getElementById(`groups-container-${categoryId}`);
        const loadingElement = document.getElementById(`loading-${categoryId}`);

        if (container) {
            // Only fetch if not already loaded
            if (container.getAttribute('data-loaded') !== 'true') {
                if (loadingElement) {
                    loadingElement.style.display = 'block';
                }

                // Get course ID from the page meta tag
                const courseId = document.querySelector('meta[name="course-id"]').content;

                // Fetch the data for this group set
                fetch(`/canvas/course/${courseId}/group_set/${categoryId}/details/`)
                    .then(response => {
                        if (!response.ok) {
                            throw new Error('Error fetching group set data');
                        }
                        return response.json();
                    })
                    .then(data => {
                        renderGroupSetData(categoryId, data);
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        if (container) {
                            container.innerHTML = `<div class="alert alert-danger" role="alert">
                                <h4 class="alert-heading">Error Loading Data</h4>
                                <p><i class="fa fa-exclamation-circle me-2"></i> Error loading group data: ${error.message}</p>
                            </div>`;
                            container.style.display = 'block';
                        }
                    })
                    .finally(() => {
                        if (loadingElement) {
                            loadingElement.style.display = 'none';
                        }
                    });
            }
        }
    }

    // Function to render group set data
    function renderGroupSetData(categoryId, data) {
        const container = document.getElementById(`groups-container-${categoryId}`);
        if (!container) return;

        // Verify we have all necessary data
        if (!data) {
            container.innerHTML = '<div class="alert alert-danger" role="alert"><h4 class="alert-heading">Error</h4><p><i class="fa fa-exclamation-circle me-2"></i> No data received from server</p></div>';
            return;
        }

        // Make sure we have a category object
        if (!data.category) {
            data.category = { id: categoryId, name: "Unknown" };
        }

        // Make sure we have a groups array
        if (!data.groups) {
            data.groups = [];
        }

        // Make sure we have an unassigned_students array
        if (!data.unassigned_students) {
            data.unassigned_students = [];
        }

        // Add course reference for creating links
        if (!data.course) {
            // Try to get from URL
            const courseIdMatch = window.location.pathname.match(/\/course\/(\d+)/);
            if (courseIdMatch && courseIdMatch[1]) {
                data.course = { id: courseIdMatch[1] };
            }
        }

        // Clear existing content
        container.innerHTML = '';

        // Set data-category-id on the tab pane for easier access
        const tabPane = document.getElementById(`groupset-${categoryId}-content`);
        if (tabPane) {
            tabPane.setAttribute('data-category-id', categoryId);
        }

        // Create row for groups
        const row = document.createElement('div');
        row.className = 'row';

        // Check if there are any groups
        const hasGroups = data.groups && data.groups.length > 0;

        // Render each group
        if (hasGroups) {
            data.groups.forEach(group => {
                const col = document.createElement('div');
                col.className = 'col-md-4 col-sm-6 mb-3';

                // Clone group template
                const template = document.getElementById('group-template');
                const groupCard = template.content.cloneNode(true);

                // Add data attributes to the card for drag-and-drop
                const cardElement = groupCard.querySelector('.group-card');
                cardElement.setAttribute('data-group-id', group.id);
                cardElement.setAttribute('data-canvas-group-id', group.canvas_id);

                // Fill group data
                groupCard.querySelector('.group-name').textContent = group.name;

                // Set up edit link
                const editLink = groupCard.querySelector('.edit-group-btn');
                const courseId = document.querySelector('meta[name="course-id"]').content;
                editLink.href = `/canvas/course/${courseId}/group/${group.id}/edit/`;

                // Set up delete button
                const deleteBtn = groupCard.querySelector('.delete-group-btn');
                deleteBtn.setAttribute('data-group-id', group.id);
                deleteBtn.setAttribute('data-group-name', group.name);
                // Delete button handling is delegated to delete-group-modal.js

                const description = groupCard.querySelector('.group-description');
                if (group.description) {
                    description.textContent = group.description;
                } else {
                    description.textContent = 'No description';
                }

                // Fill member list
                const membersList = groupCard.querySelector('.members-list');
                membersList.classList.add('sortable-container');

                if (group.members && group.members.length > 0) {
                    group.members.forEach(member => {
                        const memberTemplate = document.getElementById('member-template');
                        const memberItem = memberTemplate.content.cloneNode(true);

                        // Add data attributes for drag-and-drop
                        const li = memberItem.querySelector('.student-item');
                        li.setAttribute('data-student-id', member.user_id);
                        li.setAttribute('data-student-name', member.name);
                        li.setAttribute('data-student-email', member.email || '');

                        memberItem.querySelector('.member-name').textContent = member.name;
                        memberItem.querySelector('.student-email').textContent = member.email || '';

                        membersList.appendChild(memberItem);
                    });
                } else {
                    const emptyItem = document.createElement('div');
                    emptyItem.className = 'empty-group-placeholder';
                    emptyItem.innerHTML = '<i class="fa fa-users me-2"></i>No members - drag students here';
                    membersList.appendChild(emptyItem);
                }

                col.appendChild(groupCard);
                row.appendChild(col);
            });
        } else {
            // Show message if no groups exist
            const noGroupsCol = document.createElement('div');
            noGroupsCol.className = 'col-12 mb-3';

            const noGroupsCard = document.createElement('div');
            noGroupsCard.className = 'card no-groups-message';

            const cardBody = document.createElement('div');
            cardBody.className = 'card-body text-center py-4';

            const icon = document.createElement('i');
            icon.className = 'fa fa-users-slash fa-3x mb-3 text-muted';

            const heading = document.createElement('h5');
            heading.className = 'mb-3';
            heading.textContent = 'No Groups Available';

            const message = document.createElement('p');
            message.className = 'mb-3';
            message.textContent = 'There are no groups in this category yet. Create groups to manually or randomly assign students.';

            // Get course ID from meta tag or data
            const courseId = document.querySelector('meta[name="course-id"]')?.content ||
                            (data.course && data.course.id ? data.course.id : null);

            const createGroupBtn = document.createElement('a');
            if (courseId && data.category && data.category.id) {
                createGroupBtn.href = `/canvas/course/${courseId}/group_set/${data.category.id}/group/create/`;
                createGroupBtn.className = 'btn btn-primary btn-round';
                createGroupBtn.innerHTML = '<i class="fa fa-plus"></i> Create Group';
            } else {
                // If we can't build the URL, make it a disabled button instead
                createGroupBtn.className = 'btn btn-secondary btn-round disabled';
                createGroupBtn.innerHTML = '<i class="fa fa-plus"></i> Create Group';
                createGroupBtn.setAttribute('aria-disabled', 'true');
            }

            cardBody.appendChild(icon);
            cardBody.appendChild(heading);
            cardBody.appendChild(message);
            cardBody.appendChild(createGroupBtn);

            noGroupsCard.appendChild(cardBody);
            noGroupsCol.appendChild(noGroupsCard);
            row.appendChild(noGroupsCol);
        }

        // Add unassigned students if any
        if (data.unassigned_students && data.unassigned_students.length > 0) {
            const col = document.createElement('div');
            col.className = 'col-md-4 col-sm-6 mb-3';

            const template = document.getElementById('unassigned-students-template');
            const unassignedCard = template.content.cloneNode(true);

            // Add class to unassigned card for identification
            const unassignedCardElement = unassignedCard.querySelector('.unassigned-students-card');
            unassignedCardElement.setAttribute('data-is-unassigned', 'true');

            const unassignedList = unassignedCard.querySelector('.unassigned-list');
            const randomAssignBtn = unassignedCard.querySelector('.random-assign-btn');

            // Set category data for random assignment if available
            if (data.category && data.category.id) {
                randomAssignBtn.setAttribute('data-category-id', data.category.id);
            }

            // Disable random assign button if there are no groups
            if (!hasGroups) {
                randomAssignBtn.disabled = true;
                randomAssignBtn.setAttribute('title', 'Create groups first before randomly assigning students');
                randomAssignBtn.classList.add('disabled');

                // Add info icon with tooltip
                const infoIcon = document.createElement('i');
                infoIcon.className = 'fa fa-info-circle ms-1';
                infoIcon.setAttribute('title', 'Create groups first before randomly assigning students');
                randomAssignBtn.appendChild(infoIcon);
            } else {
                // Add event listener for random assignment (only if groups exist)
                randomAssignBtn.addEventListener('click', function() {
                    randomAssignStudents(data.category.id);
                });
            }

            // Add sortable class to unassigned list
            unassignedList.classList.add('sortable-container');

            data.unassigned_students.forEach(student => {
                const memberTemplate = document.getElementById('member-template');
                const memberItem = memberTemplate.content.cloneNode(true);

                // Add data attributes for drag-and-drop
                const li = memberItem.querySelector('.student-item');
                li.setAttribute('data-student-id', student.user_id);
                li.setAttribute('data-student-name', student.user_name);
                li.setAttribute('data-student-email', student.email || '');

                memberItem.querySelector('.member-name').textContent = student.user_name;
                memberItem.querySelector('.student-email').textContent = student.email || '';

                unassignedList.appendChild(memberItem);
            });

            col.appendChild(unassignedCard);
            row.appendChild(col);
        }

        container.appendChild(row);
        container.setAttribute('data-loaded', 'true');
        container.style.display = 'block';

        // Dispatch custom event to initialize sortable
        document.dispatchEvent(new CustomEvent('groupDataLoaded', {
            detail: { categoryId: categoryId }
        }));
    }

    // Function to sync groups
    function syncGroups() {
        // Show sync progress
        const syncProgress = document.getElementById('syncProgress');
        const syncProgressBar = document.getElementById('syncProgressBar');
        const syncStatusMessage = document.getElementById('syncStatusMessage');

        syncProgress.style.display = 'block';
        syncProgressBar.style.width = '0%';
        syncStatusMessage.textContent = 'Starting group sync...';

        // Disable sync button
        const syncButton = document.getElementById('syncGroupsBtn');
        if (syncButton) {
            syncButton.disabled = true;
        }

        // Get course ID from the page meta tag
        const courseId = document.querySelector('meta[name="course-id"]').content;

        // Use the groups-specific sync endpoint for better efficiency
        fetch(`/canvas/course/${courseId}/sync_groups/`, {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => {
            // The sync happens in the background, so we'll poll for progress
            checkSyncProgress();
        })
        .catch(error => {
            console.error('Error starting sync:', error);
            syncStatusMessage.textContent = 'Error starting sync: ' + error.message;
            if (syncButton) {
                syncButton.disabled = false;
            }
        });
    }

    // Function to check sync progress
    function checkSyncProgress() {
        const courseId = document.querySelector('meta[name="course-id"]').content;
        const intervalId = setInterval(() => {
            fetch(`/canvas/sync_progress/?course_id=${courseId}`)
                .then(response => response.json())
                .then(data => {
                    updateProgressUI(data);

                    // Check if sync is complete
                    if (data.status === 'completed' || data.status === 'error') {
                        clearInterval(intervalId);

                        // Re-enable sync button
                        const syncButton = document.getElementById('syncGroupsBtn');
                        if (syncButton) {
                            syncButton.disabled = false;
                        }

                        // Reload the page after a slight delay if successful
                        if (data.status === 'completed') {
                            setTimeout(() => {
                                window.location.reload();
                            }, 1500);
                        }
                    }
                })
                .catch(error => {
                    console.error('Error checking sync progress:', error);
                    clearInterval(intervalId);

                    // Re-enable sync button
                    const syncButton = document.getElementById('syncGroupsBtn');
                    if (syncButton) {
                        syncButton.disabled = false;
                    }
                });
        }, 1000); // Poll every second
    }

    // Function to update progress UI
    function updateProgressUI(data) {
        const syncProgressBar = document.getElementById('syncProgressBar');
        const syncStatusMessage = document.getElementById('syncStatusMessage');

        if (data.current !== undefined && data.total !== undefined) {
            const percent = (data.current / data.total) * 100;
            syncProgressBar.style.width = `${percent}%`;
        }

        if (data.message) {
            syncStatusMessage.textContent = data.message;
        }

        // Update progress bar class based on status
        if (data.status === 'completed') {
            syncProgressBar.className = 'progress-bar progress-bar-success';
        } else if (data.status === 'error') {
            syncProgressBar.className = 'progress-bar progress-bar-danger';
        } else {
            syncProgressBar.className = 'progress-bar progress-bar-primary';
        }
    }
});