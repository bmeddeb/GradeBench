/**
 * Wizard State Management
 * 
 * This module handles state management for the wizard, providing a central
 * repository for data and state that is shared between different components.
 */

import { safeParse } from './utils/helpers.js';

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

export default WizardState;