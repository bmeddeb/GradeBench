from django.views.generic import ListView

from .models import Process


class ProcessListView(ListView):
    """View to list all processes."""
    model = Process
    template_name = 'processes/process_list.html'
    context_object_name = 'processes'
    paginate_by = 10
