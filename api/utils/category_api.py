from django.db.models import Sum, F, Count
from course.utils.utils import get_token_value


def count_category_questions(category):
    return category.question_set.count()


def get_avg_category_success(category):
    questions = category.question_set.annotate(Count('user_junctions__submissions')).filter(
        user_junctions__submissions__count__gt=3)
    return avg_category_success(questions)


def get_user_success_rate(user_pk, category):
    if user_pk is None:
        return None

    questions = category.question_set.filter(user_junctions__user__pk=user_pk)
    return avg_category_success(questions)


def get_percentage(numerator, denominator):
    if denominator == 0:
        return 0
    return numerator * 100 / denominator


def avg_category_success(questions):
    tokens_recv = 0
    tokens_value = 0

    if not questions:
        return None
      
    for question in questions:
        uqjs = question.user_junctions
        tokens_recv += uqjs.aggregate(total=Sum(F('tokens_received')))['total']
        num_uqjs = uqjs.annotate(Count('submissions')).filter(submissions__count__gt=0)

        tokens_value += get_token_value(question.category, question.difficulty) * len(num_uqjs)

    return get_percentage(tokens_value, tokens_recv)


def get_next_categories_id(category):
    linked_to = category.next_categories.values_list('pk', flat=True)

    if not linked_to:
        return None
    else:
        return linked_to
