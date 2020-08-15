

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
        exist_ids = [x['id'] for x in user.question_junctions.values('id')]
        qs = [x['id'] for x in Question.objects.exclude(id__in=exist_ids).values('id')]

        for question_id in qs:
            uqj = UserQuestionJunction(user=user, question_id=question_id)
            uqj.save()

    if not user:
        exist_ids = [x['id'] for x in question.user_junctions.values('id')]
        qs = [x['id'] for x in MyUser.objects.exclude(id__in=exist_ids).values('id')]

        for user_id in qs:
            uqj = UserQuestionJunction(user_id=user_id, question=question)
            uqj.save()


def get_token_value(category, difficulty):
    from course.models.models import TokenValue

    if not category or not difficulty:
        return 0

    if not TokenValue.objects.filter(category=category, difficulty=difficulty).exists():
        token_value = TokenValue(category=category, difficulty=difficulty)
        token_value.save()
        return token_value.value
    return TokenValue.objects.get(category=category, difficulty=difficulty).value


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
                                    distractors=None):
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
        is_verified = author.is_teacher()

    if not max_submission_allowed:
        max_submission_allowed = len(choices)

    from course.models.models import MultipleChoiceQuestion

    if pk:
        MultipleChoiceQuestion.objects.filter(pk=pk).update(title=title, text=text, answer=answer,
                                                            max_submission_allowed=max_submission_allowed,
                                                            tutorial=tutorial, author=author,
                                                            category=category, difficulty=difficulty,
                                                            is_verified=is_verified,
                                                            variables=variables, choices=choices,
                                                            visible_distractor_count=visible_distractor_count)
    else:
        try:
            question = MultipleChoiceQuestion(title=title, text=text, answer=answer,
                                              max_submission_allowed=max_submission_allowed, tutorial=tutorial,
                                              author=author,
                                              category=category, difficulty=difficulty, is_verified=is_verified,
                                              variables=variables, choices=choices,
                                              visible_distractor_count=visible_distractor_count)
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
                         category=None, difficulty=None, is_verified=None, test_cases=None):
    if not max_submission_allowed:
        max_submission_allowed = 5
    if not is_verified:
        is_verified = author.is_teacher()

    from course.models.models import JavaQuestion
    if pk:
        JavaQuestion.objects.filter(pk=pk).update(title=title, text=text, max_submission_allowed=max_submission_allowed,
                                                  tutorial=tutorial, author=author, category=category,
                                                  difficulty=difficulty, is_verified=is_verified, test_cases=test_cases)
    else:
        question = JavaQuestion(title=title, text=text, max_submission_allowed=max_submission_allowed,
                                tutorial=tutorial,
                                author=author, category=category, difficulty=difficulty, is_verified=is_verified,
                                test_cases=test_cases)
        question.save()
