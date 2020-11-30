from django import template

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
def is_exam_event(event):
    return event != '' and event.is_exam()


@register.simple_tag
def exam_question_status(event, uqj):
    if is_exam_event(event) and uqj.num_attempts() > 0:
        return "Submitted"
    else:
        return "Not Submitted"
