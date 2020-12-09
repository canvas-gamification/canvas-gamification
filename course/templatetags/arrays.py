from django import template

register = template.Library()


@register.filter
def return_item(arr, i):
    try:
        return arr[i]
    except Exception:
        return None


@register.simple_tag
def return_last_item(arr):
    try:
        return arr[len(arr) - 1]
    except Exception:
        return None
