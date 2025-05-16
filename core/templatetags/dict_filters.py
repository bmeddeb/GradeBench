"""
Template filters for dictionaries
"""

import json as json_lib
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Gets an item from a dictionary for templates
    Example usage: {{ mydict|get_item:item_key }}
    """
    if not dictionary:
        return None
    
    if not key:
        return None
    
    return dictionary.get(str(key))

@register.filter
def json(value):
    """
    Convert a Python object to JSON string for JavaScript use
    Example usage: {{ my_dict|json }}
    """
    return json_lib.dumps(value)

@register.simple_tag
def get_taiga_config_value(taiga_config, group_id, field_name):
    """
    Get a value from nested taiga configuration dictionary.
    Example usage: {% get_taiga_config_value taiga_config group.id "instance" as instance_value %}
    """
    if not taiga_config or not str(group_id) in taiga_config:
        return ""
        
    group_config = taiga_config.get(str(group_id), {})
    if isinstance(group_config, dict):
        return group_config.get(field_name, "")
    return ""


@register.filter
def split(value, delimiter):
    """
    Split a string into a list using the delimiter
    Example usage: {{ "a,b,c"|split:"," }}
    """
    return value.split(delimiter)
    
@register.filter
def get_initial_value(form, field_name):
    """Get the initial value for a form field"""
    if hasattr(form, 'initial') and field_name in form.initial:
        return form.initial[field_name]
    return None