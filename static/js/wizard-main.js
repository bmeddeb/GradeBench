/**
 * Wizard Main Entry Point (Non-ES Modules Version)
 * 
 * This file serves as the main entry point for the wizard functionality.
 * It follows the same organization principles as the ES modules version
 * but uses the revealing module pattern for compatibility with browsers
 * that don't support ES modules.
 */

// Initialize when the DOM is fully loaded
$(document).ready(() => {
  // Initialize the wizard modules
  WizardState.init();
  WizardAPI.init();
  
  WizardUI.init({
    onNext: handleNextStep,
    onPrevious: handlePreviousStep,
    onReset: handleReset,
    onFinish: handleFinish
  });
  
  // Initialize step specific functionality
  const currentStep = WizardState.getCurrentStep();
  activateStepHandler(currentStep);
  
  /**
   * Handle navigation to the next step
   */
  function handleNextStep() {
    const currentStep = WizardState.getCurrentStep();
    const stepHandler = getStepHandler(currentStep);
    
    if (stepHandler && stepHandler.validate()) {
      // Gather step data
      const stepData = stepHandler.getData();
      
      // Submit step
      WizardAPI.submitStep('next', stepData, (response) => {
        // Update state with response data
        WizardState.updateFromResponse(response);
        
        // Activate next step
        const nextStep = currentStep + 1;
        activateStepHandler(nextStep);
      });
    }
  }
  
  /**
   * Handle navigation to the previous step
   */
  function handlePreviousStep() {
    const currentStep = WizardState.getCurrentStep();
    
    WizardAPI.submitStep('previous', {}, (response) => {
      // Update state with response data
      WizardState.updateFromResponse(response);
      
      // Activate previous step
      const prevStep = currentStep - 1;
      activateStepHandler(prevStep);
    });
  }
  
  /**
   * Handle the finish action
   */
  function handleFinish() {
    const currentStep = WizardState.getCurrentStep();
    const stepHandler = getStepHandler(currentStep);
    
    if (stepHandler && stepHandler.validate()) {
      // Gather step data
      const stepData = stepHandler.getData();
      
      // Submit step
      WizardAPI.submitStep('finish', stepData, (response) => {
        // Update state with response data
        WizardState.updateFromResponse(response);
        
        // Activate results step
        activateStepHandler(6);
      });
    }
  }
  
  /**
   * Handle the reset action
   */
  function handleReset() {
    if (confirm('Are you sure you want to restart the wizard? All progress will be lost.')) {
      WizardAPI.submitStep('reset', {}, (response) => {
        // Update state with response data
        WizardState.updateFromResponse(response);
        
        // Reset UI
        WizardUI.reset();
        
        // Activate first step
        activateStepHandler(1);
      });
    }
  }
  
  /**
   * Activate a specific step handler
   * @param {number} stepNumber - The step number to activate (1-based)
   */
  function activateStepHandler(stepNumber) {
    // Update UI for the step
    WizardUI.activateStep(stepNumber);
    
    // Initialize step content
    const stepHandler = getStepHandler(stepNumber);
    if (stepHandler && stepHandler.init) {
      stepHandler.init();
    }
  }
  
  /**
   * Get the handler for a specific step
   * @param {number} stepNumber - The step number (1-based)
   * @returns {Object|null} - The step handler module
   */
  function getStepHandler(stepNumber) {
    switch (stepNumber) {
      case 1: return CourseStep;
      case 2: return GroupSetStep;
      case 3: return GroupsStep;
      case 4: return IntegrationStep;
      case 5: return SummaryStep;
      case 6: return ResultsStep;
      default: return null;
    }
  }
});

/**
 * WizardState module - Manages the state of the wizard
 */
const WizardState = (function() {
  // Private state
  let _state = {
    current_step: 1,
    courses: [],
    group_sets: [],
    groups: [],
    created_teams: [],
    // Step-specific state
    course_id: null,
    group_set_ids: [],
    group_ids: [],
    create_github_repo: false,
    setup_project_management: false,
    repo_pattern: '{course_code}-{group_name}',
    confirmed: false
  };
  
  // Event listeners
  const _listeners = {
    stateChange: []
  };
  
  /**
   * Initialize the state
   */
  function init() {
    // Check if there's existing state in window.wizardContext
    if (typeof window.wizardContext !== 'undefined') {
      updateState({
        current_step: window.wizardContext.current_step || 1,
        courses: safeParse(window.wizardContext.courses) || [],
        group_sets: safeParse(window.wizardContext.group_sets) || [],
        groups: safeParse(window.wizardContext.groups) || [],
        created_teams: safeParse(window.wizardContext.created_teams) || []
      });
    }
    
    // Export state to window for backward compatibility
    _syncWithWindow();
  }
  
  /**
   * Update state with new values and notify listeners
   * @param {Object} newState - The new state properties to set
   */
  function updateState(newState) {
    const prevState = { ..._state };
    _state = { ..._state, ...newState };
    
    // Sync with window.wizardContext for backward compatibility
    _syncWithWindow();
    
    // Notify listeners
    _notifyListeners('stateChange', { prevState, newState: _state });
  }
  
  /**
   * Update state from server response
   * @param {Object} response - The server response data
   */
  function updateFromResponse(response) {
    if (response && response.wizard_data) {
      updateState({
        current_step: response.wizard_data.current_step || _state.current_step,
        courses: safeParse(response.wizard_data.courses) || _state.courses,
        group_sets: safeParse(response.wizard_data.group_sets) || _state.group_sets,
        groups: safeParse(response.wizard_data.groups) || _state.groups,
        created_teams: safeParse(response.wizard_data.created_teams) || _state.created_teams
      });
    }
  }
  
  /**
   * Get the current step
   * @returns {number} The current step number
   */
  function getCurrentStep() {
    return _state.current_step;
  }
  
  /**
   * Get the full state
   * @returns {Object} The current state
   */
  function getState() {
    return { ..._state };
  }
  
  /**
   * Get a specific piece of state
   * @param {string} key - The state key to get
   * @returns {*} The value of the specified state key
   */
  function get(key) {
    return _state[key];
  }
  
  /**
   * Set a specific piece of state
   * @param {string} key - The state key to set
   * @param {*} value - The value to set
   */
  function set(key, value) {
    const newState = {};
    newState[key] = value;
    updateState(newState);
  }
  
  /**
   * Subscribe to state changes
   * @param {string} event - The event to subscribe to (e.g., 'stateChange')
   * @param {Function} callback - The callback function
   * @returns {Function} Unsubscribe function
   */
  function subscribe(event, callback) {
    if (!_listeners[event]) {
      _listeners[event] = [];
    }
    
    _listeners[event].push(callback);
    
    // Return unsubscribe function
    return () => {
      _listeners[event] = _listeners[event].filter(cb => cb !== callback);
    };
  }
  
  /**
   * Sync state with window.wizardContext for backward compatibility
   * @private
   */
  function _syncWithWindow() {
    window.wizardContext = {
      current_step: _state.current_step,
      courses: _state.courses,
      group_sets: _state.group_sets,
      groups: _state.groups,
      created_teams: _state.created_teams
    };
  }
  
  /**
   * Notify listeners of state changes
   * @param {string} event - The event that occurred
   * @param {Object} data - The event data
   * @private
   */
  function _notifyListeners(event, data) {
    if (_listeners[event]) {
      _listeners[event].forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`Error in listener for event ${event}:`, error);
        }
      });
    }
  }
  
  // Public API
  return {
    init,
    updateState,
    updateFromResponse,
    getCurrentStep,
    getState,
    get,
    set,
    subscribe
  };
})();

/**
 * WizardAPI module - Handles AJAX requests for the wizard
 */
const WizardAPI = (function() {
  // Private variables
  const _formSelector = '#sync-wizard-form';
  
  /**
   * Initialize the API module
   */
  function init() {
    // Set up AJAX with CSRF token
    const csrftoken = getCookie('csrftoken');
    $.ajaxSetup({
      beforeSend: (xhr, settings) => {
        if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
          xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
      }
    });
  }
  
  /**
   * Submit a step to the server
   * @param {string} action - The action to perform (next, previous, reset, finish)
   * @param {Object} stepData - Additional data for the step
   * @param {Function} onSuccess - Success callback
   * @param {Function} onError - Error callback (optional)
   */
  function submitStep(action, stepData = {}, onSuccess, onError) {
    const $form = $(_formSelector);
    const formData = new FormData($form[0]);
    
    // Add action to form data
    formData.append('action', action);
    
    // Add step data to form data
    Object.keys(stepData).forEach(key => {
      if (Array.isArray(stepData[key])) {
        // Handle array values
        stepData[key].forEach(value => {
          formData.append(key, value);
        });
      } else {
        formData.append(key, stepData[key]);
      }
    });
    
    // Make AJAX request
    $.ajax({
      url: $form.attr('action'),
      type: 'POST',
      data: formData,
      processData: false,
      contentType: false,
      success: (response) => {
        if (onSuccess) {
          onSuccess(response);
        }
      },
      error: (xhr, status, error) => {
        console.error(`Error processing step: ${error}`, { xhr, status });
        
        if (onError) {
          onError(xhr, status, error);
        } else {
          // Default error handling
          let errorMessage = 'An error occurred while processing your request.';
          
          if (xhr.responseJSON && xhr.responseJSON.error) {
            errorMessage = xhr.responseJSON.error;
          } else if (xhr.statusText) {
            errorMessage = `Error: ${xhr.statusText}`;
          }
          
          alert(errorMessage);
        }
      }
    });
  }
  
  // Public API
  return {
    init,
    submitStep
  };
})();

/**
 * WizardUI module - Manages the UI of the wizard
 */
const WizardUI = (function() {
  // Private variables
  const _selectors = {
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
    groupsContainer: '#groups-container',
    progressBar: '.progress-bar',
    movingTab: '.moving-tab'
  };
  
  // Event handlers
  let _handlers = {
    onNext: null,
    onPrevious: null,
    onReset: null,
    onFinish: null
  };
  
  // References to DOM elements
  let _elements = {};
  
  /**
   * Initialize the UI module
   * @param {Object} handlers - Event handlers
   */
  function init(handlers = {}) {
    // Store handlers
    _handlers = { ..._handlers, ...handlers };
    
    // Cache jQuery DOM elements
    _cacheElements();
    
    // Show wizard card (Paper Dashboard CSS hides it until .active)
    _elements.$wizardCard.addClass('active');
    
    // Initialize wizard appearance
    _initWizardAppearance();
    
    // Set up event listeners
    _setupEventListeners();
    
    // Initialize validation
    _initValidation();
    
    // Set up progress bar
    _setupProgressBar();
    
    // Initialize wizard UI for current step
    const currentStep = WizardState.getCurrentStep();
    activateStep(currentStep);
  }
  
  /**
   * Activate a specific step in the wizard
   * @param {number} stepNumber - The step number to activate (1-based)
   */
  function activateStep(stepNumber) {
    // Update step in UI
    const $navLinks = $(_selectors.navLinks);
    const index = stepNumber - 1;
    
    // Active tab navigation
    $navLinks.removeClass('active');
    $navLinks.eq(index).addClass('active');
    
    // Show tab content
    $(_selectors.tabPanes).removeClass('show active');
    $(`#step${stepNumber}`).addClass('show active');
    
    // Update progress
    _updateProgress(index);
    
    // Enable/disable navigation buttons
    _updateNavigationButtons(stepNumber);
  }
  
  /**
   * Reset the UI to the initial state
   */
  function reset() {
    // Reset form
    _elements.$form[0].reset();
    
    // Reset UI to first step
    activateStep(1);
  }
  
  /**
   * Show a warning message
   * @param {string} message - The warning message to display
   * @param {string} type - The type of alert (success, info, warning, danger)
   */
  function showAlert(message, type = 'warning') {
    // Remove any existing alerts
    $('.wizard-alert').remove();
    
    // Create new alert
    const $alert = $(`
      <div class="alert alert-${type} wizard-alert">
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        <span>${message}</span>
      </div>
    `);
    
    // Add alert to the top of the active tab pane
    $(_selectors.tabPanes + '.active').prepend($alert);
    
    // Set up auto-dismiss
    setTimeout(() => {
      $alert.fadeOut('slow', function() {
        $(this).remove();
      });
    }, 5000);
  }
  
  /**
   * Enable or disable the Next button
   * @param {boolean} enabled - Whether to enable the button
   */
  function enableNextButton(enabled) {
    _elements.$nextBtn.prop('disabled', !enabled);
  }
  
  /**
   * Cache jQuery DOM elements for better performance
   * @private
   */
  function _cacheElements() {
    _elements = {
      $wizardCard: $(_selectors.card),
      $form: $(_selectors.form),
      $courseSelect: $(_selectors.courseSelect),
      $nextBtn: $(_selectors.nextBtn),
      $prevBtn: $(_selectors.prevBtn),
      $resetBtn: $(_selectors.resetBtn),
      $finishBtn: $(_selectors.finishBtn)
    };
  }
  
  /**
   * Set up event listeners for UI interactions
   * @private
   */
  function _setupEventListeners() {
    // Next button handler
    $(document).on('click', '#next-btn, .btn-next', function(e) {
      e.preventDefault();
      if (_handlers.onNext) {
        _handlers.onNext();
      }
    });
    
    // Previous button handler
    $(document).on('click', '#previous-btn, .btn-previous', function(e) {
      e.preventDefault();
      if (_handlers.onPrevious) {
        _handlers.onPrevious();
      }
    });
    
    // Reset button handler
    $(document).on('click', '#reset-btn', function(e) {
      e.preventDefault();
      if (_handlers.onReset) {
        _handlers.onReset();
      }
    });
    
    // Finish button handler
    $(document).on('click', '#finish-btn', function(e) {
      e.preventDefault();
      if (_handlers.onFinish) {
        _handlers.onFinish();
      }
    });
    
    // Handle direct tab clicks (disable them)
    $(_selectors.navLinks).on('click', (e) => {
      e.preventDefault();
      return false;
    });
    
    // Window resize handler
    $(window).resize(() => {
      // Recalculate moving tab position
      const activeIndex = $(_selectors.activeNavLink).parent().index();
      _refreshAnimation(_elements.$wizardCard, activeIndex);
    });
  }
  
  /**
   * Initialize wizard appearance
   * @private
   */
  function _initWizardAppearance() {
    // Create moving tab
    const firstTitle = $('.wizard-navigation li:first-child a').html();
    const $movingTab = $("<div class='moving-tab'></div>").append(firstTitle);
    _elements.$wizardCard.find('.wizard-navigation').append($movingTab);
    
    // Initial position
    const initialIndex = $(_selectors.activeNavLink).parent().index();
    _refreshAnimation(_elements.$wizardCard, initialIndex);
    
    // Initial state
    _updateTabState(initialIndex);
  }
  
  /**
   * Set up the wizard progress bar
   * @private
   */
  function _setupProgressBar() {
    const stepCount = _elements.$wizardCard.find('.wizard-navigation li').length;
    _elements.$wizardCard.find('.wizard-navigation').append(
      '<div class="progress mt-3">' +
        '<div class="progress-bar" role="progressbar" aria-valuemin="1" aria-valuemax="' + stepCount + '" style="width: 0%;"></div>' +
      '</div>'
    );
  }
  
  /**
   * Initialize form validation
   * @private
   */
  function _initValidation() {
    // Form validation
    _elements.$form.validate({
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
  }
  
  /**
   * Update the tab state based on index
   * @param {number} index - The 0-based index of the active tab
   * @private
   */
  function _updateTabState(index) {
    const total = $(_selectors.navLinks).length;
    const current = index + 1;
    
    // Update moving tab
    const activeText = $('.nav-pills li:nth-child(' + current + ') a').html();
    setTimeout(() => {
      _elements.$wizardCard.find('.moving-tab').html(activeText);
    }, 150);
    
    // Show/hide next/finish buttons
    if (current >= total) {
      _elements.$nextBtn.hide();
      _elements.$finishBtn.show();
    } else {
      _elements.$nextBtn.show();
      _elements.$finishBtn.hide();
    }
    
    _refreshAnimation(_elements.$wizardCard, index);
  }
  
  /**
   * Update the progress bar and tab state
   * @param {number} index - The 0-based index of the active tab
   * @private
   */
  function _updateProgress(index) {
    const total = $(_selectors.navLinks).length;
    const current = index + 1;
    const percent = (current / total) * 100;
    
    // Update progress bar
    _elements.$wizardCard.find('.progress-bar').css({ width: `${percent}%` });
    
    // Update moving tab text and position
    _updateTabState(index);
  }
  
  /**
   * Enable/disable navigation buttons based on step
   * @param {number} stepNumber - The current step number (1-based)
   * @private
   */
  function _updateNavigationButtons(stepNumber) {
    // Disable previous button on first step
    _elements.$prevBtn.prop('disabled', stepNumber <= 1);
    
    // Update button states based on step data
    switch (stepNumber) {
      case 1:
        // Disable next if no course selected
        const courseId = _elements.$courseSelect.val();
        _elements.$nextBtn.prop('disabled', !courseId);
        break;
      
      // Add cases for other steps as needed
    }
  }
  
  /**
   * Refresh the animation of the moving tab
   * @param {jQuery} $wizard - The wizard jQuery element
   * @param {number} index - The 0-based index of the active tab
   * @private 
   */
  function _refreshAnimation($wizard, index) {
    const total = $wizard.find('.wizard-navigation li').length;
    const moveDistance = $wizard.find('.wizard-navigation').width() / total;
    const $movingTab = $wizard.find('.moving-tab');
    const verticalLevel = 0;
    
    $movingTab.css({
      width: moveDistance,
      transform: `translate3d(${moveDistance * index}px, ${verticalLevel * 38}px, 0)`
    });
  }
  
  // Public API
  return {
    init,
    activateStep,
    reset,
    showAlert,
    enableNextButton
  };
})();

/**
 * CourseStep module - Handles the course selection step
 */
const CourseStep = (function() {
  // Private variables
  const _selectors = {
    courseSelect: '#course_id',
    noCoursesWarning: '#no-courses-warning'
  };
  
  /**
   * Initialize the course selection step
   */
  function init() {
    const $courseSelect = $(_selectors.courseSelect);
    
    // Check if we need to populate the dropdown
    if ($courseSelect.length && $courseSelect.find('option').length <= 1) {
      _populateCourseDropdown();
    }
    
    // Set up event listeners
    _setupEventListeners();
  }
  
  /**
   * Validate the course selection step
   * @returns {boolean} - Whether the step is valid
   */
  function validate() {
    const $courseSelect = $(_selectors.courseSelect);
    const courseId = $courseSelect.val();
    
    if (!courseId) {
      WizardUI.showAlert('Please select a course to continue.', 'warning');
      return false;
    }
    
    return true;
  }
  
  /**
   * Get the data for this step
   * @returns {Object} - The step data
   */
  function getData() {
    const $courseSelect = $(_selectors.courseSelect);
    return {
      course_id: $courseSelect.val()
    };
  }
  
  /**
   * Populate the course dropdown with data from state
   * @private
   */
  function _populateCourseDropdown() {
    const $courseSelect = $(_selectors.courseSelect);
    const courses = WizardState.get('courses') || [];
    
    if (courses && courses.length) {
      courses.forEach(course => {
        if (course && course.canvas_id && course.course_code && course.name) {
          $courseSelect.append(`<option value="${course.canvas_id}">${course.course_code} - ${course.name}</option>`);
        }
      });
      
      // Hide warning and enable next button
      $(_selectors.noCoursesWarning).hide();
      WizardUI.enableNextButton(true);
    } else {
      $courseSelect.append('<option value="" disabled>No courses available - please import courses from Canvas</option>');
      
      // Show the warning message
      $(_selectors.noCoursesWarning).show();
      
      // Disable next button since we can't proceed without courses
      WizardUI.enableNextButton(false);
    }
    
    // If there's a selected course in state, set it
    const selectedCourseId = WizardState.get('course_id');
    if (selectedCourseId) {
      $courseSelect.val(selectedCourseId);
    }
  }
  
  /**
   * Set up event listeners for this step
   * @private
   */
  function _setupEventListeners() {
    const $courseSelect = $(_selectors.courseSelect);
    
    // Course change handler
    $courseSelect.on('change', function() {
      const courseId = $(this).val();
      
      // Update state
      WizardState.set('course_id', courseId);
      
      // Enable/disable next button
      WizardUI.enableNextButton(!!courseId);
    });
  }
  
  // Public API
  return {
    init,
    validate,
    getData
  };
})();

// Add other step handlers here: GroupSetStep, GroupsStep, etc.

/**
 * GroupsStep module - Handles the group selection step
 */
const GroupsStep = (function() {
  // Private variables
  const _selectors = {
    groupsContainer: '#groups-container',
    groupSetsContainer: '#group-sets-container',
    noGroupsWarning: '#no-groups-warning'
  };
  
  /**
   * Initialize the group selection step
   */
  function init() {
    // Update the groups view
    _updateGroupsList();
    
    // Set up event listeners
    _setupEventListeners();
  }
  
  /**
   * Validate the group selection step
   * @returns {boolean} - Whether the step is valid
   */
  function validate() {
    const selectedGroups = $('input[name="group_ids"]:checked');
    
    if (selectedGroups.length === 0) {
      WizardUI.showAlert('Please select at least one group to continue.', 'warning');
      return false;
    }
    
    return true;
  }
  
  /**
   * Get the data for this step
   * @returns {Object} - The step data
   */
  function getData() {
    const groupIds = [];
    $('input[name="group_ids"]:checked').each(function() {
      groupIds.push($(this).val());
    });
    
    return {
      group_ids: groupIds
    };
  }
  
  /**
   * Update the groups list based on selected group sets
   * @private
   */
  function _updateGroupsList() {
    const $groupsContainer = $(_selectors.groupsContainer);
    const $groupSetsContainer = $(_selectors.groupSetsContainer);
    $groupsContainer.empty();
    $groupSetsContainer.empty();
    
    // Get selected group sets from state
    const selectedGroupSetIds = WizardState.get('group_set_ids') || [];
    
    if (selectedGroupSetIds.length === 0) {
      $groupsContainer.append('<div class="alert alert-warning">No group sets selected. Please go back and select at least one group set.</div>');
      WizardUI.enableNextButton(false);
      return;
    }
    
    // Get groups data from state
    const groups = WizardState.get('groups') || [];
    
    if (groups.length === 0) {
      // Show the no groups warning
      $(_selectors.noGroupsWarning).show();
      $groupsContainer.append('<div class="alert alert-warning">No groups found for the selected group sets. Please import groups from Canvas first.</div>');
      WizardUI.enableNextButton(false);
      return;
    } else {
      // Hide the warning
      $(_selectors.noGroupsWarning).hide();
    }
    
    // Organize groups by category
    const groupsByCategory = _organizeGroupsByCategory(groups);
    
    let anyGroupsFound = false;
    
    // Add group set titles and select/deselect controls
    selectedGroupSetIds.forEach(groupSetId => {
      const categoryData = groupsByCategory[groupSetId];
      const groupSetName = categoryData ? categoryData.name : $(`label[for="group_set_${groupSetId}"]`).text().trim();
      const groupsInSet = categoryData ? categoryData.groups : [];
      
      // Add the group set header
      $groupSetsContainer.append(`
        <div class="group-set-header mb-3" id="group-set-header-${groupSetId}">
          <h5 class="mb-2">${groupSetName}</h5>
          <div class="mb-3">
            <button type="button" class="btn btn-sm btn-outline-primary select-all-groups me-2" data-group-set="${groupSetId}">
              Select All
            </button>
            <button type="button" class="btn btn-sm btn-outline-secondary deselect-all-groups" data-group-set="${groupSetId}">
              Deselect All
            </button>
          </div>
        </div>
      `);
      
      if (groupsInSet.length === 0) {
        $(`#group-set-header-${groupSetId}`).append(`
          <div class="alert alert-warning">No groups found in this group set.</div>
        `);
      } else {
        anyGroupsFound = true;
        
        // Create a row for the card layout
        const $groupRow = $(`<div class="row" id="group-set-${groupSetId}-groups"></div>`);
        $groupsContainer.append($groupRow);
        
        // Add cards for each group
        groupsInSet.forEach(group => {
          // Create card for each group
          const membersCount = group.members_count || 0;
          let membersList = '';
          
          // For demo purposes, we'll create dummy member names
          const dummyMembers = [];
          for (let i = 1; i <= membersCount; i++) {
            dummyMembers.push(`Student ${i}`);
          }
          
          // Create the members list HTML
          if (dummyMembers.length > 0) {
            membersList = `
              <ul class="list-group list-group-flush">
                ${dummyMembers.map(member => `
                  <li class="list-group-item border-0 py-1 px-3">${member}</li>
                `).join('')}
              </ul>
            `;
          } else {
            membersList = `
              <p class="text-muted p-3">No members in this group</p>
            `;
          }
          
          // Add the card to the row
          $groupRow.append(`
            <div class="col-md-4 mb-4">
              <div class="card wizard-card h-100">
                <div class="card-header">
                  <h6 class="mb-0">${group.name}</h6>
                  <small class="text-muted">${membersCount} member${membersCount !== 1 ? 's' : ''}</small>
                </div>
                <div class="card-body p-0">
                  ${membersList}
                </div>
                <div class="card-footer">
                  <div class="form-check text-center">
                    <input class="form-check-input" type="checkbox" name="group_ids" value="${group.canvas_id}" id="group_${group.canvas_id}" data-group-set="${groupSetId}" checked>
                    <label class="form-check-label" for="group_${group.canvas_id}">
                      Select this group
                    </label>
                  </div>
                </div>
              </div>
            </div>
          `);
        });
      }
    });
    
    // Disable next button if no groups were found
    if (!anyGroupsFound) {
      WizardUI.enableNextButton(false);
      $(_selectors.noGroupsWarning).show();
    } else {
      WizardUI.enableNextButton(true);
    }
  }
  
  /**
   * Organize groups by their category/group set
   * @param {Array} groups - The groups data
   * @returns {Object} - Groups organized by category ID
   * @private
   */
  function _organizeGroupsByCategory(groups) {
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
    
    return groupsByCategory;
  }
  
  /**
   * Set up event listeners for this step
   * @private
   */
  function _setupEventListeners() {
    // Handle select all button clicks
    $(document).off('click', '.select-all-groups').on('click', '.select-all-groups', function() {
      const groupSetId = $(this).data('group-set');
      $(`input[name="group_ids"][data-group-set="${groupSetId}"]`).prop('checked', true);
    });
    
    // Handle deselect all button clicks
    $(document).off('click', '.deselect-all-groups').on('click', '.deselect-all-groups', function() {
      const groupSetId = $(this).data('group-set');
      $(`input[name="group_ids"][data-group-set="${groupSetId}"]`).prop('checked', false);
    });
  }
  
  // Public API
  return {
    init,
    validate,
    getData
  };
})();

/* Add minimal stubs for other steps for now */
const GroupSetStep = {
  init: function() { console.log('GroupSetStep init'); },
  validate: function() { return true; },
  getData: function() { return {}; }
};

const IntegrationStep = {
  init: function() { console.log('IntegrationStep init'); },
  validate: function() { return true; },
  getData: function() { return {}; }
};

const SummaryStep = {
  init: function() { console.log('SummaryStep init'); },
  validate: function() { return true; },
  getData: function() { return {}; }
};

const ResultsStep = {
  init: function() { console.log('ResultsStep init'); },
  validate: function() { return true; },
  getData: function() { return {}; }
};

// Helper functions
function safeParse(data) {
  if (typeof data !== 'string') return data;

  try {
    return JSON.parse(data);
  } catch (e) {
    console.error('Error parsing JSON:', e);
    return [];
  }
}

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