$(document).ready(function() {
  // Initialize the bootstrap wizard
  $('#wizardSync').bootstrapWizard({
    tabClass: 'nav nav-pills',
    nextSelector: '.btn-next',
    previousSelector: '.btn-previous',
    onTabShow: function(tab, navigation, index) {
      var $total = navigation.find('li').length;
      var $current = index + 1;
      
      // Update progress
      var $percent = ($current / $total) * 100;
      $('#wizardSync .progress-bar').css({width: $percent + '%'});
      
      // Show/hide buttons based on current step
      if ($current == 1) {
        $('#previous-btn').addClass('disabled');
      } else {
        $('#previous-btn').removeClass('disabled');
      }
      
      if ($current >= $total) {
        $('#next-btn').hide();
        $('#finish-btn').show();
      } else {
        $('#next-btn').show();
        $('#finish-btn').hide();
      }
    },
    onNext: function(tab, navigation, index) {
      // Submit form with AJAX to update session data
      var $form = $('#sync-wizard-form');
      var formData = new FormData($form[0]);
      formData.append('step', index);
      formData.append('action', 'next');
      
      // You can add form validation here before moving to next step
      
      $.ajax({
        url: $form.attr('action'),
        method: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        success: function(response) {
          // Handle response if needed
        },
        error: function(xhr, status, error) {
          // Handle errors
          console.error('Error:', error);
          return false;
        }
      });
      
      return true;
    },
    onPrevious: function(tab, navigation, index) {
      var $form = $('#sync-wizard-form');
      var formData = new FormData($form[0]);
      formData.append('step', index + 1); // Current step before going back
      formData.append('action', 'previous');
      
      $.ajax({
        url: $form.attr('action'),
        method: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        success: function(response) {
          // Handle response if needed
        }
      });
      
      return true;
    }
  });
  
  // Add progress bar to wizard
  $('#wizardSync .wizard-navigation').append(
    '<div class="progress mt-3">' +
    '  <div class="progress-bar" role="progressbar" aria-valuenow="1" aria-valuemin="1" aria-valuemax="6" style="width: 16.66%;"></div>' +
    '</div>'
  );
  
  // Handle form submission
  $('#sync-wizard-form').on('submit', function(e) {
    e.preventDefault();
    
    var $form = $(this);
    var formData = new FormData($form[0]);
    formData.append('action', 'finish');
    
    $.ajax({
      url: $form.attr('action'),
      method: 'POST',
      data: formData,
      processData: false,
      contentType: false,
      success: function(response) {
        // Handle successful completion
        if (response.redirect) {
          window.location.href = response.redirect;
        }
      },
      error: function(xhr, status, error) {
        // Handle errors
        console.error('Error:', error);
      }
    });
  });
});