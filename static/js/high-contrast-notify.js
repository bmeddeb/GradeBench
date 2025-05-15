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
            // Determine notification type and set up icon and title
            const type = options?.type || 'info';
            
            // Set defaults based on type (just the icon class, without fa prefix)
            const iconMap = {
                success: 'fa-check-circle me-2',
                danger: 'fa-exclamation-triangle me-2',
                warning: 'fa-exclamation-circle me-2',
                info: 'fa-info-circle me-2',
                primary: 'fa-bell me-2',
                error: 'fa-exclamation-triangle me-2' // For compatibility
            };
            
            // Default titles based on type
            const titleMap = {
                success: 'Success',
                danger: 'Error',
                warning: 'Warning',
                info: 'Information',
                primary: 'Notification',
                error: 'Error' // For compatibility
            };
            
            // Get appropriate icon and title based on content and type
            let iconClass = iconMap[type] || iconMap.info;
            let titleText = '';
            
            // Extract title from content if provided
            if (content && typeof content === 'object') {
                if (content.title) {
                    titleText = content.title;
                } else if (content.icon) {
                    // If icon is provided in content, we'll use that instead
                    iconClass = (content.icon.includes('fa-')) ? content.icon : iconMap[type];
                }
            }
            
            // If no title was extracted, use default
            if (!titleText) {
                titleText = titleMap[type] || titleMap.info;
            }
                        
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
                
                // Template with improved contrast matching static alerts with proper headings
                template: '<div data-notify="container" class="alert alert-{0}" role="alert">' +
                    '<button type="button" aria-hidden="true" class="btn-close" data-notify="dismiss" aria-label="Close"></button>' +
                    '<h5 class="alert-heading"><i class="fa ' + iconClass + '" aria-hidden="true"></i>' + titleText + '</h5>' +
                    '<p class="mb-0">{2}</p>' +
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
        
        // Set defaults based on type (just the icon class, without fa prefix)
        const iconMap = {
            success: 'fa-check-circle me-2',
            danger: 'fa-exclamation-triangle me-2',
            warning: 'fa-exclamation-circle me-2',
            info: 'fa-info-circle me-2',
            primary: 'fa-bell me-2'
        };
        
        // Default titles based on type
        const titleMap = {
            success: 'Success',
            danger: 'Error',
            warning: 'Warning',
            info: 'Information',
            primary: 'Notification'
        };
        
        // Get the icon class and title based on type
        const iconClass = iconMap[type] || iconMap.info;
        const titleText = title || titleMap[type] || titleMap.info;
        
        // With our new template format, we need to pass icon class and title separately
        $.notify({
            message: message
        }, {
            type: type,
            icon_type: 'class', 
            template: '<div data-notify="container" class="alert alert-{0}" role="alert">' +
                '<button type="button" aria-hidden="true" class="btn-close" data-notify="dismiss" aria-label="Close"></button>' +
                '<h5 class="alert-heading"><i class="fa ' + iconClass + '" aria-hidden="true"></i>' + titleText + '</h5>' +
                '<p class="mb-0">{2}</p>' +
                '<div class="progress" data-notify="progressbar">' +
                '<div class="progress-bar progress-bar-{0}" role="progressbar" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100" style="width: 0%;"></div>' +
                '</div>' +
            '</div>'
        });
        
        // No need to do anything else since we've already called $.notify
    };
});