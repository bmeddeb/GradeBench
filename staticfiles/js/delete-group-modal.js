/**
 * Handle group deletion with a modal spinner.
 * Shows a confirmation modal, then a spinner while the deletion is in progress.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Listen for delete group button clicks using event delegation
    document.addEventListener('click', function(e) {
        if (e.target && e.target.closest('.delete-group-btn')) {
            e.preventDefault();
            
            const btn = e.target.closest('.delete-group-btn');
            const groupId = btn.getAttribute('data-group-id');
            const groupName = btn.getAttribute('data-group-name');
            
            showDeleteConfirmation(groupId, groupName);
        }
    });
    
    // Function to show delete confirmation modal
    function showDeleteConfirmation(groupId, groupName) {
        // Create the confirmation modal
        let confirmModal = document.createElement('div');
        confirmModal.className = 'modal fade';
        confirmModal.id = 'deleteGroupConfirmModal';
        confirmModal.setAttribute('tabindex', '-1');
        confirmModal.setAttribute('aria-labelledby', 'deleteGroupConfirmModalLabel');
        confirmModal.setAttribute('aria-hidden', 'true');
        
        confirmModal.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="deleteGroupConfirmModalLabel">Confirm Delete</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <p>Are you sure you want to delete the group "${groupName}"?</p>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-danger" id="confirmDeleteGroupBtn">Delete</button>
                    </div>
                </div>
            </div>
        `;
        
        // Add modal to body
        document.body.appendChild(confirmModal);
        
        // Show the modal
        const bsConfirmModal = new bootstrap.Modal(confirmModal);
        bsConfirmModal.show();
        
        // Add event listener to the confirm button
        const confirmBtn = document.getElementById('confirmDeleteGroupBtn');
        confirmBtn.addEventListener('click', function() {
            bsConfirmModal.hide();
            
            // Remove the modal and proceed with deletion
            confirmModal.addEventListener('hidden.bs.modal', function() {
                try {
                    if (document.body.contains(confirmModal)) {
                        document.body.removeChild(confirmModal);
                    }
                } catch (e) {
                    console.warn('Modal already removed:', e);
                }
                // Proceed with group deletion
                deleteGroup(groupId, groupName);
            });
        });
        
        // Remove the modal when hidden
        confirmModal.addEventListener('hidden.bs.modal', function() {
            // Only remove if it hasn't been removed yet by the confirm action
            try {
                if (document.body.contains(confirmModal)) {
                    document.body.removeChild(confirmModal);
                }
            } catch (e) {
                console.warn('Modal already removed:', e);
            }
        });
    }
    
    // Function to delete a group with spinner modal
    function deleteGroup(groupId, groupName) {
        // Create a progress modal
        let progressModal = document.createElement('div');
        progressModal.className = 'modal fade';
        progressModal.id = 'deleteGroupProgressModal';
        progressModal.setAttribute('tabindex', '-1');
        progressModal.setAttribute('aria-labelledby', 'deleteGroupProgressModalLabel');
        progressModal.setAttribute('aria-hidden', 'true');
        progressModal.setAttribute('data-bs-backdrop', 'static');
        progressModal.setAttribute('data-bs-keyboard', 'false');
        
        progressModal.innerHTML = `
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="deleteGroupProgressModalLabel">Deleting Group</h5>
                    </div>
                    <div class="modal-body text-center">
                        <div class="spinner-border text-primary mb-3" role="status">
                            <span class="visually-hidden">Deleting group...</span>
                        </div>
                        <p>Deleting group "${groupName}" and updating Canvas...</p>
                        <p class="text-muted small">This may take a few moments. Please don't close this window.</p>
                    </div>
                </div>
            </div>
        `;
        
        // Add modal to body
        document.body.appendChild(progressModal);
        
        // Show the modal
        const bsProgressModal = new bootstrap.Modal(progressModal);
        bsProgressModal.show();
        
        // Get course ID and CSRF token
        const courseId = getCourseIdFromURL();
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        
        // Make the delete request
        fetch(`/canvas/course/${courseId}/group/${groupId}/delete/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            // Hide and remove the progress modal
            bsProgressModal.hide();
            setTimeout(() => {
                try {
                    if (document.body.contains(progressModal)) {
                        document.body.removeChild(progressModal);
                    }
                } catch (e) {
                    console.warn('Progress modal already removed:', e);
                }
            }, 300);
            
            if (data.success) {
                // Reload the active tab data
                const activeTab = document.querySelector('#groupSetTabs .nav-link.active');
                if (activeTab) {
                    const categoryId = activeTab.getAttribute('data-category-id');
                    const container = document.getElementById(`groups-container-${categoryId}`);
                    if (container) {
                        container.removeAttribute('data-loaded');
                    }
                    if (typeof loadGroupSetData === 'function') {
                        loadGroupSetData(categoryId);
                    } else {
                        window.location.reload();
                    }
                }
            } else {
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
            console.error('Error deleting group:', error);
            
            // Hide and remove the progress modal
            bsProgressModal.hide();
            setTimeout(() => {
                try {
                    if (document.body.contains(progressModal)) {
                        document.body.removeChild(progressModal);
                    }
                } catch (e) {
                    console.warn('Progress modal already removed:', e);
                }
            }, 300);
            
            // Show error message
            if (typeof $ !== 'undefined' && typeof $.notify === 'function') {
                $.notify({
                    message: 'An error occurred while deleting the group. Please try again.'
                }, {
                    type: 'danger',
                    placement: { from: 'top', align: 'center' },
                    z_index: 2000,
                    delay: 5000
                });
            } else {
                alert('An error occurred while deleting the group. Please try again.');
            }
        });
    }
    
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
});