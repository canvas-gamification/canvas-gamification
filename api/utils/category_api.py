from django.db.models import Sum, F, Count
from course.models.models import Question, QuestionCategory
from course.utils.utils import get_token_value
from django.shortcuts import get_object_or_404


def get_next_categories_id(category):
    linked_to = category.next_categories.values_list('pk', flat=True)

    if not linked_to:
        return None
    else:
        return linked_to


def count_category_questions(pk):
    return Question.objects.filter(category__pk=pk).count()


def get_avg_question_success(pk):
    questions = get_object_or_404(QuestionCategory, pk=pk).question_set.all()
    tokens_recv = 0
    tokens_value = 0
    for question in questions:
        uqjs = question.user_junctions
        tokens_recv += uqjs.aggregate(total=Sum(F('tokens_received')))['total']
        num_uqjs = uqjs.annotate(Count('submissions')).filter(submissions__count__gt=0)

        tokens_value += get_token_value(question.category, question.difficulty) * len(num_uqjs)

    return success_rate(tokens_value, tokens_recv)


def success_rate(total_tried, total_solved):
    if total_tried == 0:
        return 0
    return total_solved * 100 / total_tried
