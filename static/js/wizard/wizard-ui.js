/**
 * Wizard UI Module
 * 
 * This module handles the user interface components of the wizard,
 * including tab switching, progress tracking, and UI updates.
 */

import WizardState from './wizard-state.js';

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

export default WizardUI;