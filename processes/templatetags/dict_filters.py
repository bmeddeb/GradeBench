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
def get_item(dictionary, key):
    """
    Get item from dictionary.

    Usage: {{ my_dict|get_item:key_variable }}
    """
    return dictionary.get(key)


@register.filter
def get_initial_value(form, field_name):
    """
    Gets the initial value of a field from a form.

    Usage: {{ form|get_initial_value:'field_name' }}
    """
    try:
        # Try to get from initial
        if form.initial and field_name in form.initial:
            return form.initial[field_name]

        # Try to get from fields.initial
        if field_name in form.fields:
            return form.fields[field_name].initial

        return ''
    except:
        return ''


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
