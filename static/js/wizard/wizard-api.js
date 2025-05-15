/**
 * Wizard API Module
 * 
 * This module handles all AJAX communication with the server for the wizard.
 */

import { getCookie } from './utils/helpers.js';

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
  
  /**
   * Fetch courses data 
   * @param {Function} onSuccess - Success callback
   * @param {Function} onError - Error callback (optional)
   */
  function fetchCourses(onSuccess, onError) {
    // This could be a separate API endpoint in the future
    submitStep('fetch_courses', {}, onSuccess, onError);
  }
  
  /**
   * Fetch group sets for a course
   * @param {string|number} courseId - The Canvas course ID
   * @param {Function} onSuccess - Success callback
   * @param {Function} onError - Error callback (optional)
   */
  function fetchGroupSets(courseId, onSuccess, onError) {
    // This could be a separate API endpoint in the future
    submitStep('fetch_group_sets', { course_id: courseId }, onSuccess, onError);
  }
  
  /**
   * Fetch groups for selected group sets
   * @param {Array} groupSetIds - Array of group set IDs
   * @param {Function} onSuccess - Success callback
   * @param {Function} onError - Error callback (optional) 
   */
  function fetchGroups(groupSetIds, onSuccess, onError) {
    // This could be a separate API endpoint in the future
    submitStep('fetch_groups', { group_set_ids: groupSetIds }, onSuccess, onError);
  }
  
  // Public API
  return {
    init,
    submitStep,
    fetchCourses,
    fetchGroupSets,
    fetchGroups
  };
})();

export default WizardAPI;