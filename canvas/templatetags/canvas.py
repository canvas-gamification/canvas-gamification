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
    return event.has_view_permission(user) or event.status == "Closed"


@register.simple_tag
def event_button_text(event, user):
    if event.has_edit_permission(user):
        return "Edit"
    if event.is_open() and event.course.is_registered(user):
        if event.type == "EXAM":
            return "Take Exam"
        elif event.type == "ASSIGNMENT":
            return "Complete Assignment"
        else:
            return "Start Practice"
    elif event.status == "Closed" and event.course.is_registered(user):
        return "View Results"
    elif event.status == "Not available yet" and event.course.is_registered(user):
        return "Not Available"
    else:
        return "Open"






