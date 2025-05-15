/**
 * Main Wizard Entry Point
 * 
 * This file serves as the main entry point for the wizard functionality.
 * It coordinates the initialization and operation of the wizard components.
 */

// Import modules
import WizardState from './wizard-state.js';
import WizardUI from './wizard-ui.js';
import WizardAPI from './wizard-api.js';

// Step handlers
import CourseStep from './steps/step1-courses.js';
import GroupSetStep from './steps/step2-group-sets.js';
import GroupsStep from './steps/step3-groups.js';
import IntegrationStep from './steps/step4-integration.js';
import SummaryStep from './steps/step5-summary.js';
import ResultsStep from './steps/step6-results.js';

/**
 * Initialize the wizard when the DOM is fully loaded
 */
document.addEventListener('DOMContentLoaded', () => {
  // Initialize state
  WizardState.init();
  
  // Initialize UI components
  WizardUI.init({
    onNext: handleNextStep,
    onPrevious: handlePreviousStep,
    onReset: handleReset
  });
  
  // Initialize step handlers
  const stepHandlers = {
    1: CourseStep,
    2: GroupSetStep,
    3: GroupsStep,
    4: IntegrationStep, 
    5: SummaryStep,
    6: ResultsStep
  };
  
  // Initialize based on current step
  const currentStep = WizardState.getCurrentStep();
  activateStep(currentStep);

  /**
   * Handle navigation to the next step
   */
  function handleNextStep() {
    const currentStep = WizardState.getCurrentStep();
    const stepHandler = stepHandlers[currentStep];
    
    if (stepHandler && stepHandler.validate()) {
      // Gather step data and submit
      const stepData = stepHandler.getData();
      
      WizardAPI.submitStep('next', stepData, (response) => {
        // Update state with response data
        WizardState.updateFromResponse(response);
        
        // Activate next step
        const nextStep = currentStep + 1;
        activateStep(nextStep);
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
      activateStep(prevStep);
    });
  }
  
  /**
   * Reset the wizard state
   */
  function handleReset() {
    if (confirm('Are you sure you want to restart the wizard? All progress will be lost.')) {
      WizardAPI.submitStep('reset', {}, (response) => {
        // Update state with response data
        WizardState.updateFromResponse(response);
        
        // Reset UI
        WizardUI.reset();
        
        // Activate first step
        activateStep(1);
      });
    }
  }
  
  /**
   * Activate a specific step in the wizard
   * @param {number} stepNumber - The step number to activate
   */
  function activateStep(stepNumber) {
    // Update UI for the step
    WizardUI.activateStep(stepNumber);
    
    // Initialize step content
    const stepHandler = stepHandlers[stepNumber];
    if (stepHandler && stepHandler.init) {
      stepHandler.init();
    }
  }
});