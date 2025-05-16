from django.urls import path
from . import views

app_name = 'processes'

urlpatterns = [
    path('', views.ProcessListView.as_view(), name='process_list'),
]
