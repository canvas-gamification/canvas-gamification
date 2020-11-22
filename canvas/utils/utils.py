from functools import reduce
from django.db.models import Sum, F, Count
from course.utils.utils import get_token_value


def get_total_event_grade(event, user):
    uqjs = user.question_junctions.filter(question__event=event)
    token_recv = uqjs.aggregate(total=Sum(F('tokens_received')))['total']

    question_types = uqjs.all().values('question__category', 'question__difficulty').annotate(num_questions=Count('id'))

    def group_token_value(total, curr):
        return get_token_value(curr['question__category'], curr['question__difficulty']) * curr['num_questions'] + total

    token_value = reduce(group_token_value, question_types, 0)

    if not token_value == 0:
        return '{:.2f}%'.format(token_recv * 100 / token_value)
    else:
        return 'N/A'


def get_course_registration(user, course):
    from canvas.models import CanvasCourseRegistration

    qs = CanvasCourseRegistration.objects.filter(user=user, course=course)
    return qs.get() if qs.exists() else None
