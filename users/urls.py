from django.urls import path
from . import views

urlpatterns = [
    path('profile/', views.profile_view, name='user_profile'),
    path('teams/', views.teams_view, name='teams'),
    path('teams/<int:team_id>/', views.team_detail_view, name='team_detail'),
    path('teams/create/', views.create_team_view, name='create_team'),
    path('teams/<int:team_id>/add-student/', views.add_student_to_team_view, name='add_student_to_team'),
    path('teams/<int:team_id>/add-repository/', views.add_repository_view, name='add_repository'),
    path('manage-roles/', views.manage_user_roles_view, name='manage_user_roles'),
]
