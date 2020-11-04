from functools import reduce
from django.db.models import Count
from course.models.models import Question


def count_category_questions(pk):
    return Question.objects.filter(category__pk=pk).count()

def get_avg_question_success(pk):
    questions = Question.objects.filter(category__pk=pk)
    total_tried = questions.annotate(Count('user_junctions__submissions')).filter(user_junctions__submissions__count__gt=0).count()
    total_solved = questions.filter(user_junctions__is_solved=True).count()
    return success_rate(total_tried, total_solved)

def success_rate(total_tried, total_solved):
    if total_tried == 0:
        return 0
    return total_solved * 100 / total_tried