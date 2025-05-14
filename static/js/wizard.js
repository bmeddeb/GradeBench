
// Ensure we have a safe initialization even if jQuery doesn't load properly
function safeInit() {
  console.log("Wizard.js - Safe initialization called");
  
  // Check if jQuery is available
  if (typeof $ === 'undefined' || typeof jQuery === 'undefined') {
    console.error("jQuery is not available. Wizard initialization postponed.");
    // Try again in 500ms
    setTimeout(safeInit, 500);
    return;
  }
  
  console.log("jQuery is available, version: " + jQuery.fn.jquery);
  
  // Ensure wizardContext exists
  if (typeof window.wizardContext === 'undefined') {
    console.log("Creating empty wizardContext");
    window.wizardContext = {
      current_step: 1,
      courses: [],
      group_sets: [],
      groups: [],
      created_teams: []
    };
  }
  
  // Initialize wizard
  console.log("Calling initializeWizard()");
  initializeWizard();
}

// Use both document ready and DOMContentLoaded for maximum compatibility
$(document).ready(function() {
  console.log("Wizard.js - jQuery document ready called");
  safeInit();
});

// Backup initialization if jQuery ready fails
document.addEventListener('DOMContentLoaded', function() {
  console.log("Wizard.js - DOMContentLoaded called");
  // If jQuery is already initialized, this will run immediately
  // Otherwise, it will wait for jQuery to load
  setTimeout(function() {
    if (typeof $ !== 'undefined' && typeof $.fn !== 'undefined') {
      console.log("jQuery is available from DOMContentLoaded");
    } else {
      console.log("jQuery not available from DOMContentLoaded, trying safe init");
    }
    safeInit();
  }, 100);
});

function initializeWizard() {
  console.log("Initializing wizard");
  
  // Safety check
  if (typeof $ === 'undefined') {
    console.error("jQuery still not available!");
    return;
  }
  var $wizardCard = $('.card-wizard');
  var $form = $wizardCard.find('form');
  
  // Set up CSRF token for AJAX requests
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }
  
  // Set up AJAX with CSRF token
  const csrftoken = getCookie('csrftoken');
  $.ajaxSetup({
    beforeSend: function(xhr, settings) {
      if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
        xhr.setRequestHeader("X-CSRFToken", csrftoken);
      }
    }
  });

  // Show wizard card (Paper Dashboard CSS hides it until .active)
  $wizardCard.addClass('active');
  
  // Use the data from Django directly for steps
  // We'll add empty placeholders here that'll be populated from the server
  // The step_data is provided in the template context, which is passed from the view
  
  // Get wizard context data from the server (Django template)
  console.log("Loading wizard context data from server");
  if (!window.wizardContext) {
    console.error("No wizard context found - data may not have been properly provided by the server");
  }
  
  // Populate course dropdown with data from Django
  const $courseSelect = $('#course_id');
  if ($courseSelect.length) {
    console.log("Populating course dropdown");
    $courseSelect.empty().append('<option value="">Please select a course</option>');
    
    // Parse courses from wizardContext if available (with safety check)
    const courses = window.wizardContext && window.wizardContext.courses ? window.wizardContext.courses : [];
    console.log("Courses found:", courses.length);
    
    // Add real courses from database to dropdown
    if (courses && courses.length) {
      courses.forEach(course => {
        if (course && course.canvas_id && course.course_code && course.name) {
          $courseSelect.append(`<option value="${course.canvas_id}">${course.course_code} - ${course.name}</option>`);
        } else {
          console.warn("Invalid course data:", course);
        }
      });
    } else {
      console.warn("No courses available in the database");
      $courseSelect.append('<option value="" disabled>No courses available - please import courses from Canvas</option>');
      
      // Show the warning message
      $('#no-courses-warning').show();
      
      // Disable next button since we can't proceed without courses
      $('#next-btn').prop('disabled', true);
    }
  } else {
    console.warn("Course select element not found");
  }
  
  // Course change handler to fetch group sets via AJAX
  $courseSelect.on('change', function() {
    const courseId = $(this).val();
    if (courseId) {
      console.log("Course selected:", courseId);
      
      // Store the course ID in a hidden field
      if (!$('input[name="course_id"]').length) {
        $form.append(`<input type="hidden" name="course_id" value="${courseId}">`);
      } else {
        $('input[name="course_id"]').val(courseId);
      }
      
      // Enable the Next button now that a course is selected
      $('#next-btn').prop('disabled', false);
      
      // In the real implementation, we would fetch group sets via AJAX here
      // For this implementation, we'll just let the navigation buttons handle it
      console.log("Course ID stored in hidden field. Will fetch group sets when moving to next step.");
    } else {
      // Disable Next button if no course is selected
      $('#next-btn').prop('disabled', true);
    }
  });
  
  // Function to update group sets based on selected course
  // This would be called when loading step 2 with data from Django
  function populateGroupSets() {
    const $groupSetsContainer = $('.group-sets-container');
    $groupSetsContainer.empty(); // Clear existing content
    
    // Group sets should be provided by the server in wizardContext
    const groupSets = window.wizardContext.group_sets || [];
    
    if (groupSets.length === 0) {
      // Show the no group sets warning
      $('#no-group-sets-warning').show();
      
      // Add informative message to the container
      $groupSetsContainer.append('<div class="alert alert-warning">No group sets found for this course. Please import group sets from Canvas first.</div>');
      
      // Disable next button since we can't proceed without group sets
      $('#next-btn').prop('disabled', true);
      return;
    } else {
      // Hide warning and enable next button
      $('#no-group-sets-warning').hide();
      $('#next-btn').prop('disabled', false);
    }
    
    // Populate with real data from database
    groupSets.forEach(groupSet => {
      $groupSetsContainer.append(`
        <div class="card mb-3">
          <div class="card-body">
            <div class="form-check form-check-inline">
              <input class="form-check-input" type="checkbox" name="group_set_ids" value="${groupSet.canvas_id}" id="group_set_${groupSet.canvas_id}" style="width: 20px; height: 20px; margin-right: 10px; visibility: visible !important; opacity: 1 !important;">
              <label class="form-check-label" for="group_set_${groupSet.canvas_id}">
                <strong>${groupSet.name}</strong> (${groupSet.group_count} groups)
              </label>
            </div>
          </div>
        </div>
      `);
    });
  }
  
  // Call populateGroupSets if we're on step 2
  if (window.wizardContext.current_step === 2) {
    populateGroupSets();
  }

  // Form validation
  var $validator = $form.validate({
    rules: {
      course_id: {
        required: true
      }
      // add more rules per field/step as needed
    },
    highlight: function(element) {
      $(element).closest('.mb-3').addClass('has-danger').removeClass('has-success');
    },
    success: function(label) {
      $(label).closest('.mb-3').addClass('has-success').removeClass('has-danger');
    }
  });

  // Fix for Bootstrap 5: Properly handle tab panes
  function fixTabPaneVisibility(index) {
    // Hide all tab panes first
    $('.tab-pane').removeClass('show active');
    
    // Show the target tab pane
    var targetId = '#step' + (index + 1);
    $(targetId).addClass('show active');
  }

  // Manual next button handler - now submits the form via AJAX
  $(document).on('click', '#next-btn, .btn-next', function() {
    var $activeTab = $('.nav-pills .nav-link.active');
    var $nextTab = $activeTab.parent().next().find('.nav-link');
    
    if ($nextTab.length > 0 && $form.valid()) {
      // Get the current step
      var currentIndex = $('.nav-pills .nav-link').index($activeTab);
      var nextIndex = currentIndex + 1;
      
      // Pre-process step data
      if (currentIndex === 1) { // Moving from step 2 to step 3
        // Process selected group sets and populate groups
        updateGroupsList();
      }
      
      if (currentIndex === 3) { // Moving from step 4 to step 5
        // Update summary based on selections
        updateSummary();
      }
      
      // Store the course ID in a global variable when moving to the results page
      if (currentIndex === 4) { // Moving from step 5 to step 6
        window.courseId = $('#course_id').val();
      }
      
      // AJAX "next" action to submit the form without page reload
      var formData = new FormData($form[0]);
      formData.append('action', 'next');
      
      console.log("Submitting form via AJAX to move to next step");
      $.ajax({
        url: $form.attr('action'),
        type: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        success: function(response) {
          console.log("AJAX form submission successful:", response);
          
          // Update wizard context with new data if provided
          if (response.wizard_data) {
            console.log("Received updated wizard_data from server:", response.wizard_data);
            window.wizardContext = response.wizard_data;
            
            // Parse JSON strings if needed
            if (typeof window.wizardContext.courses === 'string') {
              try {
                window.wizardContext.courses = JSON.parse(window.wizardContext.courses);
                console.log("Parsed courses from JSON string:", window.wizardContext.courses.length);
              } catch (e) {
                console.error("Error parsing courses JSON:", e);
                window.wizardContext.courses = [];
              }
            }
            
            if (typeof window.wizardContext.group_sets === 'string') {
              try {
                window.wizardContext.group_sets = JSON.parse(window.wizardContext.group_sets);
                console.log("Parsed group_sets from JSON string:", window.wizardContext.group_sets.length);
              } catch (e) {
                console.error("Error parsing group_sets JSON:", e);
                window.wizardContext.group_sets = [];
              }
            }
            
            if (typeof window.wizardContext.groups === 'string') {
              try {
                window.wizardContext.groups = JSON.parse(window.wizardContext.groups);
                console.log("Parsed groups from JSON string:", window.wizardContext.groups.length);
              } catch (e) {
                console.error("Error parsing groups JSON:", e);
                window.wizardContext.groups = [];
              }
            }
            
            if (typeof window.wizardContext.created_teams === 'string') {
              try {
                window.wizardContext.created_teams = JSON.parse(window.wizardContext.created_teams);
                console.log("Parsed created_teams from JSON string:", window.wizardContext.created_teams.length);
              } catch (e) {
                console.error("Error parsing created_teams JSON:", e);
                window.wizardContext.created_teams = [];
              }
            }
          }
          
          // Update current step
          window.wizardContext.current_step = nextIndex + 1;
          
          // Activate next tab
          $('.nav-pills .nav-link').removeClass('active');
          $nextTab.addClass('active');
          
          // Fix tab pane visibility
          fixTabPaneVisibility(nextIndex);
          
          // Update progress
          updateProgress(nextIndex);
          
          // Post-process tabs
          if (nextIndex === 1) { // Moving to step 2
            populateGroupSets();
          } else if (nextIndex === 2) { // Moving to step 3
            updateGroupsList();
          } else if (nextIndex === 4) { // Moving to step 5
            updateSummary();
          }
        },
        error: function(xhr, status, error) {
          console.error("Error submitting form:", error);
          console.error("Response:", xhr.responseText);
          alert("Error moving to next step: " + error);
        }
      });
    } else {
      console.log("Form validation failed or no next tab available");
    }
  });

  $(document).on('click', '#previous-btn, .btn-previous', function() {
    var $activeTab = $('.nav-pills .nav-link.active');
    var $prevTab = $activeTab.parent().prev().find('.nav-link');
    
    if ($prevTab.length > 0) {
      // Get the current step
      var currentIndex = $('.nav-pills .nav-link').index($activeTab);
      var prevIndex = currentIndex - 1;
      
      // AJAX "previous" action
      var formData = new FormData($form[0]);
      formData.append('action', 'previous');
      
      console.log("Submitting form via AJAX to move to previous step");
      $.ajax({
        url: $form.attr('action'),
        type: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        success: function(response) {
          console.log("AJAX form submission successful:", response);
          
          // Update wizard context with new data if provided
          if (response.wizard_data) {
            console.log("Received updated wizard_data from server:", response.wizard_data);
            window.wizardContext = response.wizard_data;
            
            // Parse JSON strings if needed
            if (typeof window.wizardContext.courses === 'string') {
              try {
                window.wizardContext.courses = JSON.parse(window.wizardContext.courses);
                console.log("Parsed courses from JSON string:", window.wizardContext.courses.length);
              } catch (e) {
                console.error("Error parsing courses JSON:", e);
                window.wizardContext.courses = [];
              }
            }
            
            if (typeof window.wizardContext.group_sets === 'string') {
              try {
                window.wizardContext.group_sets = JSON.parse(window.wizardContext.group_sets);
                console.log("Parsed group_sets from JSON string:", window.wizardContext.group_sets.length);
              } catch (e) {
                console.error("Error parsing group_sets JSON:", e);
                window.wizardContext.group_sets = [];
              }
            }
            
            if (typeof window.wizardContext.groups === 'string') {
              try {
                window.wizardContext.groups = JSON.parse(window.wizardContext.groups);
                console.log("Parsed groups from JSON string:", window.wizardContext.groups.length);
              } catch (e) {
                console.error("Error parsing groups JSON:", e);
                window.wizardContext.groups = [];
              }
            }
            
            if (typeof window.wizardContext.created_teams === 'string') {
              try {
                window.wizardContext.created_teams = JSON.parse(window.wizardContext.created_teams);
                console.log("Parsed created_teams from JSON string:", window.wizardContext.created_teams.length);
              } catch (e) {
                console.error("Error parsing created_teams JSON:", e);
                window.wizardContext.created_teams = [];
              }
            }
          }
          
          // Update current step
          window.wizardContext.current_step = prevIndex + 1;
          
          // Activate previous tab
          $('.nav-pills .nav-link').removeClass('active');
          $prevTab.addClass('active');
          
          // Fix tab pane visibility
          fixTabPaneVisibility(prevIndex);
          
          // Update progress
          updateProgress(prevIndex);
          
          // Post-process tabs
          if (prevIndex === 1) { // Moving back to step 2
            populateGroupSets();
          } else if (prevIndex === 2) { // Moving back to step 3
            updateGroupsList();
          }
        },
        error: function(xhr, status, error) {
          console.error("Error navigating to previous step:", error);
          console.error("Response:", xhr.responseText);
          
          // Fallback to simple navigation if AJAX fails
          $('.nav-pills .nav-link').removeClass('active');
          $prevTab.addClass('active');
          fixTabPaneVisibility(prevIndex);
          updateProgress(prevIndex);
        }
      });
    }
  });

  // Initialize wizard appearance
  initWizard();

  // Append progress bar
  var stepCount = $wizardCard.find('.wizard-navigation li').length;
  $wizardCard.find('.wizard-navigation').append(
    '<div class="progress mt-3">' +
      '<div class="progress-bar" role="progressbar" aria-valuemin="1" aria-valuemax="' + stepCount + '" style="width: 0%;"></div>' +
    '</div>'
  );

  // Set initial progress
  var initialIndex = $('.nav-pills .nav-link.active').parent().index();
  if (initialIndex < 0) {
    // Default to first tab if none is active
    initialIndex = 0;
    $('.nav-pills .nav-link').first().addClass('active');
  }
  updateProgress(initialIndex);
  
  // Handle direct tab clicks (ensure they go through the form submission)
  $('.nav-pills .nav-link').on('click', function(e) {
    e.preventDefault();
    
    // Don't allow direct clicking of tabs - must use next/previous buttons
    return false;
  });
  
  // Reset button handler
  $(document).on('click', '#reset-btn', function() {
    // Confirm reset
    if (confirm('Are you sure you want to restart the wizard? All progress will be lost.')) {
      // Reset form
      $form[0].reset();
      
      // Reset wizard state
      const $firstTab = $('.nav-pills .nav-link').first();
      $('.nav-pills .nav-link').removeClass('active');
      $firstTab.addClass('active');
      
      // Reset tab panes
      $('.tab-pane').removeClass('show active');
      $('#step1').addClass('show active');
      
      // Reset progress
      updateProgress(0);
      
      // Repopulate mock data
      // This will ensure the form fields are reset with fresh mock data
      $('#course_id').trigger('reset.mockdata');
    }
  });

  // Functions
  function initWizard() {
    // Create moving tab
    var firstTitle = $('.wizard-navigation li:first-child a').html();
    var $movingTab = $("<div class='moving-tab'></div>").append(firstTitle);
    $wizardCard.find('.wizard-navigation').append($movingTab);
    
    // Initial position
    var initialIndex = $('.nav-pills .nav-link.active').parent().index();
    refreshAnimation($wizardCard, initialIndex);
    
    // Fix initial tab pane visibility
    fixTabPaneVisibility(initialIndex);
    
    // Initial state
    updateTabState(initialIndex);
    
    // Handle window resize to adjust the moving tab
    $(window).resize(function() {
      // Recalculate moving tab position
      var activeIndex = $('.nav-pills .nav-link.active').parent().index();
      refreshAnimation($wizardCard, activeIndex);
    });
  }

  function updateTabState(index) {
    var total = $('.nav-pills .nav-link').length;
    var current = index + 1;
    
    // Update moving tab
    var activeText = $('.nav-pills li:nth-child(' + current + ') a').html();
    setTimeout(function() {
      $wizardCard.find('.moving-tab').html(activeText);
    }, 150);
    
    // Show/hide next/finish buttons
    if (current >= total) {
      $('#next-btn').hide();
      $('#finish-btn').show();
    } else {
      $('#next-btn').show();
      $('#finish-btn').hide();
    }
    
    refreshAnimation($wizardCard, index);
  }

  function updateProgress(index) {
    var total = $('.nav-pills .nav-link').length;
    var current = index + 1;
    var percent = (current / total) * 100;
    
    // Update progress bar
    $wizardCard.find('.progress-bar').css({ width: percent + '%' });
    
    // Update moving tab text and position
    updateTabState(index);
  }

  function refreshAnimation($wizard, index) {
    var total = $wizard.find('.wizard-navigation li').length;
    var moveDistance = $wizard.find('.wizard-navigation').width() / total;
    var $movingTab = $wizard.find('.moving-tab');
    var verticalLevel = 0;

    $movingTab.css({
      'width': moveDistance,
      'transform': 'translate3d(' + (moveDistance * index) + 'px, ' + (verticalLevel * 38) + 'px, 0)'
    });
  }
  
  // Function to update groups list based on selected group sets - real data from database
  function updateGroupsList() {
    const $groupsContainer = $('#groups-container');
    $groupsContainer.empty();
    
    // Get selected group sets from the form
    const selectedGroupSets = [];
    $('input[name="group_set_ids"]:checked').each(function() {
      selectedGroupSets.push($(this).val());
    });
    
    if (selectedGroupSets.length === 0) {
      $groupsContainer.append('<div class="alert alert-warning">No group sets selected. Please go back and select at least one group set.</div>');
      $('#next-btn').prop('disabled', true);
      return;
    } else {
      $('#next-btn').prop('disabled', false);
    }
    
    // Real group data from the server database
    const groups = window.wizardContext.groups || [];
    console.log(`Processing ${groups.length} groups from database for ${selectedGroupSets.length} selected group sets`);
    
    if (groups.length === 0) {
      // Show the no groups warning
      $('#no-groups-warning').show();
      $groupsContainer.append('<div class="alert alert-warning">No groups found for the selected group sets. Please import groups from Canvas first.</div>');
      $('#next-btn').prop('disabled', true);
      return;
    } else {
      // Hide the warning
      $('#no-groups-warning').hide();
    }
    
    // Organize groups by category
    const groupsByCategory = {};
    groups.forEach(group => {
      if (!groupsByCategory[group.category_id]) {
        groupsByCategory[group.category_id] = {
          name: group.category_name,
          groups: []
        };
      }
      groupsByCategory[group.category_id].groups.push(group);
    });
    
    let anyGroupsFound = false;
    
    // Add sections for each group set
    selectedGroupSets.forEach(groupSetId => {
      const categoryData = groupsByCategory[groupSetId];
      const groupSetName = categoryData ? categoryData.name : $(`label[for="group_set_${groupSetId}"]`).text().trim();
      const groupsInSet = categoryData ? categoryData.groups : [];
      
      if (groupsInSet.length === 0) {
        $groupsContainer.append(`
          <li class="list-group-item">
            <h6>${groupSetName}</h6>
            <div class="alert alert-warning">No groups found in this group set.</div>
          </li>
        `);
      } else {
        anyGroupsFound = true;
        
        $groupsContainer.append(`
          <li class="list-group-item">
            <h6>${groupSetName}</h6>
            <div class="mb-2">
              <button type="button" class="btn btn-sm btn-outline-primary select-all-groups" data-group-set="${groupSetId}">
                Select All
              </button>
              <button type="button" class="btn btn-sm btn-outline-secondary deselect-all-groups" data-group-set="${groupSetId}">
                Deselect All
              </button>
            </div>
            <ul class="list-group" id="group-set-${groupSetId}-groups">
              ${groupsInSet.map(group => `
                <li class="list-group-item ps-4">
                  <div class="form-check">
                    <input class="form-check-input" type="checkbox" name="group_ids" value="${group.canvas_id}" id="group_${group.canvas_id}" data-group-set="${groupSetId}" checked style="width: 20px; height: 20px; margin-right: 10px; visibility: visible !important; opacity: 1 !important;">
                    <label class="form-check-label" for="group_${group.canvas_id}">
                      ${group.name} (${group.members_count} members)
                    </label>
                  </div>
                </li>
              `).join('')}
            </ul>
          </li>
        `);
      }
    });
    
    // Disable next button if no groups were found
    if (!anyGroupsFound) {
      $('#next-btn').prop('disabled', true);
      $('#no-groups-warning').show();
    }
    
    // Add event handlers for select/deselect all buttons
    $(document).off('click', '.select-all-groups').on('click', '.select-all-groups', function() {
      const groupSetId = $(this).data('group-set');
      $(`input[name="group_ids"][data-group-set="${groupSetId}"]`).prop('checked', true);
    });
    
    $(document).off('click', '.deselect-all-groups').on('click', '.deselect-all-groups', function() {
      const groupSetId = $(this).data('group-set');
      $(`input[name="group_ids"][data-group-set="${groupSetId}"]`).prop('checked', false);
    });
  }
  
  // Call updateGroupsList if we're on step 3
  if (window.wizardContext.current_step === 3) {
    updateGroupsList();
  }
  
  // Function to update confirmation summary
  function updateSummary() {
    // Get selected course
    const courseId = $('#course_id').val();
    const courseName = $('#course_id option:selected').text();
    
    // Get selected group sets
    const selectedGroupSets = [];
    $('input[name="group_set_ids"]:checked').each(function() {
      const id = $(this).val();
      const name = $(this).closest('.form-check').find('label').text().trim();
      selectedGroupSets.push(name);
    });
    
    // Get selected groups by group set
    const selectedGroupsBySet = {};
    let totalGroupCount = 0;
    
    $('input[name="group_ids"]:checked').each(function() {
      const groupId = $(this).val();
      const groupSetId = $(this).data('group-set');
      const groupName = $(this).closest('.form-check').find('label').text().trim();
      
      if (!selectedGroupsBySet[groupSetId]) {
        selectedGroupsBySet[groupSetId] = [];
      }
      
      selectedGroupsBySet[groupSetId].push(groupName);
      totalGroupCount++;
    });
    
    // Build groups summary HTML with group sets as sections
    let groupsSummaryHtml = '';
    
    if (totalGroupCount === 0) {
      groupsSummaryHtml = 'No groups selected';
    } else {
      Object.keys(selectedGroupsBySet).forEach(groupSetId => {
        const groups = selectedGroupsBySet[groupSetId];
        const groupSetName = $(`label[for="group_set_${groupSetId}"]`).text().trim();
        
        groupsSummaryHtml += `
          <div class="mb-2">
            <strong>${groupSetName}</strong>
            <ul class="mb-1">
              ${groups.map(group => `<li>${group}</li>`).join('')}
            </ul>
          </div>
        `;
      });
    }
    
    // Get sync options
    const syncMemberships = $('#sync_memberships').is(':checked') ? 'Yes' : 'No';
    const syncLeaders = $('#sync_leaders').is(':checked') ? 'Yes' : 'No';
    
    // Get integration options
    const createGithubRepo = $('#create_github_repo').is(':checked') ? 'Yes' : 'No';
    const setupProjectManagement = $('#setup_project_management').is(':checked') ? 'Yes' : 'No';
    
    // Update summary in step 5
    $('#summary-course').text(courseName);
    $('#summary-group-sets').text(selectedGroupSets.length > 0 ? selectedGroupSets.join(', ') : 'No group sets selected');
    $('#summary-groups').html(groupsSummaryHtml);
    $('#summary-sync-memberships').text(syncMemberships);
    $('#summary-sync-leaders').text(syncLeaders);
    $('#summary-github-repos').text(createGithubRepo);
    $('#summary-project-management').text(setupProjectManagement);
    
    // Calculate how many teams will be created
    $('#summary-teams-count').text(totalGroupCount);
  }
}
