// Initialize wizard when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
  // Ensure wizardContext exists
  if (typeof window.wizardContext === 'undefined') {
    window.wizardContext = {
      current_step: 1,
      courses: [],
      group_sets: [],
      groups: [],
      created_teams: []
    };
  }

  // Start the wizard initialization
  if (typeof jQuery !== 'undefined') {
    initializeWizard();
  } else {
    initializeWizardWithoutJQuery();
  }
});

// DOM Selectors object to cache and centralize selectors
const SELECTORS = {
  card: '.card-wizard',
  form: '#sync-wizard-form',
  navLinks: '.nav-pills .nav-link',
  activeNavLink: '.nav-pills .nav-link.active',
  tabPanes: '.tab-pane',
  courseSelect: '#course_id',
  nextBtn: '#next-btn',
  prevBtn: '#previous-btn',
  resetBtn: '#reset-btn',
  finishBtn: '#finish-btn',
  noCoursesWarning: '#no-courses-warning',
  noGroupSetsWarning: '#no-group-sets-warning',
  noGroupsWarning: '#no-groups-warning',
  groupSetsContainer: '.group-sets-container',
  groupsContainer: '#groups-container'
};

// Helper function to safely parse JSON
const safeParse = (data) => {
  if (typeof data !== 'string') return data;

  try {
    return JSON.parse(data);
  } catch (e) {
    return [];
  }
};

// Helper function to get CSRF token
const getCookie = (name) => {
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
};

// Fallback initialization without jQuery
function initializeWizardWithoutJQuery() {
  // Get wizard card
  const wizardCard = document.querySelector(SELECTORS.card);
  if (!wizardCard) {
    return;
  }

  // Show the wizard card
  wizardCard.classList.add('active');

  // Add current step information and bootstrap tab initialization
  const currentStep = window.wizardContext.current_step || 1;

  // Set the active tab
  const tabLinks = document.querySelectorAll(SELECTORS.navLinks);
  tabLinks.forEach((link, index) => {
    if (index === currentStep - 1) {
      link.classList.add('active');
      if (typeof bootstrap !== 'undefined') {
        new bootstrap.Tab(link).show();
      }
    } else {
      link.classList.remove('active');
    }
  });

  // Basic initialization of buttons
  const nextBtn = document.getElementById('next-btn');
  const prevBtn = document.getElementById('previous-btn');
  const resetBtn = document.getElementById('reset-btn');

  const appendActionAndSubmit = (action) => {
    const form = document.getElementById('sync-wizard-form');
    if (form) {
      const actionInput = document.createElement('input');
      actionInput.type = 'hidden';
      actionInput.name = 'action';
      actionInput.value = action;
      form.appendChild(actionInput);
      form.submit();
    }
  };

  if (nextBtn) {
    nextBtn.addEventListener('click', () => appendActionAndSubmit('next'));
  }

  if (prevBtn) {
    prevBtn.addEventListener('click', () => appendActionAndSubmit('previous'));
  }

  if (resetBtn) {
    resetBtn.addEventListener('click', () => {
      if (confirm('Are you sure you want to restart the wizard? All progress will be lost.')) {
        appendActionAndSubmit('reset');
      }
    });
  }
}

function initializeWizard() {
  // Safety check
  if (typeof $ === 'undefined') {
    return;
  }

  // Cache jQuery DOM elements
  const $wizardCard = $(SELECTORS.card);
  const $form = $wizardCard.find('form');
  const $courseSelect = $(SELECTORS.courseSelect);

  // Set up AJAX with CSRF token
  const csrftoken = getCookie('csrftoken');
  $.ajaxSetup({
    beforeSend: (xhr, settings) => {
      if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
        xhr.setRequestHeader("X-CSRFToken", csrftoken);
      }
    }
  });

  // Show wizard card (Paper Dashboard CSS hides it until .active)
  $wizardCard.addClass('active');

  // Unified form submission function for next, previous actions
  const submitStep = (action, onSuccess) => {
    const formData = new FormData($form[0]);
    formData.append('action', action);

    $.ajax({
      url: $form.attr('action'),
      type: 'POST',
      data: formData,
      processData: false,
      contentType: false,
      success: (response) => {
        // Update wizard context with new data if provided
        if (response.wizard_data) {
          window.wizardContext = response.wizard_data;

          // Parse JSON strings if needed
          window.wizardContext.courses = safeParse(window.wizardContext.courses);
          window.wizardContext.group_sets = safeParse(window.wizardContext.group_sets);
          window.wizardContext.groups = safeParse(window.wizardContext.groups);
          window.wizardContext.created_teams = safeParse(window.wizardContext.created_teams);
        }

        // Execute success callback
        onSuccess(response);
      },
      error: (xhr, status, error) => {
        alert(`Error processing step: ${error}`);
      }
    });
  };

  // Populate course dropdown conditionally
  const populateCourseDropdown = () => {
    if ($courseSelect.length && $courseSelect.find('option').length <= 1) {
      const courses = window.wizardContext?.courses || [];

      if (courses && courses.length) {
        courses.forEach(course => {
          if (course && course.canvas_id && course.course_code && course.name) {
            $courseSelect.append(`<option value="${course.canvas_id}">${course.course_code} - ${course.name}</option>`);
          }
        });

        // Hide warning and enable next button
        $(SELECTORS.noCoursesWarning).hide();
        $(SELECTORS.nextBtn).prop('disabled', false);
      } else {
        $courseSelect.append('<option value="" disabled>No courses available - please import courses from Canvas</option>');

        // Show the warning message
        $(SELECTORS.noCoursesWarning).show();

        // Disable next button since we can't proceed without courses
        $(SELECTORS.nextBtn).prop('disabled', true);
      }
    }
  };

  // Initialize course dropdown
  populateCourseDropdown();

  // Course change handler to fetch group sets via AJAX
  $courseSelect.on('change', function() {
    const courseId = $(this).val();
    if (courseId) {
      // Store the course ID in a hidden field
      if (!$('input[name="course_id"]').length) {
        $form.append(`<input type="hidden" name="course_id" value="${courseId}">`);
      } else {
        $('input[name="course_id"]').val(courseId);
      }

      // Enable the Next button now that a course is selected
      $(SELECTORS.nextBtn).prop('disabled', false);
    } else {
      // Disable Next button if no course is selected
      $(SELECTORS.nextBtn).prop('disabled', true);
    }
  });

  // Function to update group sets based on selected course
  const populateGroupSets = () => {
    const $groupSetsContainer = $(SELECTORS.groupSetsContainer);
    $groupSetsContainer.empty(); // Clear existing content

    // Group sets should be provided by the server in wizardContext
    const groupSets = window.wizardContext.group_sets || [];

    if (groupSets.length === 0) {
      // Show the no group sets warning
      $(SELECTORS.noGroupSetsWarning).show();

      // Add informative message to the container
      $groupSetsContainer.append('<div class="alert alert-warning">No group sets found for this course. Please import group sets from Canvas first.</div>');

      // Disable next button since we can't proceed without group sets
      $(SELECTORS.nextBtn).prop('disabled', true);
      return;
    } else {
      // Hide warning and enable next button
      $(SELECTORS.noGroupSetsWarning).hide();
      $(SELECTORS.nextBtn).prop('disabled', false);
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
  };

  // Function to update groups list based on selected group sets
  const updateGroupsList = () => {
    const $groupsContainer = $(SELECTORS.groupsContainer);
    $groupsContainer.empty();

    // Get selected group sets from the form
    const selectedGroupSets = [];
    $('input[name="group_set_ids"]:checked').each(function() {
      selectedGroupSets.push($(this).val());
    });

    if (selectedGroupSets.length === 0) {
      $groupsContainer.append('<div class="alert alert-warning">No group sets selected. Please go back and select at least one group set.</div>');
      $(SELECTORS.nextBtn).prop('disabled', true);
      return;
    } else {
      $(SELECTORS.nextBtn).prop('disabled', false);
    }

    // Real group data from the server database
    const groups = window.wizardContext.groups || [];

    if (groups.length === 0) {
      // Show the no groups warning
      $(SELECTORS.noGroupsWarning).show();
      $groupsContainer.append('<div class="alert alert-warning">No groups found for the selected group sets. Please import groups from Canvas first.</div>');
      $(SELECTORS.nextBtn).prop('disabled', true);
      return;
    } else {
      // Hide the warning
      $(SELECTORS.noGroupsWarning).hide();
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
      $(SELECTORS.nextBtn).prop('disabled', true);
      $(SELECTORS.noGroupsWarning).show();
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
  };

  // Function to update confirmation summary
  const updateSummary = () => {
    // Get selected course
    const courseId = $courseSelect.val();
    const courseName = $courseSelect.find('option:selected').text();

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
  };

  // Form validation
  const $validator = $form.validate({
    rules: {
      course_id: {
        required: true
      }
      // add more rules per field/step as needed
    },
    highlight: (element) => {
      $(element).closest('.mb-3').addClass('has-danger').removeClass('has-success');
    },
    success: (label) => {
      $(label).closest('.mb-3').addClass('has-success').removeClass('has-danger');
    }
  });

  // Fix for Bootstrap 5: Properly handle tab panes
  const fixTabPaneVisibility = (index) => {
    // Hide all tab panes first
    $(SELECTORS.tabPanes).removeClass('show active');

    // Show the target tab pane
    const targetId = '#step' + (index + 1);
    $(targetId).addClass('show active');
  };

  // Manual next button handler - submits the form via AJAX
  $(document).on('click', '#next-btn, .btn-next', function() {
    const $activeTab = $(SELECTORS.activeNavLink);
    const $nextTab = $activeTab.parent().next().find('.nav-link');

    if ($nextTab.length > 0 && $form.valid()) {
      // Get the current step
      const currentIndex = $(SELECTORS.navLinks).index($activeTab);
      const nextIndex = currentIndex + 1;

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
        window.courseId = $courseSelect.val();
      }

      // Submit with "next" action
      submitStep('next', (response) => {
        // Update current step
        window.wizardContext.current_step = nextIndex + 1;

        // Activate next tab
        $(SELECTORS.navLinks).removeClass('active');
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
      });
    }
  });

  // Previous button handler
  $(document).on('click', '#previous-btn, .btn-previous', function() {
    const $activeTab = $(SELECTORS.activeNavLink);
    const $prevTab = $activeTab.parent().prev().find('.nav-link');

    if ($prevTab.length > 0) {
      // Get the current step
      const currentIndex = $(SELECTORS.navLinks).index($activeTab);
      const prevIndex = currentIndex - 1;

      // Submit with "previous" action
      submitStep('previous', (response) => {
        // Update current step
        window.wizardContext.current_step = prevIndex + 1;

        // Activate previous tab
        $(SELECTORS.navLinks).removeClass('active');
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
      });
    }
  });

  // Initialize wizard appearance
  initWizardAppearance();

  // Append progress bar
  const stepCount = $wizardCard.find('.wizard-navigation li').length;
  $wizardCard.find('.wizard-navigation').append(
    '<div class="progress mt-3">' +
      '<div class="progress-bar" role="progressbar" aria-valuemin="1" aria-valuemax="' + stepCount + '" style="width: 0%;"></div>' +
    '</div>'
  );

  // Set initial progress
  const initialIndex = $(SELECTORS.activeNavLink).parent().index();
  if (initialIndex < 0) {
    // Default to first tab if none is active
    initialIndex = 0;
    $(SELECTORS.navLinks).first().addClass('active');
  }
  updateProgress(initialIndex);

  // Handle direct tab clicks (ensure they go through the form submission)
  $(SELECTORS.navLinks).on('click', (e) => {
    e.preventDefault();
    // Don't allow direct clicking of tabs - must use next/previous buttons
    return false;
  });

  // Reset button handler
  $(document).on('click', '#reset-btn', function() {
    // Confirm reset
    if (confirm('Are you sure you want to restart the wizard? All progress will be lost.')) {
      // Submit with "reset" action
      submitStep('reset', (response) => {
        // Reset form
        $form[0].reset();

        // Reset wizard state
        const $firstTab = $(SELECTORS.navLinks).first();
        $(SELECTORS.navLinks).removeClass('active');
        $firstTab.addClass('active');

        // Reset tab panes
        $(SELECTORS.tabPanes).removeClass('show active');
        $('#step1').addClass('show active');

        // Reset progress
        updateProgress(0);

        // Reload mock data
        $courseSelect.trigger('reset.mockdata');
      });
    }
  });

  // Check current step and run appropriate initialization
  if (window.wizardContext.current_step === 2) {
    populateGroupSets();
  } else if (window.wizardContext.current_step === 3) {
    updateGroupsList();
  } else if (window.wizardContext.current_step === 5) {
    updateSummary();
  }

  // Helper functions for wizard UI
  function initWizardAppearance() {
    // Create moving tab
    const firstTitle = $('.wizard-navigation li:first-child a').html();
    const $movingTab = $("<div class='moving-tab'></div>").append(firstTitle);
    $wizardCard.find('.wizard-navigation').append($movingTab);

    // Initial position
    const initialIndex = $(SELECTORS.activeNavLink).parent().index();
    refreshAnimation($wizardCard, initialIndex);

    // Fix initial tab pane visibility
    fixTabPaneVisibility(initialIndex);

    // Initial state
    updateTabState(initialIndex);

    // Handle window resize to adjust the moving tab
    $(window).resize(() => {
      // Recalculate moving tab position
      const activeIndex = $(SELECTORS.activeNavLink).parent().index();
      refreshAnimation($wizardCard, activeIndex);
    });
  }

  function updateTabState(index) {
    const total = $(SELECTORS.navLinks).length;
    const current = index + 1;

    // Update moving tab
    const activeText = $('.nav-pills li:nth-child(' + current + ') a').html();
    setTimeout(() => {
      $wizardCard.find('.moving-tab').html(activeText);
    }, 150);

    // Show/hide next/finish buttons
    if (current >= total) {
      $(SELECTORS.nextBtn).hide();
      $(SELECTORS.finishBtn).show();
    } else {
      $(SELECTORS.nextBtn).show();
      $(SELECTORS.finishBtn).hide();
    }

    refreshAnimation($wizardCard, index);
  }

  function updateProgress(index) {
    const total = $(SELECTORS.navLinks).length;
    const current = index + 1;
    const percent = (current / total) * 100;

    // Update progress bar
    $wizardCard.find('.progress-bar').css({ width: `${percent}%` });

    // Update moving tab text and position
    updateTabState(index);
  }

  function refreshAnimation($wizard, index) {
    const total = $wizard.find('.wizard-navigation li').length;
    const moveDistance = $wizard.find('.wizard-navigation').width() / total;
    const $movingTab = $wizard.find('.moving-tab');
    const verticalLevel = 0;

    $movingTab.css({
      width: moveDistance,
      transform: `translate3d(${moveDistance * index}px, ${verticalLevel * 38}px, 0)`
    });
  }
}
