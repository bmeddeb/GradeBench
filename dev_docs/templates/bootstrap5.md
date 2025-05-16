 Detailed Implementation Plan: Migration to django-bootstrap5

  Phase 1: Setup & Configuration (Day 1)

  1.1 Install django-bootstrap5

  pip install django-bootstrap5

  1.2 Update pyproject.toml

  # Add to dependencies
  dependencies = [
      # Existing dependencies...
      "django-bootstrap5>=23.3",
  ]

  1.3 Add to INSTALLED_APPS in settings.py

  INSTALLED_APPS = [
      # Existing apps...
      'django_bootstrap5',
  ]

  1.4 Configure django-bootstrap5 in settings.py

  # django-bootstrap5 settings
  BOOTSTRAP5 = {
      # Use the CDN versions already in use in the project
      'css_url': {
          'href': 'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bo
  otstrap.min.css',
          'crossorigin': 'anonymous',
      },
      'javascript_url': {
          'href': 'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/boo
  tstrap.bundle.min.js',
          'crossorigin': 'anonymous',
      },
      # Form field settings
      'required_css_class': 'required',
      'error_css_class': 'is-invalid',
      'success_css_class': 'is-valid',

      # Layout settings
      'horizontal_label_class': 'col-md-3',
      'horizontal_field_class': 'col-md-9',

      # Misc settings
      'set_placeholder': False,
      'formset_renderers': {
          'default': 'django_bootstrap5.renderers.FormsetRenderer',
      },
      'form_renderers': {
          'default': 'django_bootstrap5.renderers.FormRenderer',
      },
      'field_renderers': {
          'default': 'django_bootstrap5.renderers.FieldRenderer',
      },
  }

  Phase 2: Create Theme Bridge (Day 1-2)

  2.1 Create paper-dashboard-bs5.css

  /* /static/css/paper-dashboard-bs5.css */

  /**
   * Paper Dashboard Bootstrap 5 Theme Bridge
   * This file adapts Paper Dashboard styling to Bootstrap 5
   */

  /* Override Bootstrap 5 variables with Paper Dashboard aesthetic */
  :root {
      /* Colors from Paper Dashboard */
      --bs-primary: var(--gb-primary);
      --bs-secondary: var(--gb-secondary);
      --bs-success: var(--gb-success);
      --bs-info: var(--gb-info);
      --bs-warning: var(--gb-warning);
      --bs-danger: var(--gb-danger);

      /* Typography */
      --bs-body-font-family: var(--gb-font-family-base);
      --bs-body-font-size: var(--gb-font-size-md);
      --bs-body-font-weight: var(--gb-font-weight-normal);
      --bs-body-line-height: var(--gb-line-height-normal);

      /* Border radius */
      --bs-border-radius: var(--gb-border-radius-sm);
      --bs-border-radius-sm: calc(var(--gb-border-radius-sm) * 0.8);
      --bs-border-radius-lg: var(--gb-border-radius-md);
      --bs-border-radius-xl: var(--gb-border-radius-lg);
      --bs-border-radius-2xl: var(--gb-border-radius-pill);

      /* Form element settings */
      --bs-input-bg: var(--gb-background-card);
      --bs-input-color: var(--gb-text-primary);
      --bs-input-border-color: var(--gb-border-medium);
      --bs-input-focus-border-color: var(--gb-primary);
  }

  /* Cards - the cornerstone of Paper Dashboard */
  .card {
      background-color: var(--gb-background-card);
      border-radius: var(--gb-card-border-radius);
      border: var(--gb-card-border-width) solid var(--gb-border-light);
      margin-bottom: var(--gb-space-lg);
      box-shadow: var(--gb-shadow-sm);
      transition: transform var(--gb-transition-fast), box-shadow
  var(--gb-transition-fast);
  }

  .card:hover {
      box-shadow: var(--gb-shadow-md);
  }

  .card-header {
      background-color: transparent;
      border-bottom: var(--gb-card-border-width) solid
  var(--gb-border-light);
      padding: var(--gb-space-md) var(--gb-space-lg);
  }

  .card-title {
      margin-bottom: calc(var(--gb-space-xs) / 2);
      font-weight: var(--gb-font-weight-semibold);
      font-size: var(--gb-font-size-lg);
      color: var(--gb-text-primary);
  }

  .card-category {
      font-size: var(--gb-font-size-sm);
      color: var(--gb-text-secondary);
      margin-bottom: 0;
  }

  .card-body {
      padding: var(--gb-space-lg);
  }

  .card-footer {
      background-color: transparent;
      border-top: var(--gb-card-border-width) solid var(--gb-border-light);
      padding: var(--gb-space-md) var(--gb-space-lg);
  }

  /* Buttons with fill style */
  .btn-fill {
      color: #fff;
      background-color: var(--gb-primary);
      border-color: var(--gb-primary);
  }

  .btn-fill:hover {
      background-color: var(--gb-primary-dark);
      border-color: var(--gb-primary-dark);
  }

  .btn-fill.btn-success {
      background-color: var(--gb-success);
      border-color: var(--gb-success);
  }

  .btn-fill.btn-success:hover {
      background-color: var(--gb-success-dark);
      border-color: var(--gb-success-dark);
  }

  .btn-fill.btn-danger {
      background-color: var(--gb-danger);
      border-color: var(--gb-danger);
  }

  .btn-fill.btn-danger:hover {
      background-color: var(--gb-danger-dark);
      border-color: var(--gb-danger-dark);
  }

  /* Sidebar styling */
  .sidebar {
      background-color: var(--gb-background-sidebar);
      box-shadow: var(--gb-shadow-md);
  }

  .sidebar .nav-link {
      color: var(--gb-text-primary);
      font-weight: var(--gb-font-weight-normal);
      padding: 0.75rem 1.5rem;
      transition: all var(--gb-transition-fast);
  }

  .sidebar .nav-link:hover,
  .sidebar .nav-link.active {
      background-color: var(--gb-secondary-light);
      color: var(--gb-primary);
  }

  .sidebar .nav-link i {
      margin-right: var(--gb-space-sm);
      font-size: 1.25em;
  }

  /* Table styling */
  .table thead.text-primary th {
      color: var(--gb-primary);
      font-weight: var(--gb-font-weight-semibold);
      border-bottom-width: 1px;
  }

  .table-hover tbody tr:hover {
      background-color: var(--gb-secondary-light);
  }

  /* Form control styling */
  .form-control {
      border: 1px solid var(--gb-border-medium);
      border-radius: var(--gb-border-radius-sm);
      padding: var(--gb-input-padding-y) var(--gb-input-padding-x);
      transition: border-color var(--gb-transition-fast), box-shadow
  var(--gb-transition-fast);
  }

  .form-control:focus {
      border-color: var(--gb-primary);
      box-shadow: 0 0 0 0.25rem rgba(var(--gb-primary-rgb), 0.25);
  }

  .form-label {
      font-weight: var(--gb-font-weight-semibold);
      margin-bottom: var(--gb-space-xs);
      color: var(--gb-text-primary);
  }

  .form-text {
      color: var(--gb-text-secondary);
      font-size: var(--gb-font-size-sm);
      margin-top: var(--gb-space-xs);
  }

  /* Badge adjustments */
  .badge {
      text-transform: uppercase;
      font-weight: var(--gb-font-weight-semibold);
      padding: 0.35em 0.65em;
      border-radius: var(--gb-border-radius-pill);
  }

  2.2 Update variables.css to include Bootstrap 5 RGB variables

  /* Add these to /static/css/variables.css */

  :root {
      /* Existing variables... */

      /* RGB versions for opacity support */
      --gb-primary-rgb: 0, 123, 255;
      --gb-secondary-rgb: 108, 117, 125;
      --gb-success-rgb: 40, 167, 69;
      --gb-danger-rgb: 220, 53, 69;
      --gb-warning-rgb: 255, 193, 7;
      --gb-info-rgb: 23, 162, 184;
  }

  Phase 3: Update Base Templates (Day 3-4)

  3.1 Create template components directory

  mkdir -p templates/components

  3.2 Create _sidebar.html partial

  <!-- templates/components/_sidebar.html -->
  <div class="sidebar" data-color="default" data-active-color="danger">
      <div class="logo">
          <a href="{% url 'home' %}" class="simple-text logo-mini">
              <div class="logo-image-small">
                  <img src="/static/img/logo-small.png">
              </div>
          </a>
          <a href="{% url 'home' %}" class="simple-text logo-normal">
              GradeBench
          </a>
      </div>

      <div class="sidebar-wrapper">
          {% if user.is_authenticated %}
          <div class="user">
              <!-- User profile section -->
              {% include 'components/_user_profile.html' %}
          </div>
          {% endif %}

          <ul class="nav">
              <!-- Navigation items -->
              {% include 'components/_nav_items.html' %}
          </ul>
      </div>
  </div>

  3.3 Create _user_profile.html partial

  <!-- templates/components/_user_profile.html -->
  <div class="photo">
      {% if user.profile.github_avatar_url %}
          <img src="{{ user.profile.github_avatar_url }}" alt="{{ 
  user.username }}'s avatar" />
      {% else %}
          <img src="/static/img/default-avatar.png" alt="Default avatar" />
      {% endif %}
  </div>
  <div class="info">
      <a data-bs-toggle="collapse" href="#collapseExample" 
  class="collapsed">
          <span>
              {{ user.get_full_name|default:user.username }}
              <b class="caret"></b>
          </span>
      </a>
      <div class="clearfix"></div>
      <div class="collapse" id="collapseExample">
          <ul class="nav">
              <li>
                  <a href="{% url 'profile' %}" 
  class="profile-dropdown-item">
                      <i class="fa fa-user-circle text-primary me-2"></i>
                      <span class="sidebar-normal text-uppercase 
  fw-bold">Profile</span>
                  </a>
              </li>
              <li>
                  <a href="{% url 'logout' %}" 
  class="profile-dropdown-item">
                      <i class="fa fa-sign-out text-danger me-2"></i>
                      <span class="sidebar-normal text-uppercase 
  fw-bold">Logout</span>
                  </a>
              </li>
          </ul>
      </div>
  </div>

  3.4 Create _nav_items.html partial

  <!-- templates/components/_nav_items.html -->
  <li class="{% block nav_dashboard %}{% endblock %}">
      <a href="{% url 'home' %}">
          <i class="nc-icon nc-bank"></i>
          <p>Dashboard</p>
      </a>
  </li>

  <li class="{% block nav_canvas %}{% endblock %}">
      <a href="#canvasExamples" data-bs-toggle="collapse" 
  aria-expanded="true">
          <i class="nc-icon nc-ruler-pencil"></i>
          <p>
              Canvas <b class="caret"></b>
          </p>
      </a>
      <div class="collapse {% block nav_canvas_show %}{% endblock %}" 
  id="canvasExamples">
          <ul class="nav">
              <!-- Canvas nav items -->
              <li class="{% block nav_canvas_dashboard %}{% endblock %}">
                  <a href="{% url 'canvas_dashboard' %}">
                      <span class="sidebar-mini-icon"><i class="fa 
  fa-tachometer"></i></span>
                      <span class="sidebar-normal">Canvas Dashboard</span>
                  </a>
              </li>
              <!-- Additional canvas items... -->
          </ul>
      </div>
  </li>

  <!-- Additional nav items... -->

  3.5 Create _navbar.html partial

  <!-- templates/components/_navbar.html -->
  <nav class="navbar navbar-expand-lg navbar-absolute fixed-top 
  navbar-transparent">
      <div class="container-fluid">
          <div class="navbar-wrapper">
              <div class="navbar-minimize">
                  <button id="minimizeSidebar" class="btn btn-icon 
  btn-round">
                      <i class="nc-icon nc-minimal-right text-center 
  visible-on-sidebar-mini"></i>
                      <i class="nc-icon nc-minimal-left text-center 
  visible-on-sidebar-regular"></i>
                  </button>
              </div>
              <div class="navbar-toggle">
                  <button type="button" class="navbar-toggler">
                      <span class="navbar-toggler-bar bar1"></span>
                      <span class="navbar-toggler-bar bar2"></span>
                      <span class="navbar-toggler-bar bar3"></span>
                  </button>
              </div>
              <a class="navbar-brand" href="javascript:;">{% block
  page_title %}GradeBench{% endblock %}</a>
          </div>

          <button class="navbar-toggler" type="button" 
  data-bs-toggle="collapse" data-bs-target="#navigation" 
  aria-controls="navigation-index" aria-expanded="false" aria-label="Toggle
   navigation">
              <span class="navbar-toggler-bar navbar-kebab"></span>
              <span class="navbar-toggler-bar navbar-kebab"></span>
              <span class="navbar-toggler-bar navbar-kebab"></span>
          </button>

          <div class="collapse navbar-collapse justify-content-end" 
  id="navigation">
              <!-- Search form and user navigation -->
              {% include 'components/_navbar_items.html' %}
          </div>
      </div>
  </nav>

  3.6 Update base.html template

  <!-- templates/base.html -->
  {% load django_bootstrap5 %}
  <!DOCTYPE html>
  <html lang="en">
  <head>
      <meta charset="utf-8" />
      <link rel="apple-touch-icon" sizes="76x76" 
  href="/static/img/apple-icon.png">
      <link rel="icon" type="image/png" href="/static/img/favicon.png">
      <meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1" />
      <meta content="width=device-width, initial-scale=1.0, 
  maximum-scale=1.0, user-scalable=0, shrink-to-fit=no" name="viewport" />
      <title>{% block title %}GradeBench{% endblock %}</title>

      <!-- Fonts and icons -->
      <link 
  href="https://fonts.googleapis.com/css?family=Montserrat:400,700,200" 
  rel="stylesheet" />
      <link href="https://maxcdn.bootstrapcdn.com/font-awesome/latest/css/f
  ont-awesome.min.css" rel="stylesheet">

      <!-- CSS Files -->
      {% bootstrap_css %}
      <link href="/static/css/variables.css" rel="stylesheet" />
      <link href="/static/css/components/index.css" rel="stylesheet" />
      <link href="/static/css/paper-dashboard-bs5.css" rel="stylesheet" />
      <link href="/static/css/paper-dashboard.css" rel="stylesheet" />

      {% block extra_css %}{% endblock %}
      {% block extra_head %}{% endblock %}
  </head>

  <body>
      <div class="wrapper">
          <!-- Sidebar -->
          {% include 'components/_sidebar.html' %}

          <div class="main-panel">
              <!-- Navbar -->
              {% include 'components/_navbar.html' %}

              <div class="content">
                  <!-- Django messages -->
                  {% bootstrap_messages %}

                  <!-- Main content -->
                  {% block content %}{% endblock %}
              </div>

              <!-- Footer -->
              {% include 'components/_footer.html' %}
          </div>
      </div>

      <!-- Core JS Files -->
      {% bootstrap_javascript %}
      <script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
      <script src="https://cdn.jsdelivr.net/npm/perfect-scrollbar@1.5.5/dis
  t/perfect-scrollbar.min.js"></script>

      <!-- Chart JS -->
      <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.u
  md.min.js"></script>

      <!-- Notifications Plugin -->
      <script src="https://cdn.jsdelivr.net/npm/bootstrap-notify@3.1.3/boot
  strap-notify.min.js"></script>

      <!-- Control Center for Paper Dashboard -->
      <script src="/static/js/paper-dashboard.min.js"></script>

      <!-- High Contrast Notifications -->
      <script src="/static/js/high-contrast-notify.js"></script>

      <!-- Timezone detection -->
      <script>
          (function() {
              var tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
              if (tz && document.cookie.indexOf('detected_timezone=') ===
  -1) {
                  document.cookie = "detected_timezone=" + tz + ";path=/";
                  // Optionally, reload the page so the server picks up the
   new cookie
                  location.reload();
              }
          })();
      </script>

      {% block extra_js %}{% endblock %}
  </body>
  </html>

  Phase 4: Reusable Component Templates (Day 5)

  4.1 Create card.html component

  <!-- templates/components/card.html -->
  {% comment %}
  Usage:
  {% include 'components/card.html' with title="Card Title" subtitle="Card
  Subtitle" content=html_content %}

  Or with a content block:
  {% include 'components/card.html' with title="Card Title" subtitle="Card
  Subtitle" %}
      {% block card_content %}
          <!-- Your card content here -->
      {% endblock %}
  {% endinclude %}
  {% endcomment %}

  <div class="card">
      {% if title or subtitle %}
      <div class="card-header">
          {% if title %}<h4 class="card-title">{{ title }}</h4>{% endif %}
          {% if subtitle %}<p class="card-category">{{ subtitle }}</p>{%
  endif %}
      </div>
      {% endif %}
      <div class="card-body">
          {% if content %}{{ content|safe }}{% endif %}
          {% block card_content %}{% endblock %}
      </div>
      {% if footer %}
      <div class="card-footer">
          {{ footer|safe }}
      </div>
      {% endif %}
  </div>

  4.2 Create table.html component

  <!-- templates/components/table.html -->
  {% comment %}
  Usage:
  {% include 'components/table.html' with headers=headers rows=rows %}

  headers = ["Name", "Email", "Status"]
  rows = [["John Doe", "john@example.com", "<span class='badge 
  bg-success'>Active</span>"], ...]
  {% endcomment %}

  <div class="table-responsive">
      <table class="table table-hover">
          <thead class="text-primary">
              <tr>
                  {% for header in headers %}
                  <th>{{ header }}</th>
                  {% endfor %}
              </tr>
          </thead>
          <tbody>
              {% for row in rows %}
              <tr>
                  {% for cell in row %}
                  <td>{{ cell|safe }}</td>
                  {% endfor %}
              </tr>
              {% endfor %}
          </tbody>
      </table>
  </div>

  4.3 Create alert.html component

  <!-- templates/components/alert.html -->
  {% comment %}
  Usage:
  {% include 'components/alert.html' with type="success" title="Success!"
  message="Your changes have been saved." %}
  {% endcomment %}

  <div class="alert alert-{{ type|default:'info' }} alert-dismissible fade 
  show" role="alert">
      {% if title %}<h4 class="alert-heading">{{ title }}</h4>{% endif %}
      <p>{{ message }}</p>
      <button type="button" class="btn-close" data-bs-dismiss="alert" 
  aria-label="Close"></button>
  </div>

  4.4 Create form.html component

  <!-- templates/components/form.html -->
  {% load django_bootstrap5 %}
  {% comment %}
  Usage:
  {% include 'components/form.html' with form=form submit_text="Save" %}
  {% endcomment %}

  <form method="{{ method|default:'post' }}" {% if form_id %}id="{{ form_id
   }}"{% endif %}
        {% if enctype %}enctype="{{ enctype }}"{% endif %} novalidate>
      {% csrf_token %}

      {% if form.non_field_errors %}
      <div class="alert alert-danger">
          {% for error in form.non_field_errors %}
          <p>{{ error }}</p>
          {% endfor %}
      </div>
      {% endif %}

      {% bootstrap_form form %}

      {% if form_buttons %}
      <div class="form-group">
          {{ form_buttons|safe }}
      </div>
      {% else %}
      <div class="text-center">
          {% bootstrap_button submit_text|default:"Submit"
  button_type="submit" button_class="btn-primary btn-fill" %}
          {% if cancel_url %}
          <a href="{{ cancel_url }}" class="btn btn-secondary">Cancel</a>
          {% endif %}
      </div>
      {% endif %}
  </form>

  Phase 5: Form Implementation (Day 6-7)

  5.1 Create base form class

  # core/forms.py
  from django import forms

  class PaperDashboardForm(forms.Form):
      """Base form with Paper Dashboard styling defaults"""

      def __init__(self, *args, **kwargs):
          super().__init__(*args, **kwargs)
          self._setup_fields()

      def _setup_fields(self):
          """Add bootstrap classes to all fields"""
          for field_name, field in self.fields.items():
              # Skip fields that have widget defined with attrs
              if hasattr(field.widget, 'attrs') and field.widget.attrs:
                  # Set default classes if not present
                  if 'class' not in field.widget.attrs:
                      field.widget.attrs['class'] = 'form-control'
              else:
                  # Add bootstrap5 form-control class
                  field.widget.attrs = {
                      'class': 'form-control',
                  }

              # Add placeholder based on label if not set
              if 'placeholder' not in field.widget.attrs and field.label:
                  field.widget.attrs['placeholder'] = field.label


  class PaperDashboardModelForm(forms.ModelForm):
      """Base model form with Paper Dashboard styling defaults"""

      def __init__(self, *args, **kwargs):
          super().__init__(*args, **kwargs)
          self._setup_fields()

      def _setup_fields(self):
          """Add bootstrap classes to all fields"""
          for field_name, field in self.fields.items():
              # Skip fields that have widget defined with attrs
              if hasattr(field.widget, 'attrs') and field.widget.attrs:
                  # Set default classes if not present
                  if 'class' not in field.widget.attrs:
                      field.widget.attrs['class'] = 'form-control'
              else:
                  # Add bootstrap5 form-control class
                  field.widget.attrs = {
                      'class': 'form-control',
                  }

              # Add placeholder based on label if not set
              if 'placeholder' not in field.widget.attrs and field.label:
                  field.widget.attrs['placeholder'] = field.label

  5.2 Create canvas/forms.py

  # lms/canvas/forms.py
  from django import forms
  from core.forms import PaperDashboardForm, PaperDashboardModelForm
  from .models import CanvasIntegration

  class CanvasSetupForm(PaperDashboardModelForm):
      """Form for Canvas API setup"""

      class Meta:
          model = CanvasIntegration
          fields = ['canvas_url', 'api_key']
          widgets = {
              'canvas_url': forms.URLInput(attrs={
                  'placeholder': 'https://canvas.instructure.com'
              }),
              'api_key': forms.PasswordInput(attrs={
                  'placeholder': 'Enter your Canvas API key',
                  'id': 'apiKeyInput'
              })
          }
          help_texts = {
              'canvas_url': 'The URL of your Canvas instance. Default is 
  https://canvas.instructure.com',
              'api_key': 'You can generate an API key in your Canvas 
  account settings under "Approved Integrations".'
          }

  class CourseFilterForm(PaperDashboardForm):
      """Form for filtering courses"""

      search = forms.CharField(
          required=False,
          widget=forms.TextInput(attrs={
              'placeholder': 'Search by course name or code',
              'class': 'form-control'
          })
      )

      term = forms.ChoiceField(
          required=False,
          choices=[('', 'All Terms')],  # Will be populated in __init__
          widget=forms.Select(attrs={
              'class': 'form-select'
          })
      )

      def __init__(self, *args, **kwargs):
          terms = kwargs.pop('terms', [])
          super().__init__(*args, **kwargs)

          # Update term choices with available terms
          term_choices = [('', 'All Terms')]
          for term in terms:
              term_choices.append((term['id'], term['name']))

          self.fields['term'].choices = term_choices

  5.3 Update Canvas Setup View

  # lms/canvas/views/setup.py
  from django.shortcuts import render, redirect
  from django.contrib import messages
  from django.views import View
  from django.contrib.auth.mixins import LoginRequiredMixin

  from ..models import CanvasIntegration
  from ..forms import CanvasSetupForm

  class CanvasSetupView(LoginRequiredMixin, View):
      """View for Canvas API setup"""

      def get(self, request):
          # Get existing integration if it exists
          integration = CanvasIntegration.objects.first()

          # Create form with existing data or empty
          form = CanvasSetupForm(instance=integration)

          context = {
              'form': form,
              'integration': integration
          }

          return render(request, 'canvas/setup.html', context)

      def post(self, request):
          # Get existing integration if it exists
          integration = CanvasIntegration.objects.first()

          # Create form with posted data
          form = CanvasSetupForm(request.POST, instance=integration)

          if form.is_valid():
              # Save the form
              form.save()

              # Add success message
              messages.success(request, 'Canvas API configuration saved 
  successfully!')

              # Redirect to Canvas dashboard
              return redirect('canvas_dashboard')

          # If form is invalid, render the form with errors
          context = {
              'form': form,
              'integration': integration
          }

          return render(request, 'canvas/setup.html', context)

  5.4 Update setup.html template

  <!-- templates/canvas/setup.html -->
  {% extends 'canvas/base.html' %}
  {% load django_bootstrap5 %}

  {% block title %}Canvas Setup | GradeBench{% endblock %}
  {% block page_title %}Canvas API Setup{% endblock %}
  {% block nav_canvas_setup %}active{% endblock %}

  {% block canvas_content %}
  <div class="row">
      <div class="col-md-8 mx-auto">
          {% include 'components/card.html' with title="Canvas API
  Configuration" subtitle="Set up your Canvas API access token" %}
              {% block card_content %}
                  {% include 'components/form.html' with form=form
  submit_text="Save Configuration" %}

                  <div class="alert alert-info mt-4">
                      <h4>How to Generate a Canvas API Key</h4>
                      <ol>
                          <li>Log in to your Canvas account</li>
                          <li>Go to Account &gt; Settings</li>
                          <li>Scroll down to "Approved Integrations"</li>
                          <li>Click "New Access Token"</li>
                          <li>Enter a purpose (e.g., "GradeBench
  Integration")</li>
                          <li>Set an expiration date (or leave blank for no
   expiration)</li>
                          <li>Click "Generate Token"</li>
                          <li>Copy the token and paste it here</li>
                      </ol>
                      <p class="mb-0">Note: The token will only be
  displayed once. If you lose it, you'll need to generate a new one.</p>
                  </div>
              {% endblock %}
          {% endinclude %}
      </div>
  </div>
  {% endblock %}

  {% block canvas_js %}
  <script>
      document.addEventListener('DOMContentLoaded', function() {
          const toggleApiKeyBtn = document.getElementById('toggleApiKey');
          const apiKeyInput = document.getElementById('apiKeyInput');

          if (toggleApiKeyBtn && apiKeyInput) {
              toggleApiKeyBtn.addEventListener('click', function() {
                  // Toggle between password and text
                  if (apiKeyInput.type === 'password') {
                      apiKeyInput.type = 'text';
                      toggleApiKeyBtn.innerHTML = '<i class="fa 
  fa-eye-slash"></i>';
                  } else {
                      apiKeyInput.type = 'password';
                      toggleApiKeyBtn.innerHTML = '<i class="fa 
  fa-eye"></i>';
                  }
              });
          }
      });
  </script>
  {% endblock %}

  Phase 6: List View Implementation (Day 8-9)

  6.1 Update assignments_list.html

  <!-- templates/canvas/assignments_list.html -->
  {% extends 'canvas/base.html' %}
  {% load static %}
  {% load user_timezone %}
  {% load django_bootstrap5 %}

  {% block title %}Canvas Assignments | GradeBench{% endblock %}
  {% block page_title %}Canvas Assignments{% endblock %}
  {% block nav_canvas_assignments %}active{% endblock %}

  {% block canvas_content %}
  <div class="row">
      <div class="col-md-12">
          {% include 'components/card.html' with title="Canvas Assignments"
   subtitle="All assignments across Canvas courses" %}
              {% block card_content %}
                  {% if assignments_by_course %}
                      <div class="d-flex justify-content-end mb-3">
                          <a href="{% url 'canvas_courses_list' %}" 
  class="btn btn-primary btn-sm">
                              <i class="fa fa-plus"></i> Add More Courses
                          </a>
                      </div>

                      {% for course_data in assignments_by_course %}
                      <div class="course-section mb-4">
                          <h4>{{ course_data.course.course_code }}: {{
  course_data.course.name }}</h4>

                          {% with headers=assignment_headers
  rows=course_data.formatted_assignments %}
                              {% include 'components/table.html' with
  headers=headers rows=rows %}
                          {% endwith %}
                      </div>
                      {% if not forloop.last %}<hr class="mb-4">{% endif %}
                      {% endfor %}
                  {% else %}
                      <div class="text-center py-5">
                          <h3>No assignments found</h3>
                          <p>No assignments have been created in any Canvas
   courses yet.</p>
                          <p>
                              <a href="{% url 'canvas_courses_list' %}" 
  class="btn btn-primary btn-fill mt-3">
                                  <i class="fa fa-plus"></i> Add Courses
  from Canvas
                              </a>
                          </p>
                      </div>
                  {% endif %}
              {% endblock %}
          {% endinclude %}
      </div>
  </div>
  {% endblock %}

  6.2 Update Assignment View

  # lms/canvas/views/assignments.py
  from django.shortcuts import render
  from django.contrib.auth.mixins import LoginRequiredMixin
  from django.views import View

  from ..models import CanvasCourse, CanvasAssignment

  class AssignmentsListView(LoginRequiredMixin, View):
      """View for listing all assignments"""

      def get(self, request):
          # Get all courses with assignments
          courses =
  CanvasCourse.objects.prefetch_related('assignments').all()

          # Format data for template
          assignments_by_course = []
          for course in courses:
              assignments = course.assignments.all().order_by('due_at')

              # Skip courses with no assignments
              if not assignments:
                  continue

              # Format assignment data for table rows
              formatted_assignments = []
              for assignment in assignments:
                  # Format the date
                  due_date = assignment.due_at
                  if due_date:
                      due_date = f"{due_date|user_timezone:user|date:'M d, 
  Y'}"
                  else:
                      due_date = "No due date"

                  # Format status badges
                  status = []
                  if assignment.published:
                      status.append('<span class="badge 
  bg-success">Published</span>')
                  else:
                      status.append('<span class="badge 
  bg-warning">Unpublished</span>')

                  if assignment.muted:
                      status.append('<span class="badge 
  bg-info">Muted</span>')

                  # Format actions
                  actions = f'<a href="{{% url "canvas_assignment_detail" 
  course_id={course.canvas_id} assignment_id={assignment.canvas_id} %}}" 
  class="btn btn-info btn-xs"><i class="fa fa-eye"></i> View</a>'

                  # Add to formatted assignments
                  formatted_assignments.append([
                      assignment.name,
                      due_date,
                      assignment.points_possible,
                      ' '.join(status),
                      actions
                  ])

              # Add course data to assignments_by_course
              assignments_by_course.append({
                  'course': course,
                  'assignments': assignments,
                  'formatted_assignments': formatted_assignments
              })

          # Table headers
          assignment_headers = ["Name", "Due Date", "Points", "Status",
  "Actions"]

          context = {
              'assignments_by_course': assignments_by_course,
              'assignment_headers': assignment_headers
          }

          return render(request, 'canvas/assignments_list.html', context)

  Phase 7: Detail View Implementation (Day 10-11)

  7.1 Create assignment_detail.html

  <!-- templates/canvas/assignment_detail.html -->
  {% extends 'canvas/base.html' %}
  {% load static %}
  {% load user_timezone %}
  {% load django_bootstrap5 %}

  {% block title %}{{ assignment.name }} | Canvas Assignments{% endblock %}
  {% block page_title %}Assignment: {{ assignment.name }}{% endblock %}
  {% block nav_canvas_assignments %}active{% endblock %}

  {% block canvas_content %}
  <div class="row">
      <div class="col-md-8">
          {% include 'components/card.html' with title=assignment.name
  subtitle="Assignment Details" %}
              {% block card_content %}
                  <div class="assignment-info">
                      <div class="mb-3">
                          <strong>Course:</strong>
                          <a href="{% url 'canvas_course_detail' 
  course_id=course.canvas_id %}">
                              {{ course.course_code }}: {{ course.name }}
                          </a>
                      </div>

                      <div class="mb-3">
                          <strong>Due Date:</strong>
                          {% if assignment.due_at %}
                              {{
  assignment.due_at|user_timezone:user|date:"F d, Y h:i A" }}
                          {% else %}
                              No due date
                          {% endif %}
                      </div>

                      <div class="mb-3">
                          <strong>Points:</strong> {{
  assignment.points_possible }}
                      </div>

                      <div class="mb-3">
                          <strong>Status:</strong>
                          {% if assignment.published %}
                              <span class="badge 
  bg-success">Published</span>
                          {% else %}
                              <span class="badge 
  bg-warning">Unpublished</span>
                          {% endif %}

                          {% if assignment.muted %}
                              <span class="badge bg-info">Muted</span>
                          {% endif %}
                      </div>

                      <hr>

                      <div class="assignment-description mt-4">
                          <h5>Assignment Description</h5>
                          <div class="content-area bg-light p-3 rounded">
                              {{
  assignment.description|safe|default:"<em>No description provided</em>" }}
                          </div>
                      </div>
                  </div>
              {% endblock %}
          {% endinclude %}
      </div>

      <div class="col-md-4">
          {% include 'components/card.html' with title="Assignment Actions"
   %}
              {% block card_content %}
                  <div class="d-grid gap-2">
                      <a href="{{ assignment.html_url }}" target="_blank" 
  class="btn btn-info btn-fill mb-2">
                          <i class="fa fa-external-link"></i> View in
  Canvas
                      </a>

                      {% if assignment.submission_types and 'online_upload'
   in assignment.submission_types %}
                      <a href="#" class="btn btn-primary btn-fill mb-2">
                          <i class="fa fa-cloud-upload"></i> View
  Submissions
                      </a>
                      {% endif %}

                      <a href="{% url 'canvas_assignments_list' %}" 
  class="btn btn-secondary">
                          <i class="fa fa-arrow-left"></i> Back to
  Assignments
                      </a>
                  </div>
              {% endblock %}
          {% endinclude %}

          {% if assignment.submission_types %}
          {% include 'components/card.html' with title="Submission Types"
  %}
              {% block card_content %}
                  <ul class="list-group list-group-flush">
                      {% for sub_type in assignment.submission_types %}
                      <li class="list-group-item">
                          {% if sub_type == 'online_upload' %}
                              <i class="fa fa-upload text-primary 
  me-2"></i> File Upload
                          {% elif sub_type == 'online_text_entry' %}
                              <i class="fa fa-file-text-o text-success 
  me-2"></i> Text Entry
                          {% elif sub_type == 'online_url' %}
                              <i class="fa fa-link text-info me-2"></i>
  Website URL
                          {% elif sub_type == 'media_recording' %}
                              <i class="fa fa-microphone text-warning 
  me-2"></i> Media Recording
                          {% elif sub_type == 'discussion_topic' %}
                              <i class="fa fa-comments text-danger 
  me-2"></i> Discussion Topic
                          {% else %}
                              <i class="fa fa-check-circle me-2"></i> {{
  sub_type|title|replace:"_":" " }}
                          {% endif %}
                      </li>
                      {% empty %}
                      <li class="list-group-item">No submission types
  specified</li>
                      {% endfor %}
                  </ul>
              {% endblock %}
          {% endinclude %}
          {% endif %}
      </div>
  </div>
  {% endblock %}

  Phase 8: Style Guide Page (Day 12)

  8.1 Create styleguide.html

  <!-- templates/styleguide.html -->
  {% extends 'base.html' %}
  {% load django_bootstrap5 %}
  {% load static %}

  {% block title %}Style Guide | GradeBench{% endblock %}
  {% block page_title %}Style Guide{% endblock %}
  {% block nav_styleguide %}active{% endblock %}
  {% block nav_admin_show %}show{% endblock %}

  {% block content %}
  <div class="row">
      <div class="col-md-12">
          {% include 'components/card.html' with title="Style Guide"
  subtitle="Bootstrap 5 with Paper Dashboard" %}
              {% block card_content %}
                  <h4>Typography</h4>
                  <div class="row">
                      <div class="col-md-6">
                          <h1>Heading 1</h1>
                          <h2>Heading 2</h2>
                          <h3>Heading 3</h3>
                          <h4>Heading 4</h4>
                          <h5>Heading 5</h5>
                          <h6>Heading 6</h6>
                      </div>
                      <div class="col-md-6">
                          <p class="lead">Lead paragraph</p>
                          <p>Regular paragraph text</p>
                          <p><small>Small text</small></p>
                          <p><strong>Bold text</strong></p>
                          <p><em>Italic text</em></p>
                          <p><code>Code text</code></p>
                      </div>
                  </div>

                  <hr>

                  <h4>Colors</h4>
                  <div class="row">
                      <div class="col-md-12">
                          <div class="d-flex flex-wrap gap-2 mb-3">
                              <div class="p-3 bg-primary 
  text-white">Primary</div>
                              <div class="p-3 bg-secondary 
  text-white">Secondary</div>
                              <div class="p-3 bg-success 
  text-white">Success</div>
                              <div class="p-3 bg-danger 
  text-white">Danger</div>
                              <div class="p-3 bg-warning 
  text-dark">Warning</div>
                              <div class="p-3 bg-info 
  text-white">Info</div>
                              <div class="p-3 bg-light 
  text-dark">Light</div>
                              <div class="p-3 bg-dark 
  text-white">Dark</div>
                          </div>
                      </div>
                  </div>

                  <hr>

                  <h4>Buttons</h4>
                  <div class="row">
                      <div class="col-md-6">
                          <h5>Standard Buttons</h5>
                          <div class="d-flex flex-wrap gap-2 mb-3">
                              <button class="btn 
  btn-primary">Primary</button>
                              <button class="btn 
  btn-secondary">Secondary</button>
                              <button class="btn 
  btn-success">Success</button>
                              <button class="btn 
  btn-danger">Danger</button>
                              <button class="btn 
  btn-warning">Warning</button>
                              <button class="btn btn-info">Info</button>
                          </div>
                      </div>
                      <div class="col-md-6">
                          <h5>Fill Buttons (Paper Dashboard Style)</h5>
                          <div class="d-flex flex-wrap gap-2 mb-3">
                              <button class="btn btn-primary 
  btn-fill">Primary Fill</button>
                              <button class="btn btn-success 
  btn-fill">Success Fill</button>
                              <button class="btn btn-danger 
  btn-fill">Danger Fill</button>
                              <button class="btn btn-warning 
  btn-fill">Warning Fill</button>
                              <button class="btn btn-info btn-fill">Info
  Fill</button>
                          </div>
                      </div>
                  </div>

                  <hr>

                  <h4>Forms with django-bootstrap5</h4>
                  <div class="row">
                      <div class="col-md-6">
                          <form method="post" action="#" class="mb-4">
                              {% csrf_token %}
                              {% bootstrap_field form.username %}
                              {% bootstrap_field form.email %}
                              {% bootstrap_field form.password %}
                              {% bootstrap_field form.remember %}
                              {% bootstrap_button "Submit"
  button_type="submit" button_class="btn-primary" %}
                          </form>
                      </div>
                      <div class="col-md-6">
                          <h5>Usage example:</h5>
                          <pre class="bg-light p-3 rounded">&lt;form
  method="post"&gt;
      {% templatetag openblock %} csrf_token {% templatetag closeblock %}
      {% templatetag openblock %} bootstrap_field form.username {%
  templatetag closeblock %}
      {% templatetag openblock %} bootstrap_field form.email {% templatetag
   closeblock %}
      {% templatetag openblock %} bootstrap_button "Submit"
  button_type="submit" {% templatetag closeblock %}
  &lt;/form&gt;</pre>
                      </div>
                  </div>

                  <hr>

                  <h4>Cards</h4>
                  <div class="row">
                      <div class="col-md-6">
                          <div class="card">
                              <div class="card-header">
                                  <h4 class="card-title">Card Title</h4>
                                  <p class="card-category">Card
  Subtitle</p>
                              </div>
                              <div class="card-body">
                                  This is a standard card with header and
  body.
                              </div>
                              <div class="card-footer">
                                  Card footer
                              </div>
                          </div>
                      </div>
                      <div class="col-md-6">
                          <h5>Usage example:</h5>
                          <pre class="bg-light p-3 rounded">{% templatetag
  openblock %} include 'components/card.html' with
      title="Card Title"
      subtitle="Card Subtitle"
      content="This is the card content."
      footer="Card footer"
  {% templatetag closeblock %}</pre>
                      </div>
                  </div>

                  <hr>

                  <h4>Tables</h4>
                  <div class="row">
                      <div class="col-md-12">
                          {% with headers=table_headers rows=table_rows %}
                              {% include 'components/table.html' with
  headers=headers rows=rows %}
                          {% endwith %}
                      </div>
                  </div>

                  <hr>

                  <h4>Alerts</h4>
                  <div class="row">
                      <div class="col-md-12">
                          {% include 'components/alert.html' with
  type="success" title="Success!" message="This is a success alert." %}
                          {% include 'components/alert.html' with
  type="danger" title="Error!" message="This is a danger alert." %}
                          {% include 'components/alert.html' with
  type="warning" message="This is a warning alert without title." %}
                          {% include 'components/alert.html' with
  type="info" message="This is an info alert without title." %}
                      </div>
                  </div>
              {% endblock %}
          {% endinclude %}
      </div>
  </div>
  {% endblock %}

  {% block extra_js %}
  <script>
      // Create a demo form for the styleguide
      document.addEventListener('DOMContentLoaded', function() {
          // This script is just for demonstration
          console.log('Styleguide loaded');
      });
  </script>
  {% endblock %}

  8.2 Update styleguide view

  # core/views/auth.py
  # Add to existing file:

  from django import forms

  class DemoForm(forms.Form):
      """Demo form for the styleguide"""
      username = forms.CharField(
          label="Username",
          max_length=100,
          required=True,
          widget=forms.TextInput(attrs={
              'placeholder': 'Enter username',
              'class': 'form-control'
          })
      )
      email = forms.EmailField(
          label="Email",
          required=True,
          widget=forms.EmailInput(attrs={
              'placeholder': 'Enter email',
              'class': 'form-control'
          })
      )
      password = forms.CharField(
          label="Password",
          required=True,
          widget=forms.PasswordInput(attrs={
              'placeholder': 'Enter password',
              'class': 'form-control'
          })
      )
      remember = forms.BooleanField(
          label="Remember me",
          required=False,
          widget=forms.CheckboxInput()
      )

  class StyleguideView(LoginRequiredMixin, View):
      """View for the styleguide"""

      def get(self, request):
          # Create a demo form for styleguide
          form = DemoForm()

          # Table demo data
          table_headers = ["Name", "Email", "Role", "Status", "Actions"]
          table_rows = [
              ["John Doe", "john@example.com", "Student", '<span 
  class="badge bg-success">Active</span>', '<button class="btn btn-info 
  btn-sm"><i class="fa fa-eye"></i></button>'],
              ["Jane Smith", "jane@example.com", "Teacher", '<span 
  class="badge bg-warning">Pending</span>', '<button class="btn btn-info 
  btn-sm"><i class="fa fa-eye"></i></button>'],
              ["Bob Johnson", "bob@example.com", "Admin", '<span 
  class="badge bg-danger">Inactive</span>', '<button class="btn btn-info 
  btn-sm"><i class="fa fa-eye"></i></button>'],
          ]

          context = {
              'form': form,
              'table_headers': table_headers,
              'table_rows': table_rows
          }

          return render(request, 'styleguide.html', context)

  Phase 9: Final Polishing & Testing (Day 13-14)

  9.1 Create a utility Django template filter library

  # core/templatetags/bootstrap_filters.py
  from django import template
  from django.template.defaultfilters import stringfilter
  import re

  register = template.Library()

  @register.filter
  @stringfilter
  def bootstrap_alert_class(value):
      """Convert Django message level to Bootstrap 5 alert class"""
      if value == 'error':
          return 'danger'
      return value

  @register.filter
  @stringfilter
  def replace(value, arg):
      """Replace all instances of the first argument with the second in the
   value"""
      args = arg.split('|')
      if len(args) != 2:
          return value
      return value.replace(args[0], args[1])

  @register.filter
  @stringfilter
  def addclass(value, css_class):
      """Add a CSS class to an HTML tag"""
      match = re.search(r'class=["\']([^"\']*)["\']', value)
      if match:
          # Class attribute already exists
          current_classes = match.group(1)
          if css_class not in current_classes.split():
              # Add the new class if it's not already present
              new_classes = f"{current_classes} {css_class}"
              return re.sub(r'class=["\']([^"\']*)["\']',
  f'class="{new_classes}"', value)
          return value
      else:
          # No class attribute yet, add it
          return re.sub(r'(<[a-zA-Z0-9]+)', f'\\1 class="{css_class}"',
  value)

  9.2 Run comprehensive testing

  1. Test all forms with django-bootstrap5
  2. Verify responsive behavior on different screen sizes
  3. Test all components in the styleguide
  4. Check for any styling inconsistencies

  9.3 Create django-bootstrap5 cheat sheet for developers

  Create a markdown file django_bootstrap5_cheatsheet.md with common
  patterns and examples:

  # django-bootstrap5 Cheat Sheet for GradeBench

  ## Basic Form Rendering

  ```django
  {% load django_bootstrap5 %}

  {# Render entire form #}
  {% bootstrap_form form %}

  {# Render single field #}
  {% bootstrap_field form.username %}

  {# Render field with custom layout #}
  {% bootstrap_field form.username layout="horizontal" %}

  {# Render field with custom size #}
  {% bootstrap_field form.username size="sm" %}

  {# Render field with placeholder #}
  {% bootstrap_field form.username placeholder="Enter username" %}

  Buttons

  {# Primary button #}
  {% bootstrap_button "Submit" button_type="submit"
  button_class="btn-primary" %}

  {# Paper Dashboard style button #}
  {% bootstrap_button "Save" button_type="submit" button_class="btn-success
   btn-fill" %}

  {# Button with icon #}
  {% bootstrap_button "<i class='fa fa-save'></i> Save"
  button_type="submit" button_class="btn-primary" %}

  Messages

  {# In your view #}
  messages.success(request, "Item saved successfully!")
  messages.error(request, "An error occurred.")

  {# In your template #}
  {% bootstrap_messages %}

  Custom Components

  {# Card component #}
  {% include 'components/card.html' with title="Card Title" subtitle="Card
  Subtitle" content="Card content" %}

  {# Table component #}
  {% include 'components/table.html' with headers=headers rows=rows %}

  {# Alert component #}
  {% include 'components/alert.html' with type="success" title="Success!"
  message="Operation completed successfully." %}

  {# Form component #}
  {% include 'components/form.html' with form=form submit_text="Save" %}

  Form Layout Examples

  {# Horizontal form #}
  <form method="post">
      {% csrf_token %}
      {% bootstrap_form form layout="horizontal" %}
      {% bootstrap_button "Submit" button_type="submit"
  button_class="btn-primary" %}
  </form>

  {# Inline form #}
  <form method="post" class="row row-cols-lg-auto g-3 align-items-center">
      {% csrf_token %}
      <div class="col-12">
          {% bootstrap_field form.search show_label=False %}
      </div>
      <div class="col-12">
          {% bootstrap_field form.filter show_label=False %}
      </div>
      <div class="col-12">
          {% bootstrap_button "Search" button_type="submit"
  button_class="btn-primary" %}
      </div>
  </form>

  ## Timeline Summary

  - **Days 1-2:** Setup django-bootstrap5 and create theme bridge
  - **Days 3-5:** Update base templates and create reusable components
  - **Days 6-7:** Implement form system with django-bootstrap5
  - **Days 8-9:** Update list views with new components
  - **Days 10-11:** Update detail views and finalize templates
  - **Day 12:** Create comprehensive style guide
  - **Days 13-14:** Final testing, polishing, and documentation

  