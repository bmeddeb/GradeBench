from django import forms
from django.utils.translation import gettext_lazy as _
from lms.canvas.models import CanvasCourse, CanvasGroupCategory, CanvasGroup
from django_select2.forms import Select2Widget, Select2MultipleWidget


class TeamWizardStep1Form(forms.Form):
    """Step 1: Course Selection Form"""
    course = forms.ModelChoiceField(
        queryset=CanvasCourse.objects.all(),
        label=_('Select Canvas Course'),
        widget=Select2Widget(attrs={
            'class': 'form-select select2',
            'data-placeholder': 'Select a Canvas course',
            'data-theme': 'bootstrap-5'
        })
    )
    use_github = forms.BooleanField(
        required=False,
        label=_('GitHub'),
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'role': 'switch'
        })
    )
    use_taiga = forms.BooleanField(
        required=False,
        label=_('Taiga'),
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'role': 'switch'
        })
    )


class TeamWizardStep2Form(forms.Form):
    """Step 2: Group Set Selection Form"""
    group_categories = forms.ModelMultipleChoiceField(
        queryset=CanvasGroupCategory.objects.none(),  # Will be set dynamically
        label=_('Select Group Categories'),
        # Use MultipleHiddenInput since we have our own UI
        widget=forms.MultipleHiddenInput(),
        required=True
    )

    def __init__(self, *args, **kwargs):
        course_id = kwargs.pop('course_id', None)
        super().__init__(*args, **kwargs)

        if course_id:
            self.fields['group_categories'].queryset = CanvasGroupCategory.objects.filter(
                course_id=course_id
            )


class TeamWizardStep3Form(forms.Form):
    """Step 3: Group Selection Form"""
    selected_groups = forms.MultipleChoiceField(
        choices=[],  # Will be set dynamically
        label=_('Select Groups to Create Teams'),
        widget=forms.MultipleHiddenInput(),
        required=True
    )

    def __init__(self, *args, **kwargs):
        category_ids = kwargs.pop('category_ids', [])
        super().__init__(*args, **kwargs)

        from lms.canvas.models import CanvasGroup

        # Get all groups belonging to the selected categories
        groups = CanvasGroup.objects.filter(
            category__id__in=category_ids).order_by('name')

        # Set choices for the form field
        self.fields['selected_groups'].choices = [
            (str(group.id), group.name) for group in groups
        ]

        # Store groups by category for the template
        self.groups_by_category = {}
        for group in groups:
            category_name = group.category.name if group.category else 'Uncategorized'
            if category_name not in self.groups_by_category:
                self.groups_by_category[category_name] = []
            self.groups_by_category[category_name].append(group)


class TeamWizardStep4Form(forms.Form):
    """Step 4: GitHub Configuration Form"""
    # This is a placeholder - in the actual implementation,
    # you would dynamically create fields based on the selected groups
    github_repo_names = forms.CharField(
        label=_('GitHub Repository Name Template'),
        help_text=_('Will be prefixed with course code'),
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )


class TeamWizardStep5Form(forms.Form):
    """Step 5: Taiga Configuration Form"""
    # This is a placeholder - in the actual implementation,
    # you would dynamically create fields based on the selected groups
    taiga_project_names = forms.CharField(
        label=_('Taiga Project Name Template'),
        help_text=_('Will be prefixed with course code'),
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )


class TeamWizardStep6Form(forms.Form):
    """Step 6: Confirmation Form"""
    confirm = forms.BooleanField(
        required=True,
        label=_('I confirm all selections and configurations are correct'),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
