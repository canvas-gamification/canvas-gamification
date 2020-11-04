from django import template
from canvas.utils.utils import get_total_event_grade

register = template.Library()


@register.filter
def total_event_grade(event, user):
    return get_total_event_grade(event, user)
