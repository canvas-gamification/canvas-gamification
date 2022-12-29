from course.models.models import UserQuestionJunction, QuestionCategory, DIFFICULTY_CHOICES


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


def get_unsolved_practice_questions_count_by_category(user_id):
    categories = QuestionCategory.objects.all()

    result = []

    for category in categories:
        for difficulty, _ in DIFFICULTY_CHOICES:
            unsolved_questions = UserQuestionJunction.objects.filter(
                user_id=user_id,
                question__category_id=category.id,
                question__difficulty=difficulty,
                question__is_verified=True,
                is_solved=False,
            ).count()
            result.append({"category": category.id, "difficulty": difficulty, "unsolved_questions": unsolved_questions})

    return result
