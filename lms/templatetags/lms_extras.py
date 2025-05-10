from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Gets an item from a dictionary by key. Returns None if the key doesn't exist.
    
    Usage:
    {{ my_dict|get_item:my_key }}
    """
    return dictionary.get(key)