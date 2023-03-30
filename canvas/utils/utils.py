from functools import reduce
from django.db.models import Sum, F, Count

# from course.models.models import UserQuestionJunction
from course.utils.utils import get_token_value


def get_total_event_tokens(event):
    question_types = event.question_set.values("category", "difficulty").annotate(num_questions=Count("id"))

    def group_token_value(total, curr):
        return get_token_value(curr["category"], curr["difficulty"]) * curr["num_questions"] + total

    token_value = reduce(group_token_value, question_types, 0)

    return token_value


def get_total_event_grade(event, user):
    uqjs = user.question_junctions.filter(question__event=event)
    token_recv = uqjs.aggregate(total=Sum(F("tokens_received")))["total"]

    token_value = get_total_event_tokens(event)

    if not token_value == 0:
        return token_recv * 100 / token_value
    else:
        return 0


def get_course_registration(user, course):
    from canvas.models.models import CanvasCourseRegistration

    qs = CanvasCourseRegistration.objects.filter(user=user, course=course)
    if qs.exists():
        return qs.get()
    course_reg = CanvasCourseRegistration(user=user, course=course)

    course_reg.save()
    return course_reg


# def get_has_solved_event(event, user):
#     event_questions = event.question_set.all()
#     uqjs = UserQuestionJunction.objects.filter(user_id=user.id, is_solved=True, question__in=event_questions)
#
#     if uqjs.exists():
#         return True
#
#     return False
