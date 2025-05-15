"""
Form classes for Canvas app
"""
from django import forms
from .models import CanvasIntegration


class CanvasSetupForm(forms.ModelForm):
    """Form for configuring Canvas API settings"""
    
    class Meta:
        model = CanvasIntegration
        fields = ["canvas_url", "api_key"]
        widgets = {
            "canvas_url": forms.URLInput(
                attrs={
                    "placeholder": "https://canvas.instructure.com",
                    "class": "form-control",
                }
            ),
            "api_key": forms.PasswordInput(
                attrs={
                    "placeholder": "Enter your Canvas API key",
                    "class": "form-control",
                    "id": "apiKeyInput",
                }
            ),
        }
        help_texts = {
            "canvas_url": "The URL of your Canvas instance. Default is https://canvas.instructure.com",
            "api_key": "You can generate an API key in your Canvas account settings under \"Approved Integrations\"."
        }


class CourseFilterForm(forms.Form):
    """Form for filtering Canvas courses"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={"placeholder": "Search courses", "class": "form-control"}
        ),
    )
    
    status = forms.ChoiceField(
        required=False,
        choices=[
            ("", "All Statuses"),
            ("active", "Active"),
            ("completed", "Completed"),
            ("upcoming", "Upcoming"),
        ],
        widget=forms.Select(attrs={"class": "form-select"}),
    )