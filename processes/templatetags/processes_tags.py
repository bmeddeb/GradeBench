from django import template

register = template.Library()


@register.filter
def get(dictionary, key):
    """
    Get value from dictionary by key.

    Usage: {{ my_dict|get:key_variable }}
    """
    return dictionary.get(key)


@register.filter
def startswith(text, starts):
    """
    Returns True if text starts with the given string.

    Usage: {% if field.name|startswith:'repo_name_' %}
    """
    if isinstance(text, str):
        return text.startswith(starts)
    return False


@register.filter
def add(text, value):
    """
    Adds (concatenates) two values.

    Usage: {{ 'override_'|add:group_id }}
    """
    return str(text) + str(value)


@register.filter
def get_field(form, field_name):
    """
    Gets a field from a form by name.

    Usage: {{ form|get_field:'field_name' }}
    """
    try:
        return form[field_name]
    except:
        return None


@register.filter
def get_id(field):
    """
    Gets the ID of a form field.

    Usage: {{ field|get_id }}
    """
    try:
        return field.id_for_label
    except:
        return ''
