from course.models.models import UserQuestionJunction, QuestionCategory, DIFFICULTY_CHOICES, Question


def get_solved_practice_questions_count(user_id, category_id, difficulty, start_time, end_time):
    uqjs = UserQuestionJunction.objects.filter(
        user_id=user_id,
        question__category_id=category_id,
        is_solved=True,
        solved_at__gt=start_time,
        solved_at__lt=end_time,
        question__is_verified=True,
        question__event=None,
        question__course=None,
        question__question_status=Question.CREATED,
    )

    if difficulty:
        uqjs = uqjs.filter(question__difficulty=difficulty)

    return uqjs.count()


def get_solved_questions_ratio(user_id, category_id, difficulty):
    uqjs = UserQuestionJunction.objects.filter(
        user_id=user_id,
        question__category_id=category_id,
        question__difficulty=difficulty,
        question__is_verified=True,
        question__event=None,
        question__course=None,
        question__question_status=Question.CREATED,
    )

    total_count = uqjs.count()
    solved_count = uqjs.filter(is_solved=True).count()

    return 0 if total_count == 0 else solved_count / total_count


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
                question__event=None,
                question__course=None,
                question__question_status=Question.CREATED,
                is_solved=False,
            ).count()
            result.append(
                {
                    "category": category.id,
                    "difficulty": difficulty,
                    "unsolved_questions": unsolved_questions,
                }
            )

    return result


def get_number_of_questions_counted_by_category_and_difficulty():
    categories = QuestionCategory.objects.all()

    result = []

    for category in categories:
        for difficulty, _ in DIFFICULTY_CHOICES:
            available_questions = category.question_set.filter(
                difficulty=difficulty,
                is_verified=True,
                course=None,
                event=None,
                question_status=Question.CREATED,
            ).count()

            result.append(
                {
                    "category": category.id,
                    "difficulty": difficulty,
                    "available_questions": available_questions,
                }
            )

    return result
