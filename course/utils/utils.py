from django.db.models import Count, Q


def get_user_question_junction(user, question):
    from course.models.models import UserQuestionJunction

    if user.question_junctions.filter(question=question).exists():
        return user.question_junctions.get(question=question)
    user_question_junction = UserQuestionJunction(user=user, question=question)
    user_question_junction.save()
    return user_question_junction


def ensure_uqj(user, question):
    from course.models.models import UserQuestionJunction
    from course.models.models import Question
    from accounts.models import MyUser

    if not user and not question:
        return

    if user and question:
        if user.question_junctions.filter(question=question).exists():
            return
        uqj = UserQuestionJunction(user=user, question=question)
        uqj.save()

    if not question:
        exist_ids = {x['question_id'] for x in user.question_junctions.values('question_id')}
        all_ids = {x['id'] for x in Question.objects.values('id')}
        qs = all_ids - exist_ids

        for question_id in qs:
            uqj = UserQuestionJunction(user=user, question_id=question_id)
            uqj.save()

    if not user:
        exist_ids = {x['user_id'] for x in question.user_junctions.values('user_id')}
        all_ids = {x['id'] for x in MyUser.objects.values('id')}
        qs = all_ids - exist_ids

        for user_id in qs:
            uqj = UserQuestionJunction(user_id=user_id, question=question)
            uqj.save()


def get_token_value_object(category, difficulty):
    from course.models.models import TokenValue

    if not category or not difficulty:
        token_value = TokenValue()
        token_value.value = 0
        return token_value

    if not TokenValue.objects.filter(category=category, difficulty=difficulty).exists():
        token_value = TokenValue(category=category, difficulty=difficulty)
        token_value.save()
        return token_value
    return TokenValue.objects.get(category=category, difficulty=difficulty)


def get_token_value(category, difficulty):
    return get_token_value_object(category, difficulty).value


def get_token_values():
    from course.models.models import QuestionCategory
    from course.models.models import DIFFICULTY_CHOICES
    from course.models.models import TokenValue

    categories = QuestionCategory.objects.filter(parent__isnull=False).all()

    for category in categories:
        for difficulty in [x for x, y in DIFFICULTY_CHOICES]:
            get_token_value(category, difficulty)

    return TokenValue.objects.all()


def increment_char(c):
    return chr(ord(c) + 1)


class QuestionCreateException(Exception):

    def __init__(self, message, user_message):
        super().__init__()
        self.message = message
        self.user_message = user_message


def create_multiple_choice_question(pk=None, title=None, text=None, answer=None, max_submission_allowed=None,
                                    tutorial=None, author=None, category=None, difficulty=None, is_verified=None,
                                    variables=None, choices=None, visible_distractor_count=None, answer_text=None,
                                    distractors=None, course=None, event=None):
    if not answer and not answer_text:
        raise QuestionCreateException(
            message="answer or answer_text should be provided!",
            user_message="Cannot create question due to an unknown error, please contact developers"
        )

    if choices and (answer_text or distractors):
        raise QuestionCreateException(
            message="choices and (answer_text or distractors) cannot be set at the same time!",
            user_message="Cannot create question due to an unknown error, please contact developers"
        )

    if not variables:
        variables = []

    if not choices:
        choices = {}
        choice_label = 'a'

        answer = choice_label
        choices[choice_label] = answer_text
        choice_label = increment_char(choice_label)

        for distractor in distractors:
            choices[choice_label] = distractor
            choice_label = increment_char(choice_label)

    if not is_verified:
        is_verified = author.is_teacher

    if not max_submission_allowed:
        max_submission_allowed = len(choices)

    from course.models.multiple_choice import MultipleChoiceQuestion

    if pk:
        MultipleChoiceQuestion.objects.filter(pk=pk).update(title=title, text=text, answer=answer,
                                                            max_submission_allowed=max_submission_allowed,
                                                            tutorial=tutorial, author=author,
                                                            category=category, difficulty=difficulty,
                                                            is_verified=is_verified,
                                                            variables=variables, choices=choices,
                                                            visible_distractor_count=visible_distractor_count,
                                                            course=course,
                                                            event=event)
    else:
        try:
            question = MultipleChoiceQuestion(title=title, text=text, answer=answer,
                                              max_submission_allowed=max_submission_allowed, tutorial=tutorial,
                                              author=author,
                                              category=category, difficulty=difficulty, is_verified=is_verified,
                                              variables=variables, choices=choices,
                                              visible_distractor_count=visible_distractor_count,
                                              course=course,
                                              event=event)
            question.save()
        except Exception as e:
            print(e)
            raise QuestionCreateException(
                message="Invalid list of arguments to create MultipleChoiceQuestion",
                user_message="Cannot create question due to an unknown error, please contact developers"
            )
        return question
    return None


def create_java_question(pk=None, title=None, text=None, max_submission_allowed=None, tutorial=None, author=None,
                         category=None, difficulty=None, is_verified=None, junit_template=None, variables=None,
                         input_files=None, course=None, event=None):
    if not max_submission_allowed:
        max_submission_allowed = 5
    if not is_verified:
        is_verified = author.is_teacher
    if not variables:
        variables = []

    from course.models.java import JavaQuestion
    if pk:
        JavaQuestion.objects.filter(pk=pk).update(
            title=title,
            text=text,
            max_submission_allowed=max_submission_allowed,
            tutorial=tutorial,
            author=author,
            category=category,
            difficulty=difficulty,
            is_verified=is_verified,
            junit_template=junit_template,
            input_files=input_files,
            variables=variables,
            course=course,
            event=event,
        )
    else:
        question = JavaQuestion(
            title=title,
            text=text,
            max_submission_allowed=max_submission_allowed,
            tutorial=tutorial,
            author=author,
            category=category,
            difficulty=difficulty,
            is_verified=is_verified,
            junit_template=junit_template,
            input_files=input_files,
            variables=variables,
            course=course,
            event=event,
        )
        question.save()


def create_parsons_question(pk=None, title=None, text=None, max_submission_allowed=None, tutorial=None, author=None,
                            category=None, difficulty=None, is_verified=None, junit_template=None, variables=None,
                            input_files=None, course=None, event=None):
    if not max_submission_allowed:
        max_submission_allowed = 5
    if not is_verified:
        is_verified = author.is_teacher
    if not variables:
        variables = []

    from course.models.parsons import ParsonsQuestion
    if pk:
        ParsonsQuestion.objects.filter(pk=pk).update(
            title=title,
            text=text,
            max_submission_allowed=max_submission_allowed,
            tutorial=tutorial,
            author=author,
            category=category,
            difficulty=difficulty,
            is_verified=is_verified,
            junit_template=junit_template,
            input_files=input_files,
            variables=variables,
            course=course,
            event=event,
        )
    else:
        question = ParsonsQuestion(
            title=title,
            text=text,
            max_submission_allowed=max_submission_allowed,
            tutorial=tutorial,
            author=author,
            category=category,
            difficulty=difficulty,
            is_verified=is_verified,
            junit_template=junit_template,
            input_files=input_files,
            variables=variables,
            course=course,
            event=event,
        )
        question.save()


def create_mcq_submission(uqj=None, answer=None):
    from course.models.multiple_choice import MultipleChoiceSubmission
    submission = MultipleChoiceSubmission(
        uqj=uqj,
        answer=answer
    )
    submission.save()
    return submission


def get_question_title(user, question, key):
    if key is None:
        return question.title
    elif question.course.is_instructor(user) and key is not None:
        return "Question " + str(key) + " - " + question.title
    else:
        return "Question " + str(key)


def calculate_average_success(uqjs, category=None, difficulty=None):
    """
    Function that will calculate average success as a value between 0-1 depending on the queryset and filters given.
    Accounts for a category filter, and a difficulty filter, both of which are optional.
    """
    if category:
        category_filter = Q(question__category=category) | Q(question__category__parent=category)
        if difficulty:
            solved = uqjs.filter(
                category_filter, is_solved=True, question__difficulty=difficulty).count()
            total = uqjs.annotate(Count('submissions')) \
                .filter(category_filter, question__difficulty=difficulty, submissions__count__gt=0) \
                .count()
        else:
            solved = uqjs.filter(category_filter, is_solved=True).count()
            total = uqjs.annotate(Count('submissions')) \
                .filter(category_filter, submissions__count__gt=0) \
                .count()
    else:
        solved = uqjs.filter(is_solved=True).count()
        total = uqjs.annotate(Count('submissions')).filter(submissions__count__gt=0).count()

    return success_rate(solved, total)


def success_rate(solved, total):
    return 0 if total == 0 else (solved / total)
