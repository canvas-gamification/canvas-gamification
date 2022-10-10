from course.models.models import UserQuestionJunction


def get_solved_practice_questions_count(user_id, category_id, difficulty):
    uqjs = UserQuestionJunction.objects.filter(
        user_id=user_id, question__category_id=category_id, is_solved=True, question__is_verified=True
    )

    if difficulty:
        uqjs = uqjs.filter(question__difficulty=difficulty)

    return uqjs.count()
