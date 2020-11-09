from django import template

register = template.Library()


@register.simple_tag
def is_registered(course, user):
    return course.is_registered(user)


@register.simple_tag
def is_allowed_to_open(course, user):
    return course.is_registered(user) or course.is_instructor(user) or user.is_teacher
