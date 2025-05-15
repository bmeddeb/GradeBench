/**
 * Step 1: Course Selection
 * 
 * This module handles the logic for the first step of the wizard,
 * where the user selects a Canvas course.
 */

import WizardState from '../wizard-state.js';
import WizardUI from '../wizard-ui.js';

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

export default CourseStep;