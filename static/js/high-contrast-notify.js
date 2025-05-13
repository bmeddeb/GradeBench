/**
 * High Contrast Bootstrap Notify
 * 
 * This script overrides the default bootstrap-notify settings
 * to provide more accessible, high-contrast notifications.
 */

// Wait for document to be ready
$(document).ready(function() {
    // Store the original $.notify function
    const originalNotify = $.notify;
    
    // If the notify function exists, override it
    if (typeof originalNotify === 'function') {
        // Override the notify function
        $.notify = function(content, options) {
            // Default options for high contrast
            const highContrastDefaults = {
                // Higher z-index to ensure visibility
                z_index: 10000,
                
                // Placement (no change from default, but explicit)
                placement: {
                    from: "top",
                    align: "right"
                },
                
                // Animation
                animate: {
                    enter: 'animated fadeInDown',
                    exit: 'animated fadeOutUp'
                },
                
                // Display time
                delay: 5000,
                
                // Template with improved contrast
                template: '<div data-notify="container" class="alert alert-{0}" role="alert">' +
                    '<button type="button" aria-hidden="true" class="close" data-notify="dismiss">&times;</button>' +
                    '<span data-notify="icon"></span> ' +
                    '<span data-notify="title"><strong>{1}</strong></span> ' +
                    '<span data-notify="message">{2}</span>' +
                    '<div class="progress" data-notify="progressbar">' +
                    '<div class="progress-bar progress-bar-{0}" role="progressbar" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100" style="width: 0%;"></div>' +
                    '</div>' +
                '</div>'
            };
            
            // Merge the high contrast defaults with user provided options
            const mergedOptions = $.extend(true, {}, highContrastDefaults, options || {});
            
            // Call the original notify function with our enhanced options
            return originalNotify.call(this, content, mergedOptions);
        };
        
        // Attach to console to log the override
        console.log('Bootstrap Notify has been enhanced with high contrast settings.');
    }

    // Create a helper function for showing alerts
    window.showHighContrastAlert = function(message, type, title) {
        // Default type to info if not provided
        type = type || 'info';
        
        // Set defaults based on type
        const iconMap = {
            success: 'fa fa-check-circle',
            danger: 'fa fa-exclamation-triangle',
            warning: 'fa fa-exclamation-circle',
            info: 'fa fa-info-circle',
            primary: 'fa fa-bell'
        };
        
        // Build the notify data
        const notifyData = {
            icon: iconMap[type] || iconMap.info,
            message: message
        };
        
        // Add title if provided
        if (title) {
            notifyData.title = title;
        }
        
        // Show the notification
        $.notify(notifyData, {
            type: type
        });
    };
});