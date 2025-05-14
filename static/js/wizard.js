
$(document).ready(function() {
  var $wizardCard = $('.card-wizard');
  var $form = $wizardCard.find('form');

  // Show wizard card (Paper Dashboard CSS hides it until .active)
  $wizardCard.addClass('active');

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

  // Initialize wizard
  $wizardCard.bootstrapWizard({
    tabClass: 'nav nav-pills',
    nextSelector: '.btn-next',
    previousSelector: '.btn-previous',

    onInit: function(tab, navigation, index) {
      var totalSteps = navigation.find('li').length;
      var firstTitle = navigation.find('li:first-child a').html();
      var $movingTab = $("<div class='moving-tab'></div>").append(firstTitle);
      $wizardCard.find('.wizard-navigation').append($movingTab);

      refreshAnimation($wizardCard, index);
      $wizardCard.find('.moving-tab').css('transition', 'transform 0s');
    },

    onTabClick: function(tab, navigation, index) {
      if (!$validator.form()) {
        $validator.focusInvalid();
        return false;
      }
      return true;
    },

    onNext: function(tab, navigation, index) {
      if (!$form.valid()) {
        $validator.focusInvalid();
        return false;
      }
      // AJAX "next" action
      var formData = new FormData($form[0]);
      formData.append('action', 'next');
      $.ajax({
        url: $form.attr('action'),
        type: 'POST',
        data: formData,
        processData: false,
        contentType: false
      });
      return true;
    },

    onPrevious: function(tab, navigation, index) {
      var formData = new FormData($form[0]);
      formData.append('action', 'previous');
      $.ajax({
        url: $form.attr('action'),
        type: 'POST',
        data: formData,
        processData: false,
        contentType: false
      });
      return true;
    },

    onTabShow: function(tab, navigation, index) {
      var total = navigation.find('li').length;
      var current = index + 1;
      var percent = (current / total) * 100;

      // Update progress bar
      $wizardCard.find('.progress-bar').css({ width: percent + '%' });

      // Show/hide buttons
      if (current >= total) {
        $wizardCard.find('.btn-next').hide();
        $wizardCard.find('.btn-finish').show();
      } else {
        $wizardCard.find('.btn-next').show();
        $wizardCard.find('.btn-finish').hide();
      }

      // Update moving-tab text
      var activeText = navigation.find('li:nth-child(' + current + ') a').html();
      setTimeout(function() {
        $wizardCard.find('.moving-tab').html(activeText);
      }, 150);

      refreshAnimation($wizardCard, index);
    }
  });

  // Append progress bar
  var stepCount = $wizardCard.find('.wizard-navigation li').length;
  $wizardCard.find('.wizard-navigation').append(
    '<div class="progress mt-3">' +
      '<div class="progress-bar" role="progressbar" aria-valuemin="1" aria-valuemax="' + stepCount + '" style="width: 0%;"></div>' +
    '</div>'
  );

  // Helper to animate moving-tab
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
});
