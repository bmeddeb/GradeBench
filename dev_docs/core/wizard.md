# Canvas Group to Core Team Sync Wizard Template

This document defines the **base HTML template** for the multi‑step synchronization wizard. It outlines the overall layout, placeholder blocks, and the data context needed for rendering and controlling the wizard flow.

---

## 1. Page Layout

```html
{% extends "paper_dashboard/base.html" %}

{% load static %}

{% block head %}
  <!-- Paper Dashboard CSS -->
  <link href="{% static 'css/bootstrap.min.css' %}" rel="stylesheet" />
  <link href="{% static 'css/paper-dashboard.css?v=2.1.1' %}" rel="stylesheet" />
  <!-- Optional demo CSS (omit in production) -->
  <link href="{% static 'css/demo.css' %}" rel="stylesheet" />
{% endblock %}

{% block content %}
<div class="content">
  <div class="col-md-10 mr-auto ml-auto">
    <div class="wizard-container">
      <div class="card card-wizard" data-color="primary" id="wizardSync">
        <form id="sync-wizard-form" method="post" action="{% url 'wizard_main' %}">
          {% csrf_token %}
          <!-- Header -->
          <div class="card-header text-center">
            <h3 class="card-title">Canvas Group to Core Team Sync</h3>
            <h5 class="description">Follow the steps to complete synchronization</h5>
            <div class="wizard-navigation">
              <ul>
                {% for label in progress_labels %}
                <li class="nav-item">
                  <a class="nav-link {% if forloop.counter == current_step %}active{% endif %}"
                     href="#step{{ forloop.counter }}"
                     data-toggle="tab"
                     role="tab"
                     aria-controls="step{{ forloop.counter }}"
                     aria-selected="{{ forloop.counter == current_step }}">
                    {{ label }}
                  </a>
                </li>
                {% endfor %}
              </ul>
            </div>
          </div>

          <!-- Body -->
          <div class="card-body">
            <div class="tab-content">
              {% block step_content %}{% endblock %}
            </div>
          </div>

          <!-- Footer Buttons -->
          <div class="card-footer">
            <div class="pull-left">
              <button type="button"
                      id="previous-btn"
                      class="btn btn-previous btn-fill btn-default btn-wd"
                      {% if not back_enabled %}disabled{% endif %}>
                Previous
              </button>
            </div>
            <div class="pull-right">
              {% if current_step < progress_labels|length %}
              <button type="button"
                      id="next-btn"
                      class="btn btn-next btn-fill btn-primary btn-wd"
                      {% if not next_enabled %}disabled{% endif %}>
                Next
              </button>
              {% else %}
              <button type="submit"
                      id="finish-btn"
                      class="btn btn-finish btn-fill btn-primary btn-wd">
                Finish
              </button>
              {% endif %}
            </div>
            <div class="clearfix"></div>
          </div>
        </form>
      </div>
    </div> <!-- wizard-container -->
  </div>
</div>
{% endblock %}

{% block scripts %}
  <!-- Core JS -->
  <script src="{% static 'js/core/jquery.min.js' %}"></script>
  <script src="{% static 'js/core/popper.min.js' %}"></script>
  <script src="{% static 'js/core/bootstrap.min.js' %}"></script>
  <!-- Wizard plugin -->
  <script src="{% static 'js/plugins/jquery.bootstrap-wizard.js' %}"></script>
  <!-- Form validation -->
  <script src="{% static 'js/plugins/jquery.validate.min.js' %}"></script>

  <script>
    $(function() {
      $('#sync-wizard-form').bootstrapWizard({
        tabClass: 'nav nav-pills',
        nextSelector: '.btn-next',
        previousSelector: '.btn-previous',
        onTabShow: function($tab, $navigation, index) {
          // Enable/disable Next/Finish button
          var total = {{ progress_labels|length }};
          var current = index + 1;
          $('#next-btn').toggle(current < total);
          $('#finish-btn').toggle(current === total);
        }
      });
    });
  </script>
{% endblock %}
```
Notes:

Replace references to paper_dashboard/base.html with your actual base layout if different.

Ensure static assets (CSS/JS) paths align with your Django collectstatic settings.

This wrapper injects the 6-step tabs dynamically via progress_labels and uses block step_content for step-specific partials.

The form posts at the final step; intermediate steps should persist selections in session via AJAX in your view logic.

6. Wire Up & Test in Django

To serve and test this wizard at http://<host>/wizard/, follow these steps:

6.1. Add URL Route

In your core app’s urls.py, include:
```python
# core/urls.py
from django.urls import path
from .views import wizard_view

urlpatterns = [
    # ... other routes ...
    path('wizard/', wizard_view, name='wizard_main'),
]
```
Make sure your project’s main urls.py includes the core app:
```python
# project/urls.py
from django.urls import include, path

urlpatterns = [
    # ...
    path('', include('core.urls')),
]
```
In core/views.py, implement a simple view to render the template with dummy context:
```python
# core/views.py
from django.shortcuts import render

def wizard_view(request):
    # Initial test: always show step 1
    context = {
        'progress_labels': [
            'Course Selection', 'Group Set Selection',
            'Group Selection', 'Integration Config',
            'Confirmation', 'Results'
        ],
        'current_step': 1,
        'back_enabled': False,
        'next_enabled': True,
    }
    return render(request, 'wizard_template.html', context)
```
6.3. Add a Stub Partial

Create a minimal partial for step 1 so the page renders without errors:
```html
<!-- templates/wizard/step_1_course_selection.md -->
<div class="tab-pane show active" id="step1">
  <h5 class="info-text">Step 1: Course Selection (stub)</h5>
</div>
6.4. Collect Static & Run

Run python manage.py collectstatic (if using DEBUG=False).
```

Start the dev server:
```bash
python manage.py runserver
```
Once you confirm the basic template renders, you can replace stubs with the real partials and add AJAX logic in your view to handle step transitions.

and proceed with the following steps
---

## 2. Context Data Requirements

The master template expects the following context variables:

| Variable          | Type        | Description                                                |
| ----------------- | ----------- | ---------------------------------------------------------- |
| `current_step`    | `int`       | Index of the active step (1–6)                             |
| `back_enabled`    | `bool`      | Whether "Back" button should be enabled                    |
| `next_enabled`    | `bool`      | Whether "Next" button should be enabled                    |
| `progress_labels` | `List[str]` | Labels for each step (e.g., \["Course", "Group Set", ...]) |
| `step_data`       | `dict`      | Per-step data payload (loaded via AJAX)                    |

---

## 3. Step-Specific Includes

Each wizard step is rendered via its own partial template. Include them in the `step_content` block based on `current_step`:

```django
{% block step_content %}
  {% if current_step == 1 %}
    {% include "wizard/step_1_course_selection.md" %}
  {% elif current_step == 2 %}
    {% include "wizard/step_2_group_set_selection.md" %}
  {% elif current_step == 3 %}
    {% include "wizard/step_3_group_selection.md" %}
  {% elif current_step == 4 %}
    {% include "wizard/step_4_integration_config.md" %}
  {% elif current_step == 5 %}
    {% include "wizard/step_5_confirmation.md" %}
  {% elif current_step == 6 %}
    {% include "wizard/step_6_results.md" %}
  {% endif %}
{% endblock %}
```

---

## 4. Links to Detailed Step Documents

* [Step 1: Course Selection & Integration Toggles](step_1_course_selection.md)
* [Step 2: Group Set Selection](step_2_group_set_selection.md)
* [Step 3: Group Selection](step_3_group_selection.md)
* [Step 4: Integration Configuration](step_4_integration_config.md)
* [Step 5: Confirmation Summary](step_5_confirmation.md)
* [Step 6: Results Display](step_6_results.md)

---

## 5. Next Steps

1. Create each `step_X_*.md` with:

   * **HTML structure** for that step
   * **Data variables** needed
   * **AJAX endpoints** to fetch/save data
   * **Form elements** and validation rules
2. Wire up JavaScript to:

   * Load `step_data[current_step]` via AJAX
   * Handle `Back`/`Next` clicks and persist selections
   * Update progress bar dynamically

Once each step document is in place, link them into this master template and start implementing the view logic accordingly.
