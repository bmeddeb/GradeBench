/**
 * Canvas Group Management - Drag and Drop with SortableJS (DEBUG VERSION 3)
 * Implements student assignment to groups via drag and drop with enhanced debugging.
 * This version makes entire items draggable and gets course ID from URL.
 */

// Immediately log when the script starts loading
console.log('📂 [SORTABLE-DEBUG-V3] Script starting to load...');

// Function to extract course ID from URL
function getCourseIdFromURL() {
    const path = window.location.pathname;
    const regex = /\/canvas\/course\/(\d+)/;
    const match = path.match(regex);
    
    if (match && match[1]) {
        console.log(`✅ [SORTABLE-DEBUG-V3] Extracted course ID from URL: ${match[1]}`);
        return match[1];
    }
    
    console.error('❌ [SORTABLE-DEBUG-V3] Could not extract course ID from URL path:', path);
    return null;
}

// Function to visually highlight drag items for debugging
function highlightDragItems() {
    console.log('🔍 [SORTABLE-DEBUG-V3] Highlighting draggable items for visibility');
    const studentItems = document.querySelectorAll('.student-item');
    
    studentItems.forEach(item => {
        // Add a temporary visual indicator for debugging
        item.setAttribute('data-debug-draggable', 'true');
        
        // Add inline styles to make items very obvious
        item.style.border = '2px solid #2196F3';
        item.style.backgroundColor = 'rgba(33, 150, 243, 0.1)';
        item.style.cursor = 'grab';
        
        // Log each item found
        console.log('✅ [SORTABLE-DEBUG-V3] Found draggable item:', item);
    });
    
    console.log(`📊 [SORTABLE-DEBUG-V3] Total draggable items found: ${studentItems.length}`);
}

// Function to check if SortableJS is working by creating a test instance
function testSortableJS() {
    console.log('🧪 [SORTABLE-DEBUG-V3] Testing if SortableJS is functional');
    
    try {
        // Create a temporary test element
        const testDiv = document.createElement('div');
        testDiv.id = 'sortable-test-container';
        testDiv.innerHTML = `
            <ul id="sortable-test-list">
                <li>Test Item 1</li>
                <li>Test Item 2</li>
                <li>Test Item 3</li>
            </ul>
        `;
        
        // Hide it but append to body
        testDiv.style.position = 'absolute';
        testDiv.style.left = '-9999px';
        testDiv.style.top = '-9999px';
        document.body.appendChild(testDiv);
        
        // Try to create a Sortable instance
        const testList = document.getElementById('sortable-test-list');
        if (!testList) {
            console.error('❌ [SORTABLE-DEBUG-V3] Test list element not found');
            return false;
        }
        
        const testSortable = new Sortable(testList, {
            animation: 150
        });
        
        // Check if the instance was created
        if (testSortable) {
            console.log('✅ [SORTABLE-DEBUG-V3] SortableJS test instance created successfully');
            // Clean up
            testSortable.destroy();
            document.body.removeChild(testDiv);
            return true;
        } else {
            console.error('❌ [SORTABLE-DEBUG-V3] Failed to create test Sortable instance');
            return false;
        }
    } catch (err) {
        console.error('❌ [SORTABLE-DEBUG-V3] Error testing SortableJS:', err);
        return false;
    }
}

document.addEventListener('DOMContentLoaded', function() {
    console.log('📂 [SORTABLE-DEBUG-V3] DOM fully loaded, checking for SortableJS');
    
    // Add visual indicator for script loading
    const debugIndicator = document.createElement('div');
    debugIndicator.style.position = 'fixed';
    debugIndicator.style.bottom = '10px';
    debugIndicator.style.right = '10px';
    debugIndicator.style.backgroundColor = 'rgba(33, 150, 243, 0.8)';
    debugIndicator.style.color = 'white';
    debugIndicator.style.padding = '5px 10px';
    debugIndicator.style.borderRadius = '5px';
    debugIndicator.style.zIndex = '9999';
    debugIndicator.style.fontSize = '12px';
    debugIndicator.style.fontFamily = 'monospace';
    debugIndicator.textContent = '🔍 SortableJS Debug V3 Active';
    document.body.appendChild(debugIndicator);
    
    // Verify SortableJS is available
    if (typeof Sortable === 'undefined') {
        console.error('❌ [SORTABLE-DEBUG-V3] SortableJS is not loaded. Drag and drop will not work.');
        debugIndicator.style.backgroundColor = 'rgba(255, 0, 0, 0.8)';
        debugIndicator.textContent = '❌ SortableJS Not Loaded!';
        
        if (typeof $ !== 'undefined' && typeof $.notify === 'function') {
            $.notify({
                message: 'SortableJS is not loaded. Drag and drop will not work.'
            }, {
                type: 'danger',
                placement: { from: 'top', align: 'center' },
                z_index: 2000,
                delay: 5000
            });
        } else {
            alert('SortableJS is not loaded. Drag and drop will not work.');
        }
        return;  // Exit early if SortableJS isn't available
    } else {
        console.log('✅ [SORTABLE-DEBUG-V3] SortableJS is available:', Sortable.version || 'unknown version');
        
        // Test if SortableJS is actually working
        if (!testSortableJS()) {
            debugIndicator.style.backgroundColor = 'rgba(255, 165, 0, 0.8)';
            debugIndicator.textContent = '⚠️ SortableJS Test Failed!';
        }
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
    
    console.log('🔍 [SORTABLE-DEBUG-V3] Checking DOM elements:');
    console.log('- saveChangesBanner:', saveChangesBanner ? 'found ✅' : 'missing ❌');
    console.log('- saveChangesBtn:', saveChangesBtn ? 'found ✅' : 'missing ❌');
    console.log('- discardChangesBtn:', discardChangesBtn ? 'found ✅' : 'missing ❌');
    
    // Listen for group data loaded event
    document.addEventListener('groupDataLoaded', function(e) {
        console.log('📂 [SORTABLE-DEBUG-V3] groupDataLoaded event received:', e.detail);
        
        const categoryId = e.detail.categoryId;
        currentCategoryId = categoryId;
        
        console.log(`🔄 [SORTABLE-DEBUG-V3] Preparing to initialize sortables for category ${categoryId}`);
        
        // Remove all previous sortable instances to avoid duplicates
        removeSortableInstances();
        
        // Increase the delay to ensure DOM is fully ready
        console.log(`⏱️ [SORTABLE-DEBUG-V3] Setting timeout of 500ms to ensure DOM is ready`);
        setTimeout(() => {
            // First highlight drag items for visibility
            highlightDragItems();
            
            // Then initialize sortables
            initSortables(categoryId);
            captureOriginalAssignments();
        }, 500);  // Increased from 100ms to 500ms
    });
    
    // Initialize Sortable.js for all group lists and the unassigned list
    function initSortables(categoryId) {
        console.log(`🚀 [SORTABLE-DEBUG-V3] Initializing Sortable.js for category ${categoryId}`);
        
        // Find all member lists in this category's tab
        const tabContent = document.getElementById(`groupset-${categoryId}-content`);
        if (!tabContent) {
            console.error(`❌ [SORTABLE-DEBUG-V3] Tab content not found for category ${categoryId}`);
            return;
        }
        
        console.log(`✅ [SORTABLE-DEBUG-V3] Found tab content:`, tabContent);
        
        // Get all group member lists
        const memberLists = tabContent.querySelectorAll('.members-list');
        console.log(`📊 [SORTABLE-DEBUG-V3] Found ${memberLists.length} member lists`);
        
        // Detailed logging of each member list
        memberLists.forEach((list, index) => {
            console.log(`📋 [SORTABLE-DEBUG-V3] Member list #${index+1}:`, list);
            console.log(`- Parent card:`, list.closest('.card'));
            console.log(`- Contains ${list.children.length} children`);
            
            // Check if the list has proper styling
            const computedStyle = window.getComputedStyle(list);
            console.log(`- CSS min-height: ${computedStyle.minHeight}`);
            console.log(`- CSS position: ${computedStyle.position}`);
            
            // Log all data attributes of the parent card
            const parentCard = list.closest('.card');
            if (parentCard) {
                console.log('- Parent card dataset:', parentCard.dataset);
                
                // Add visual indicator to each list
                list.style.border = '2px dashed blue';
                list.setAttribute('data-debug-list', `list-${index}`);
            }
        });
        
        // Create a Sortable instance for each members list
        memberLists.forEach((list, index) => {
            try {
                // Check if this is a group card list or unassigned list
                const cardElement = list.closest('.card');
                if (!cardElement) {
                    console.warn(`❌ [SORTABLE-DEBUG-V3] Could not find card for list #${index}`, list);
                    return;
                }
                
                // Check if it's an unassigned list
                if (cardElement.classList.contains('unassigned-students-card')) {
                    // Skip - we'll handle the unassigned list separately
                    console.log('🔄 [SORTABLE-DEBUG-V3] Skipping unassigned list - will initialize separately');
                    return;
                }
                
                // It's a group card
                const groupId = cardElement.dataset.groupId;
                console.log(`🔍 [SORTABLE-DEBUG-V3] Processing group card with ID: ${groupId || 'MISSING'}`);
                
                if (!groupId) {
                    console.warn('❌ [SORTABLE-DEBUG-V3] Group card is missing data-group-id attribute', cardElement);
                    
                    // Log all attributes for debugging
                    console.log('Card element attributes:');
                    Array.from(cardElement.attributes).forEach(attr => {
                        console.log(`- ${attr.name}: ${attr.value}`);
                    });
                    
                    // Try looking for the ID in parent elements
                    let parent = cardElement.parentElement;
                    while (parent && !groupId) {
                        if (parent.dataset.groupId) {
                            console.log(`🔍 [SORTABLE-DEBUG-V3] Found group ID in parent:`, parent.dataset.groupId);
                        }
                        parent = parent.parentElement;
                    }
                    
                    // Try to initialize anyway using a fallback ID
                    const fallbackId = 'unknown-' + Math.random().toString(36).substr(2, 9);
                    console.log(`🔧 [SORTABLE-DEBUG-V3] Using fallback ID for group: ${fallbackId}`);
                    
                    // Add debug class to card
                    cardElement.classList.add('sortable-debug-missing-id');
                    cardElement.style.border = '3px solid red';
                    
                    // Create a new Sortable instance with the fallback ID
                    try {
                        sortableInstances[`group-${fallbackId}`] = new Sortable(list, {
                            group: `category-${categoryId}`,
                            animation: 150,
                            // No handle - entire item is draggable
                            chosenClass: 'sortable-chosen',
                            dragClass: 'sortable-drag',
                            ghostClass: 'sortable-ghost',
                            
                            // Add additional debug callbacks
                            onStart: function(evt) {
                                console.log('🔄 [SORTABLE-DEBUG-V3] Drag started on fallback group:', evt.item);
                            },
                            onEnd: function(evt) {
                                console.log('🔄 [SORTABLE-DEBUG-V3] Drag ended on fallback group:', evt.item);
                            },
                            onChoose: function(evt) {
                                console.log('🔄 [SORTABLE-DEBUG-V3] Item chosen in fallback group:', evt.item);
                            },
                            onUnchoose: function(evt) {
                                console.log('🔄 [SORTABLE-DEBUG-V3] Item unchosen in fallback group:', evt.item);
                            }
                        });
                        console.log(`✅ [SORTABLE-DEBUG-V3] Created fallback Sortable instance for group-${fallbackId}`);
                    } catch (err) {
                        console.error(`❌ [SORTABLE-DEBUG-V3] Failed to create fallback Sortable:`, err);
                    }
                    return;
                }
                
                try {
                    // Add debug style to list
                    list.style.border = '2px solid green';
                    list.setAttribute('data-debug-init', 'true');
                    
                    console.log(`🔄 [SORTABLE-DEBUG-V3] Creating Sortable for group-${groupId}`, list);
                    
                    const sortable = new Sortable(list, {
                        group: `category-${categoryId}`,  // Group name to allow dragging between lists
                        animation: 150,                    // Animation speed in ms
                        // No handle - entire item is draggable
                        chosenClass: 'sortable-chosen',    // Class for chosen item
                        dragClass: 'sortable-drag',        // Class for dragging item
                        ghostClass: 'sortable-ghost',      // Class for drop placeholder
                        forceFallback: false,              // Force fallback
                        fallbackClass: 'sortable-fallback',// Class for fallback
                        scroll: true,                      // Enable scrolling in lists
                        bubbleScroll: true,                // Bubble scroll through parents
                        scrollSensitivity: 80,             // Scroll sensitivity in px
                        scrollSpeed: 10,                   // Scroll speed in px/s
                        
                        // Debug callbacks
                        onStart: function(evt) {
                            console.log(`🔄 [SORTABLE-DEBUG-V3] Drag started on group-${groupId}:`, evt.item);
                        },
                        onEnd: function(evt) {
                            console.log(`🔄 [SORTABLE-DEBUG-V3] Drag ended on group-${groupId}:`, evt.item);
                        },
                        onChoose: function(evt) {
                            console.log(`🔄 [SORTABLE-DEBUG-V3] Item chosen in group-${groupId}:`, evt.item);
                            
                            // Add visual feedback
                            evt.item.style.boxShadow = '0 0 10px rgba(0,128,0,0.5)';
                        },
                        onUnchoose: function(evt) {
                            console.log(`🔄 [SORTABLE-DEBUG-V3] Item unchosen in group-${groupId}:`, evt.item);
                            
                            // Remove visual feedback
                            evt.item.style.boxShadow = '';
                        },
                        
                        // Element is dragged from one list to another
                        onAdd: function(evt) {
                            const studentId = evt.item.dataset.studentId;
                            const newGroupId = groupId;
                            const fromElement = evt.from.closest('.card');
                            const oldGroupId = fromElement ? fromElement.dataset.groupId : null;
                            
                            console.log(`✅ [SORTABLE-DEBUG-V3] Student ${studentId} moved from ${oldGroupId || 'unassigned'} to ${newGroupId || 'unassigned'}`);
                            
                            // Mark unsaved changes and show banner
                            if (!hasUnsavedChanges) {
                                hasUnsavedChanges = true;
                                showSaveChangesBanner();
                            }
                        }
                    });
                    
                    sortableInstances[`group-${groupId}`] = sortable;
                    console.log(`✅ [SORTABLE-DEBUG-V3] Successfully created Sortable instance for group-${groupId}`);
                } catch (err) {
                    console.error(`❌ [SORTABLE-DEBUG-V3] Error creating regular Sortable instance for group-${groupId}:`, err);
                }
            } catch (err) {
                console.error(`❌ [SORTABLE-DEBUG-V3] Error in group list processing:`, err);
            }
        });
        
        // Get the unassigned students list
        const unassignedCard = tabContent.querySelector('.unassigned-students-card');
        const unassignedList = tabContent.querySelector('.unassigned-list');
        
        console.log('🔍 [SORTABLE-DEBUG-V3] Unassigned card:', unassignedCard);
        console.log('🔍 [SORTABLE-DEBUG-V3] Unassigned list:', unassignedList);
        
        if (unassignedList) {
            try {
                console.log('🔄 [SORTABLE-DEBUG-V3] Initializing unassigned list for category', categoryId);
                
                // Add debug visual cues
                unassignedList.style.border = '2px solid orange';
                unassignedList.setAttribute('data-debug-unassigned', 'true');
                
                // Create Sortable instance for the unassigned list
                const sortable = new Sortable(unassignedList, {
                    group: `category-${categoryId}`,  // Group name to allow dragging between lists
                    animation: 150,                    // Animation speed in ms
                    // No handle - entire item is draggable
                    chosenClass: 'sortable-chosen',    // Class for chosen item
                    dragClass: 'sortable-drag',        // Class for dragging item
                    ghostClass: 'sortable-ghost',      // Class for drop placeholder
                    forceFallback: false,              // Force fallback
                    fallbackClass: 'sortable-fallback',// Class for fallback
                    scroll: true,                      // Enable scrolling in lists
                    bubbleScroll: true,                // Bubble scroll through parents
                    scrollSensitivity: 80,             // Scroll sensitivity in px
                    scrollSpeed: 10,                   // Scroll speed in px/s
                    
                    // Debug callbacks
                    onStart: function(evt) {
                        console.log('🔄 [SORTABLE-DEBUG-V3] Drag started from unassigned list:', evt.item);
                    },
                    onEnd: function(evt) {
                        console.log('🔄 [SORTABLE-DEBUG-V3] Drag ended from unassigned list:', evt.item);
                    },
                    onChoose: function(evt) {
                        console.log('🔄 [SORTABLE-DEBUG-V3] Item chosen in unassigned list:', evt.item);
                        
                        // Add visual feedback
                        evt.item.style.boxShadow = '0 0 10px rgba(255,165,0,0.5)';
                    },
                    onUnchoose: function(evt) {
                        console.log('🔄 [SORTABLE-DEBUG-V3] Item unchosen in unassigned list:', evt.item);
                        
                        // Remove visual feedback
                        evt.item.style.boxShadow = '';
                    },
                    
                    // Element is dragged from one list to another
                    onAdd: function(evt) {
                        const studentId = evt.item.dataset.studentId;
                        const fromElement = evt.from.closest('.card');
                        let oldGroupId = null;
                        
                        // Try to get the group ID from the card element
                        if (fromElement && !fromElement.classList.contains('unassigned-students-card')) {
                            oldGroupId = fromElement.dataset.groupId;
                        }
                        
                        console.log(`✅ [SORTABLE-DEBUG-V3] Student ${studentId} moved from ${oldGroupId || 'unknown'} to unassigned`);
                        
                        // Mark unsaved changes and show banner
                        if (!hasUnsavedChanges) {
                            hasUnsavedChanges = true;
                            showSaveChangesBanner();
                        }
                    }
                });
                
                // Store the instance
                sortableInstances['unassigned'] = sortable;
                console.log('✅ [SORTABLE-DEBUG-V3] Successfully initialized unassigned list');
            } catch (err) {
                console.error('❌ [SORTABLE-DEBUG-V3] Error creating Sortable instance for unassigned list:', err);
            }
        } else {
            console.warn('❌ [SORTABLE-DEBUG-V3] Unassigned list not found in category', categoryId);
        }
        
        console.log('📊 [SORTABLE-DEBUG-V3] Sortable instances created:', Object.keys(sortableInstances));
    }
    
    // Remove all Sortable instances to avoid duplicate event handlers
    function removeSortableInstances() {
        console.log('🔄 [SORTABLE-DEBUG-V3] Removing existing Sortable instances');
        
        for (const key in sortableInstances) {
            if (sortableInstances[key]) {
                try {
                    console.log(`🔄 [SORTABLE-DEBUG-V3] Destroying instance: ${key}`);
                    sortableInstances[key].destroy();
                } catch (err) {
                    console.warn(`⚠️ [SORTABLE-DEBUG-V3] Error destroying sortable instance ${key}:`, err);
                }
                delete sortableInstances[key];
            }
        }
        
        console.log('✅ [SORTABLE-DEBUG-V3] All instances removed');
    }
    
    // Capture the original student assignments for comparison
    function captureOriginalAssignments() {
        console.log('🔄 [SORTABLE-DEBUG-V3] Capturing original assignments');
        originalAssignments = {};
        
        // If no category is loaded yet, return
        if (!currentCategoryId) {
            console.log('⚠️ [SORTABLE-DEBUG-V3] No current category, skipping assignment capture');
            return;
        }
        
        const tabContent = document.getElementById(`groupset-${currentCategoryId}-content`);
        if (!tabContent) {
            console.log('⚠️ [SORTABLE-DEBUG-V3] Tab content not found, skipping assignment capture');
            return;
        }
        
        // Get all student items in groups
        const groupCards = tabContent.querySelectorAll('.group-card');
        console.log(`🔍 [SORTABLE-DEBUG-V3] Found ${groupCards.length} group cards`);
        
        groupCards.forEach(card => {
            const groupId = card.dataset.groupId;
            const studentItems = card.querySelectorAll('.student-item');
            
            console.log(`🔍 [SORTABLE-DEBUG-V3] Group ${groupId} has ${studentItems.length} students`);
            
            studentItems.forEach(item => {
                const studentId = item.dataset.studentId;
                originalAssignments[studentId] = groupId;
                console.log(`🔍 [SORTABLE-DEBUG-V3] Student ${studentId} assigned to group ${groupId}`);
            });
        });
        
        // Get all unassigned students
        const unassignedStudents = tabContent.querySelectorAll('.unassigned-list .student-item');
        console.log(`🔍 [SORTABLE-DEBUG-V3] Found ${unassignedStudents.length} unassigned students`);
        
        unassignedStudents.forEach(item => {
            const studentId = item.dataset.studentId;
            originalAssignments[studentId] = null; // null means unassigned
            console.log(`🔍 [SORTABLE-DEBUG-V3] Student ${studentId} is unassigned`);
        });
        
        console.log('✅ [SORTABLE-DEBUG-V3] Original assignments captured:', originalAssignments);
    }
    
    // Get the current student assignments
    function getCurrentAssignments() {
        console.log('🔍 [SORTABLE-DEBUG-V3] Getting current assignments');
        const currentAssignments = {};
        
        // If no category is loaded yet, return empty object
        if (!currentCategoryId) {
            console.log('⚠️ [SORTABLE-DEBUG-V3] No current category, returning empty assignments');
            return currentAssignments;
        }
        
        const tabContent = document.getElementById(`groupset-${currentCategoryId}-content`);
        if (!tabContent) {
            console.log('⚠️ [SORTABLE-DEBUG-V3] Tab content not found, returning empty assignments');
            return currentAssignments;
        }
        
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
        
        console.log('✅ [SORTABLE-DEBUG-V3] Current assignments:', currentAssignments);
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
        console.log('🔄 [SORTABLE-DEBUG-V3] Showing save changes banner');
        if (saveChangesBanner) {
            saveChangesBanner.classList.add('visible');
        }
    }
    
    // Hide the save changes banner
    function hideSaveChangesBanner() {
        console.log('🔄 [SORTABLE-DEBUG-V3] Hiding save changes banner');
        if (saveChangesBanner) {
            saveChangesBanner.classList.remove('visible');
        }
    }
    
    // Save changes to the server
    async function saveChanges() {
        console.log('🔄 [SORTABLE-DEBUG-V3] Saving changes');
        if (!currentCategoryId) {
            console.log('⚠️ [SORTABLE-DEBUG-V3] No current category, cannot save changes');
            return;
        }
        
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
            console.log('ℹ️ [SORTABLE-DEBUG-V3] No changes to save');
            hasUnsavedChanges = false;
            hideSaveChangesBanner();
            return;
        }
        
        console.log(`🔄 [SORTABLE-DEBUG-V3] Saving ${changes.length} changes...`, changes);
        
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
            
            // Get course ID from URL instead of meta tag
            const courseId = getCourseIdFromURL();
            console.log('🔍 [SORTABLE-DEBUG-V3] Using course ID from URL:', courseId);
            
            if (!courseId) {
                throw new Error('Could not determine course ID from URL');
            }
            
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            console.log('🔍 [SORTABLE-DEBUG-V3] CSRF token available:', !!csrfToken);
            
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
            
            console.log('🔍 [SORTABLE-DEBUG-V3] Server response:', response.status, response.statusText);
            const data = await response.json();
            console.log('🔍 [SORTABLE-DEBUG-V3] Response data:', data);
            
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
                
                console.log('✅ [SORTABLE-DEBUG-V3] Changes saved successfully');
            } else {
                throw new Error(data.error || 'Unknown error saving changes');
            }
        } catch (error) {
            console.error('❌ [SORTABLE-DEBUG-V3] Error saving changes:', error);
            
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
        console.log('🔄 [SORTABLE-DEBUG-V3] Discarding changes');
        if (!currentCategoryId || !hasUnsavedChanges) {
            console.log('⚠️ [SORTABLE-DEBUG-V3] No current category or no changes, skipping discard');
            return;
        }
        
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
        if (typeof loadGroupSetData === 'function') {
            console.log('🔄 [SORTABLE-DEBUG-V3] Calling loadGroupSetData to reset state');
            loadGroupSetData(currentCategoryId);
        } else {
            console.warn('⚠️ [SORTABLE-DEBUG-V3] loadGroupSetData function not available');
        }
        
        // Reset flags and hide banner
        hasUnsavedChanges = false;
        hideSaveChangesBanner();
    }
    
    // Event listeners for banner buttons
    if (saveChangesBtn) {
        console.log('🔍 [SORTABLE-DEBUG-V3] Adding click listener to saveChangesBtn');
        saveChangesBtn.addEventListener('click', saveChanges);
    }
    
    if (discardChangesBtn) {
        console.log('🔍 [SORTABLE-DEBUG-V3] Adding click listener to discardChangesBtn');
        discardChangesBtn.addEventListener('click', discardChanges);
    }
    
    // Listen for tab changes
    const groupSetTabs = document.querySelectorAll('#groupSetTabs .nav-link');
    console.log(`🔍 [SORTABLE-DEBUG-V3] Found ${groupSetTabs.length} group set tabs`);
    
    groupSetTabs.forEach(tab => {
        tab.addEventListener('show.bs.tab', function(e) {
            console.log('🔍 [SORTABLE-DEBUG-V3] Tab change event:', e);
            
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
        console.log('🔄 [SORTABLE-DEBUG-V3] randomAssignStudents called for category', categoryId);
        if (!categoryId) {
            console.warn('⚠️ [SORTABLE-DEBUG-V3] No category ID provided for random assignment');
            return;
        }
        
        // Confirm with the user
        if (!confirm('Randomly assign all unassigned students to groups in this category?')) {
            console.log('ℹ️ [SORTABLE-DEBUG-V3] User cancelled random assignment');
            return;
        }
        
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
            
            // Get course ID from URL instead of meta tag
            const courseId = getCourseIdFromURL();
            if (!courseId) {
                throw new Error('Could not determine course ID from URL');
            }
            
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            
            console.log('🔍 [SORTABLE-DEBUG-V3] Random assign - Course ID:', courseId);
            console.log('🔍 [SORTABLE-DEBUG-V3] Random assign - CSRF token available:', !!csrfToken);
            
            const response = await fetch(`/canvas/course/${courseId}/group_set/${categoryId}/random_assign/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            console.log('🔍 [SORTABLE-DEBUG-V3] Random assign - Response:', response.status, response.statusText);
            const data = await response.json();
            console.log('🔍 [SORTABLE-DEBUG-V3] Random assign - Data:', data);
            
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
                    console.log('🔄 [SORTABLE-DEBUG-V3] Calling loadGroupSetData to refresh after random assignment');
                    loadGroupSetData(categoryId);
                } else {
                    console.warn('⚠️ [SORTABLE-DEBUG-V3] loadGroupSetData function not available, reloading page');
                    window.location.reload();
                }
                
                // Reset flags and hide banner if it was showing
                hasUnsavedChanges = false;
                hideSaveChangesBanner();
            } else {
                throw new Error(data.error || 'Unknown error during random assignment');
            }
        } catch (error) {
            console.error('❌ [SORTABLE-DEBUG-V3] Error during random assignment:', error);
            
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
                alert(`Error during random assignment: ${error.message}`);
            }
        }
    };
});