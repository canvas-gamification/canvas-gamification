from django import template
from canvas.models import Event
register = template.Library()


@register.simple_tag
def row_class(submission, event):
    if isinstance(event, Event) and event.is_exam:
        return ""
    else:
        return "table-" + submission.status_color
