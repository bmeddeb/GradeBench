
$(document).ready(function() {
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
  
  // Add mock data for the demonstration
  const mockData = {
    courses: [
      { id: 1, code: 'CS101', name: 'Introduction to Computer Science' },
      { id: 2, code: 'CS201', name: 'Data Structures and Algorithms' },
      { id: 3, code: 'CS301', name: 'Database Systems' }
    ],
    groupSets: [
      { id: 1, name: 'Project Teams', group_count: 12 },
      { id: 2, name: 'Lab Partners', group_count: 24 },
      { id: 3, name: 'Study Groups', group_count: 8 }
    ],
    groups: [
      { id: 1, name: 'Team Alpha', members_count: 4 },
      { id: 2, name: 'Team Beta', members_count: 4 },
      { id: 3, name: 'Team Gamma', members_count: 4 }
    ]
  };
  
  // Populate course dropdown with mock data
  const $courseSelect = $('#course_id');
  $courseSelect.empty().append('<option value="">Please select a course</option>');
  mockData.courses.forEach(course => {
    $courseSelect.append(`<option value="${course.id}">${course.code} - ${course.name}</option>`);
  });
  
  // Populate group sets checkboxes
  const $groupSetsContainer = $('.group-sets-container');
  if ($groupSetsContainer.length > 0 && $groupSetsContainer.children().length === 0) {
    mockData.groupSets.forEach(groupSet => {
      $groupSetsContainer.append(`
        <div class="card mb-3">
          <div class="card-body">
            <div class="form-check">
              <input class="form-check-input" type="checkbox" name="group_set_ids" value="${groupSet.id}" id="group_set_${groupSet.id}">
              <label class="form-check-label" for="group_set_${groupSet.id}">
                <strong>${groupSet.name}</strong> (${groupSet.group_count} groups)
              </label>
            </div>
          </div>
        </div>
      `);
    });
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

  // Manual next/previous button handlers (for Bootstrap 5 compatibility)
  $(document).on('click', '#next-btn, .btn-next', function() {
    var $activeTab = $('.nav-pills .nav-link.active');
    var $nextTab = $activeTab.parent().next().find('.nav-link');
    
    if ($nextTab.length > 0 && $form.valid()) {
      // Get the current step
      var currentIndex = $('.nav-pills .nav-link').index($activeTab);
      var nextIndex = currentIndex + 1;
      
      // Handle step transitions with mock data
      if (currentIndex === 1) { // Moving from step 2 to step 3
        // Process selected group sets and populate groups
        updateGroupsList();
      }
      
      if (currentIndex === 3) { // Moving from step 4 to step 5
        // Update summary based on selections
        updateSummary();
      }
      
      // For mock data version, just navigate directly
      $('.nav-pills .nav-link').removeClass('active');
      $nextTab.addClass('active');
      
      // Fix tab pane visibility
      fixTabPaneVisibility(nextIndex);
      
      // Update progress
      updateProgress(nextIndex);
      
      /* When backend is implemented, use this:
      // AJAX "next" action
      var formData = new FormData($form[0]);
      formData.append('action', 'next');
      $.ajax({
        url: $form.attr('action'),
        type: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        success: function(response) {
          // Activate next tab
          $('.nav-pills .nav-link').removeClass('active');
          $nextTab.addClass('active');
          
          // Fix tab pane visibility
          fixTabPaneVisibility(nextIndex);
          
          // Update progress
          updateProgress(nextIndex);
        }
      });
      */
    }
  });

  $(document).on('click', '#previous-btn, .btn-previous', function() {
    var $activeTab = $('.nav-pills .nav-link.active');
    var $prevTab = $activeTab.parent().prev().find('.nav-link');
    
    if ($prevTab.length > 0) {
      // Get the current step
      var currentIndex = $('.nav-pills .nav-link').index($activeTab);
      var prevIndex = currentIndex - 1;
      
      // For mock data version, just navigate directly
      $('.nav-pills .nav-link').removeClass('active');
      $prevTab.addClass('active');
      
      // Fix tab pane visibility
      fixTabPaneVisibility(prevIndex);
      
      // Update progress
      updateProgress(prevIndex);
      
      /* When backend is implemented, use this:
      // AJAX "previous" action
      var formData = new FormData($form[0]);
      formData.append('action', 'previous');
      $.ajax({
        url: $form.attr('action'),
        type: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        success: function(response) {
          // Activate previous tab
          $('.nav-pills .nav-link').removeClass('active');
          $prevTab.addClass('active');
          
          // Fix tab pane visibility
          fixTabPaneVisibility(prevIndex);
          
          // Update progress
          updateProgress(prevIndex);
        }
      });
      */
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
  
  // Function to update groups list based on selected group sets
  function updateGroupsList() {
    const $groupsContainer = $('#groups-container');
    $groupsContainer.empty();
    
    // Get selected group sets
    const selectedGroupSets = [];
    $('input[name="group_set_ids"]:checked').each(function() {
      selectedGroupSets.push($(this).val());
    });
    
    if (selectedGroupSets.length === 0) {
      $groupsContainer.append('<div class="alert alert-warning">No group sets selected. Please go back and select at least one group set.</div>');
      return;
    }
    
    // Add mock groups
    mockData.groups.forEach(group => {
      $groupsContainer.append(`
        <li class="list-group-item">
          <div class="form-check">
            <input class="form-check-input" type="checkbox" name="group_ids" value="${group.id}" id="group_${group.id}" checked>
            <label class="form-check-label" for="group_${group.id}">
              ${group.name} (${group.members_count} members)
            </label>
          </div>
        </li>
      `);
    });
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
    
    // Get selected groups
    const selectedGroups = [];
    $('input[name="group_ids"]:checked').each(function() {
      const id = $(this).val();
      const name = $(this).closest('.form-check').find('label').text().trim();
      selectedGroups.push(name);
    });
    
    // Get sync options
    const syncMemberships = $('#sync_memberships').is(':checked') ? 'Yes' : 'No';
    const syncLeaders = $('#sync_leaders').is(':checked') ? 'Yes' : 'No';
    
    // Get integration options
    const createGithubRepo = $('#create_github_repo').is(':checked') ? 'Yes' : 'No';
    const setupProjectManagement = $('#setup_project_management').is(':checked') ? 'Yes' : 'No';
    
    // Update summary in step 5
    $('#summary-course').text(courseName);
    $('#summary-group-sets').text(selectedGroupSets.length > 0 ? selectedGroupSets.join(', ') : 'No group sets selected');
    $('#summary-groups').text(selectedGroups.length > 0 ? selectedGroups.join(', ') : 'No groups selected');
    $('#summary-sync-memberships').text(syncMemberships);
    $('#summary-sync-leaders').text(syncLeaders);
    $('#summary-github-repos').text(createGithubRepo);
    $('#summary-project-management').text(setupProjectManagement);
  }
});
