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
    # Dynamic form - fields will be created in __init__

    def __init__(self, *args, **kwargs):
        # Get selected groups and course from previous steps
        selected_group_ids = kwargs.pop('selected_group_ids', [])
        course = kwargs.pop('course', None)
        super().__init__(*args, **kwargs)

        if not selected_group_ids or not course:
            return

        from lms.canvas.models import CanvasGroup

        # Get the course code for prefixing repo names
        course_code = course.course_code or course.name.split(':')[0].strip()
        # Sanitize course code - replace spaces with hyphens
        course_code = self._sanitize_name(course_code)

        # Create fields for each selected group
        for group_id in selected_group_ids:
            try:
                group = CanvasGroup.objects.get(id=group_id)
                # Sanitize group name: replace spaces with hyphens, remove invalid chars
                sanitized_name = self._sanitize_name(group.name)

                # Default repo name is course_code-sanitized_group_name
                default_name = f"{course_code}-{sanitized_name}".lower()

                # Create a field for the repo name - directly editable
                self.fields[f'repo_name_{group_id}'] = forms.CharField(
                    label=f"Repository name for {group.name}",
                    initial=default_name,
                    max_length=100,
                    widget=forms.TextInput(attrs={
                        'class': 'form-control repo-name-input',
                        'data-toggle': 'tooltip',
                        'title': 'Repository name: spaces → hyphens, only letters, numbers, hyphens, and underscores allowed',
                        'data-group-id': group_id,
                        'data-default-name': default_name,
                        'autocomplete': 'off'
                    }),
                    help_text=f"Default: {default_name}"
                )
            except CanvasGroup.DoesNotExist:
                continue

    def _sanitize_name(self, name):
        """
        Sanitize a name for use in a GitHub repository:
        - Replace spaces with hyphens
        - Remove characters that aren't alphanumeric, hyphens, or underscores
        """
        import re
        # Replace spaces with hyphens
        name = name.replace(' ', '-')
        # Remove invalid characters
        name = re.sub(r'[^\w\-]', '', name)
        return name

    def clean(self):
        """
        Validate that all repository names conform to GitHub requirements:
        - Only alphanumeric characters, hyphens, and underscores
        - Maximum length of 100 characters
        """
        cleaned_data = super().clean()

        import re
        pattern = r'^[a-zA-Z0-9\-_]+$'

        for field_name, value in cleaned_data.items():
            if field_name.startswith('repo_name_'):
                if not re.match(pattern, value):
                    self.add_error(
                        field_name,
                        "Repository name can only contain letters, numbers, hyphens, and underscores."
                    )

        return cleaned_data


class TeamWizardStep5Form(forms.Form):
    """Step 5: Taiga Configuration Form"""
    # Dynamic form - fields will be created in __init__

    def __init__(self, *args, **kwargs):
        # Get selected groups and course from previous steps
        selected_group_ids = kwargs.pop('selected_group_ids', [])
        course = kwargs.pop('course', None)
        super().__init__(*args, **kwargs)

        if not selected_group_ids or not course:
            return

        from lms.canvas.models import CanvasGroup

        # Get the course code for prefixing project names
        course_code = course.course_code or course.name.split(':')[0].strip()
        # Sanitize course code - replace spaces with hyphens
        course_code = self._sanitize_name(course_code)

        # Create fields for each selected group
        for group_id in selected_group_ids:
            try:
                group = CanvasGroup.objects.get(id=group_id)
                # Sanitize group name: replace spaces with hyphens, remove invalid chars
                sanitized_name = self._sanitize_name(group.name)

                # Default project name is course_code-sanitized_group_name
                default_name = f"{course_code}-{sanitized_name}".lower()

                # Create a field for the project name - directly editable
                self.fields[f'project_name_{group_id}'] = forms.CharField(
                    label=f"Taiga project name for {group.name}",
                    initial=default_name,
                    max_length=100,
                    widget=forms.TextInput(attrs={
                        'class': 'form-control project-name-input',
                        'data-toggle': 'tooltip',
                        'title': 'Project name: spaces → hyphens, only letters, numbers, hyphens, and underscores allowed',
                        'data-group-id': group_id,
                        'data-default-name': default_name,
                        'autocomplete': 'off'
                    }),
                    help_text=f"Default: {default_name}"
                )
            except CanvasGroup.DoesNotExist:
                continue

    def _sanitize_name(self, name):
        """
        Sanitize a name for use in a Taiga project:
        - Replace spaces with hyphens
        - Remove characters that aren't alphanumeric, hyphens, or underscores
        """
        import re
        # Replace spaces with hyphens
        name = name.replace(' ', '-')
        # Remove invalid characters
        name = re.sub(r'[^\w\-]', '', name)
        return name

    def clean(self):
        """
        Validate that all project names conform to Taiga requirements:
        - Only alphanumeric characters, hyphens, and underscores
        - Maximum length of 100 characters
        """
        cleaned_data = super().clean()

        import re
        pattern = r'^[a-zA-Z0-9\-_]+$'

        for field_name, value in cleaned_data.items():
            if field_name.startswith('project_name_'):
                if not re.match(pattern, value):
                    self.add_error(
                        field_name,
                        "Project name can only contain letters, numbers, hyphens, and underscores."
                    )

        return cleaned_data


class TeamWizardStep6Form(forms.Form):
    """Step 6: Confirmation Form"""
    confirm = forms.BooleanField(
        required=True,
        label=_('I confirm all selections and configurations are correct'),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
