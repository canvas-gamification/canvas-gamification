from functools import reduce
from django.db.models import Sum, F, Count
from course.models.models import Question
from course.utils.utils import get_token_value


def get_next_categories_id(category):
    linked_to = category.next_categories.values_list('pk', flat=True)

    if not linked_to:
        return None
    else:
        return linked_to


def count_category_questions(pk):
    return Question.objects.filter(category__pk=pk).count()


def get_avg_question_success(pk):
    questions = Question.objects.filter(category__pk=pk)
    tokens_recv = questions.aggregate(total=Sum(F('user_junctions__tokens_received')))['total']
    question_types = questions.all().values('category', 'difficulty').annotate(num_questions=Count('id'))

    def group_token_value(total, curr):
        return get_token_value(curr['category'], curr['difficulty']) * curr['num_questions'] + total

    tokens_value = reduce(group_token_value, question_types, 0)

    return success_rate(tokens_value, tokens_recv)


def success_rate(total_tried, total_solved):
    if total_tried == 0:
        return 0
    return total_solved * 100 / total_tried
