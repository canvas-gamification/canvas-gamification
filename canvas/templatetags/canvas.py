from django import template
from course.models.models import Event

register = template.Library()


@register.simple_tag
def is_registered_in_course(course, user):
    return course.is_registered(user)


@register.simple_tag
def is_allowed_to_open_course(course, user):
    return course.has_view_permission(user)


@register.simple_tag
def is_allowed_to_open_event(event, user):
    return event.has_view_permission(user) or event.can_view_results(user)


@register.simple_tag
def is_allowed_to_edit_event(event, user):
    return event.has_edit_permission(user)


@register.simple_tag
def event_button_text(event, user):
    if event.has_edit_permission(user):
        return "Open"
    if event.is_allowed_to_open(user):
        if event.type == "EXAM":
            return "Take Exam"
        elif event.type == "ASSIGNMENT":
            return "Complete Assignment"
        else:
            return "Start Practice"
    elif event.can_view_results(user):
        return "View Results"
    elif event.cannot_access_event_yet(user):
        return "Not Available"
    else:
        return "Open"


@register.simple_tag
def tokens_column_name(event):
    if isinstance(event, Event) and event.is_exam_and_open():
        return "Tokens Worth"
    else:
        return "Tokens Earned"


@register.simple_tag
def exam_question_status(event, uqj):
    if event.is_exam and uqj.num_attempts() > 0:
        return "Submitted"
    else:
        return "Not Submitted"


@register.simple_tag
def row_class(uqj, event):
    if isinstance(event, Event) and event.is_exam:
        return ""
    else:
        return uqj.status_class
