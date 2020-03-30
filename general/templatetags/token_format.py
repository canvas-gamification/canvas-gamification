from django import template

register = template.Library()


@register.filter
def token_change_format(token):
    return "{:+.2f}".format(token)

