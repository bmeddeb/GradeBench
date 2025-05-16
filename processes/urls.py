from django.urls import path
from . import views

app_name = 'processes'

urlpatterns = [
    path('', views.ProcessListView.as_view(), name='process_list'),
    path('teams/', views.TeamWizard.as_view(
        condition_dict={
            'github_config': views.TeamWizard.condition_github_config,
            'taiga_config': views.TeamWizard.condition_taiga_config,
        }
    ), name='team_wizard'),
]
