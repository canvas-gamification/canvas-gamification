from django import template

register = template.Library()


@register.filter
def return_item(arr, i):
    try:
        return arr[i]
    except Exception:
        return None
