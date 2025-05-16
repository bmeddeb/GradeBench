from django.contrib import admin
from .models import Process


@admin.register(Process)
class ProcessAdmin(admin.ModelAdmin):
    """Admin interface for Process model."""
    list_display = ('name', 'created_at', 'updated_at')
    search_fields = ('name', 'description')
    list_filter = ('created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')
