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
    return event.has_view_permission(user)
