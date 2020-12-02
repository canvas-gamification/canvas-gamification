from django.db.models import Sum, F, Count
from course.models.models import Question
from course.utils.utils import get_token_value


def count_category_questions(pk):
    return Question.objects.filter(category__pk=pk).count()


def get_avg_question_success(category):
    questions = category.question_set.annotate(Count('user_junctions__submissions')).filter(
        user_junctions__submissions__count__gt=3)
    return get_avg_category_success(questions)


def get_user_success_rate(user_pk, category):
    if user_pk is None:
        return None

    questions = category.question_set.filter(user_junctions__user__pk=user_pk)
    return get_avg_category_success(questions)


def success_rate(total_tried, total_solved):
    if total_tried == 0:
        return 0
    return total_solved * 100 / total_tried


def get_avg_category_success(questions):
    tokens_recv = 0
    tokens_value = 0

    if not questions:
        return None

    for question in questions:
        uqjs = question.user_junctions
        tokens_recv += uqjs.aggregate(total=Sum(F('tokens_received')))['total']
        num_uqjs = uqjs.annotate(Count('submissions')).filter(submissions__count__gt=0)

        tokens_value += get_token_value(question.category, question.difficulty) * len(num_uqjs)

    return success_rate(tokens_value, tokens_recv)
