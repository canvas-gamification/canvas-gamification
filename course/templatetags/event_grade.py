from django import template
from course.models.models import UserQuestionJunction

register = template.Library()


@register.filter
def total_event_grade(event, user):
    uqjs = UserQuestionJunction.objects.filter(user=user, question__event=event).all()
    token_value = 0
    tokens_recv = 0
    for uqj in uqjs:
        token_value += uqj.question.token_value
        tokens_recv += uqj.tokens_received

    # return '{} / {}'.format(tokens_recv, token_value)
    return '{:.2f}%'.format(tokens_recv * 100/token_value)