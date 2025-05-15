/**
 * Step 3: Group Selection
 * 
 * This module handles the logic for the third step of the wizard,
 * where the user selects groups to synchronize.
 */

import WizardState from '../wizard-state.js';
import WizardUI from '../wizard-ui.js';
import { createElement } from '../utils/helpers.js';

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
      _renderGroupSetHeader($groupSetsContainer, groupSetId, groupSetName);
      
      if (groupsInSet.length === 0) {
        $(`#group-set-header-${groupSetId}`).append(`
          <div class="alert alert-warning">No groups found in this group set.</div>
        `);
      } else {
        anyGroupsFound = true;
        
        // Create a row for the card layout and add it to container
        _renderGroupCards($groupsContainer, groupSetId, groupsInSet);
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
   * Render a group set header with select/deselect buttons
   * @param {jQuery} $container - The container element
   * @param {string|number} groupSetId - The group set ID
   * @param {string} groupSetName - The group set name
   * @private
   */
  function _renderGroupSetHeader($container, groupSetId, groupSetName) {
    $container.append(`
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
  }
  
  /**
   * Render group cards for a group set
   * @param {jQuery} $container - The container element
   * @param {string|number} groupSetId - The group set ID
   * @param {Array} groups - The groups to render
   * @private
   */
  function _renderGroupCards($container, groupSetId, groups) {
    // Create a row for the cards
    const $groupRow = $(`<div class="row" id="group-set-${groupSetId}-groups"></div>`);
    $container.append($groupRow);
    
    // Add cards for each group
    groups.forEach(group => {
      // Create card for each group
      const membersCount = group.members_count || 0;
      
      // In a real implementation, this would be fetched from the server 
      // based on CanvasGroupMembership and CanvasEnrollment
      const membersList = _generateMembersList(group);
      
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
  
  /**
   * Generate HTML for the members list
   * @param {Object} group - The group data
   * @returns {string} - HTML for the members list
   * @private
   */
  function _generateMembersList(group) {
    const membersCount = group.members_count || 0;
    
    // For demo purposes, we'll create dummy member names
    // In a real implementation, you would fetch this from the API
    if (membersCount > 0) {
      const memberItems = [];
      
      // For now, generate placeholder members
      for (let i = 1; i <= membersCount; i++) {
        memberItems.push(`<li class="list-group-item border-0 py-1 px-3">Student ${i}</li>`);
      }
      
      return `
        <ul class="list-group list-group-flush">
          ${memberItems.join('')}
        </ul>
      `;
    } else {
      return `<p class="text-muted p-3">No members in this group</p>`;
    }
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

export default GroupsStep;