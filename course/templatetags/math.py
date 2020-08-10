from django import template

register = template.Library()


@register.filter
def to_percentage(value):
    return "{}%".format(round(value*100, 2))
