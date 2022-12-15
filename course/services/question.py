from course.models.models import UserQuestionJunction


def get_solved_practice_questions_count(user_id, category_id, difficulty, start_time, end_time):
    uqjs = UserQuestionJunction.objects.filter(
        user_id=user_id,
        question__category_id=category_id,
        is_solved=True,
        question__is_verified=True,
        solved_at__gt=start_time,
        solved_at__lt=end_time,
    )

    if difficulty:
        uqjs = uqjs.filter(question__difficulty=difficulty)

    return uqjs.count()
