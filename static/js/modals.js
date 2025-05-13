/**
 * Modals helper utilities
 */

// Create a modal with a spinner for long-running operations
function createSpinnerModal(id, title, message, submessage) {
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.id = id;
    modal.setAttribute('tabindex', '-1');
    modal.setAttribute('aria-labelledby', `${id}Label`);
    modal.setAttribute('aria-hidden', 'true');
    modal.setAttribute('data-bs-backdrop', 'static');
    modal.setAttribute('data-bs-keyboard', 'false');
    
    modal.innerHTML = `
        <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="${id}Label">${title}</h5>
                </div>
                <div class="modal-body text-center">
                    <div class="spinner-border text-primary mb-3" role="status">
                        <span class="visually-hidden">Processing...</span>
                    </div>
                    <p>${message}</p>
                    ${submessage ? `<p class="text-muted small">${submessage}</p>` : ''}
                </div>
            </div>
        </div>
    `;
    
    return modal;
}

// Show a spinner modal
function showSpinnerModal(id, title, message, submessage) {
    // Remove any existing modal with the same ID
    const existingModal = document.getElementById(id);
    if (existingModal) {
        existingModal.remove();
    }
    
    // Create and add the modal
    const modal = createSpinnerModal(id, title, message, submessage);
    document.body.appendChild(modal);
    
    // Show the modal
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
    
    // Return the modal and its Bootstrap instance
    return { 
        element: modal, 
        instance: bsModal 
    };
}

// Hide and remove a modal safely
function removeModal(modalObj) {
    if (!modalObj) return;
    
    try {
        // Hide the modal
        if (modalObj.instance) {
            modalObj.instance.hide();
        }
        
        // Remove the element after a short delay
        setTimeout(() => {
            if (modalObj.element && document.body.contains(modalObj.element)) {
                document.body.removeChild(modalObj.element);
            }
        }, 300);
    } catch (error) {
        console.error('Error removing modal:', error);
    }
}