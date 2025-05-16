from django.shortcuts import render, redirect
from django.views.generic import ListView
from django.contrib import messages
from django.urls import reverse
from formtools.wizard.views import SessionWizardView
from django.db import transaction

from .models import Process
from .forms import (
    TeamWizardStep1Form,
    TeamWizardStep2Form,
    TeamWizardStep3Form,
    TeamWizardStep4Form,
    TeamWizardStep5Form,
    TeamWizardStep6Form,
)

# Create your views here.


class ProcessListView(ListView):
    """View to list all processes."""
    model = Process
    template_name = 'processes/process_list.html'
    context_object_name = 'processes'
    paginate_by = 10


class TeamWizard(SessionWizardView):
    """
    Multi-step wizard for creating Teams from Canvas Groups.

    Steps:
    1. Course Selection (with GitHub and Taiga toggles)
    2. Group Set Selection
    3. Group Selection
    4. GitHub Configuration (conditional)
    5. Taiga Configuration (conditional)
    6. Confirmation & Persistence
    """
    form_list = [
        ('course_selection', TeamWizardStep1Form),
        ('group_set_selection', TeamWizardStep2Form),
        ('group_selection', TeamWizardStep3Form),
        ('github_config', TeamWizardStep4Form),
        ('taiga_config', TeamWizardStep5Form),
        ('confirmation', TeamWizardStep6Form),
    ]
    template_name = 'processes/team_wizard.html'

    def get_form_kwargs(self, step=None):
        """Pass dynamic parameters to forms based on previous steps."""
        kwargs = super().get_form_kwargs(step)

        if step == 'group_set_selection':
            # Pass course_id from step 1 to step 2
            step1_data = self.get_cleaned_data_for_step('course_selection')
            if step1_data:
                kwargs['course_id'] = step1_data.get(
                    'course').id if step1_data.get('course') else None
                print(
                    f"Passing course_id={kwargs['course_id']} to group_set_selection form")

        elif step == 'group_selection':
            # Pass selected group categories from step 2 to step 3
            step2_data = self.get_cleaned_data_for_step('group_set_selection')
            if step2_data:
                categories = step2_data.get('group_categories', [])
                kwargs['category_ids'] = [cat.id for cat in categories]
                print(
                    f"Passing category_ids={kwargs['category_ids']} to group_selection form")
            else:
                print("No data from step 2 - group_set_selection")

        return kwargs

    def get_template_names(self):
        """Return specific template for steps if they exist."""
        return [
            f'processes/team_wizard_{self.steps.current}.html',
            self.template_name,
        ]

    def get_context_data(self, form, **kwargs):
        """Add extra context for each step."""
        context = super().get_context_data(form, **kwargs)

        # Add step-specific context
        if self.steps.current == 'confirmation':
            # Add summary of all selections for confirmation page
            all_data = {}
            for step_name in self.steps.all:
                step_data = self.get_cleaned_data_for_step(step_name)
                if step_data:
                    all_data[step_name] = step_data
            context['all_data'] = all_data

        # Pass groups_by_category from Step 3 form
        elif self.steps.current == 'group_selection' and hasattr(form, 'groups_by_category'):
            context['groups_by_category'] = form.groups_by_category

        # Add step titles for display in the template
        context['step_titles'] = {
            'course_selection': 'Course Selection',
            'group_set_selection': 'Group Set Selection',
            'group_selection': 'Group Selection',
            'github_config': 'GitHub Config',
            'taiga_config': 'Taiga Config',
            'confirmation': 'Confirmation',
        }

        # Add more compact step titles for the progress indicators
        context['step_short_titles'] = {
            'course_selection': 'Course',
            'group_set_selection': 'Group Sets',
            'group_selection': 'Groups',
            'github_config': 'GitHub',
            'taiga_config': 'Taiga',
            'confirmation': 'Confirm',
        }

        return context

    def condition_github_config(self):
        """Only show GitHub config step if use_github was checked in step 1."""
        step1_data = self.get_cleaned_data_for_step('course_selection')
        return step1_data and step1_data.get('use_github', False)

    def condition_taiga_config(self):
        """Only show Taiga config step if use_taiga was checked in step 1."""
        step1_data = self.get_cleaned_data_for_step('course_selection')
        return step1_data and step1_data.get('use_taiga', False)

    def done(self, form_list, **kwargs):
        """Process the wizard data and create Team and Student records."""
        # Convert form_list to a dictionary for easier access
        form_dict = kwargs.get('form_dict', {})
        all_data = {}
        for form_key, form in form_dict.items():
            all_data[form_key] = form.cleaned_data

        # This is a placeholder for the actual implementation
        # In a real scenario, you would process the data and create Team objects

        # For demonstration purposes, show a success message
        messages.success(self.request, 'Teams created successfully!')

        # Redirect to a success page or list view
        return redirect('processes:process_list')

    def process_step(self, form):
        """Process the form for the current step."""
        # Log form data for debugging
        step_name = self.steps.current
        print(f"Processing {step_name} form")
        print(f"Form data: {form.data}")
        print(f"Form cleaned_data: {form.cleaned_data}")
        return super().process_step(form)
