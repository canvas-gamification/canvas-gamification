from django.db.models import Count
from course.models.models import Question


def count_category_questions(pk):
    return Question.objects.filter(category__pk=pk).count()


def get_avg_question_success(pk):
    questions = Question.objects.filter(category__pk=pk)
    return get_question_success_rate(questions)


def get_user_success_rate(user_pk, category_pk):
    if user_pk is None:
        return None

    questions = Question.objects.filter(category__pk=category_pk, user_junctions__user__pk=user_pk)
    return get_question_success_rate(questions)


def success_rate(total_tried, total_solved):
    if total_tried == 0:
        return 0
    return total_solved * 100 / total_tried


def get_question_success_rate(questions):
    questions_tried = questions.annotate(Count('user_junctions__submissions')).filter(
        user_junctions__submissions__count__gt=0)
    total_tried = questions_tried.count()
    total_solved = questions_tried.filter(user_junctions__is_solved=True).count()

    return success_rate(total_tried, total_solved)