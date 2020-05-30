def get_user_question_junction(user, question):
    from course.models import UserQuestionJunction

    if user.question_junctions.filter(question=question).exists():
        return user.question_junctions.get(question=question)
    user_question_junction = UserQuestionJunction(user=user, question=question)
    user_question_junction.save()
    return user_question_junction


def get_token_value(category, difficulty):
    from course.models import TokenValue

    if not category or not difficulty:
        return 0

    if not TokenValue.objects.filter(category=category, difficulty=difficulty).exists():
        token_value = TokenValue(category=category, difficulty=difficulty)
        token_value.save()
        return token_value.value
    return TokenValue.objects.get(category=category, difficulty=difficulty).value


def increment_char(c):
    return chr(ord(c) + 1)


def create_multiple_choice_question(title=None, text=None, answer=None, max_submission_allowed=None, tutorial=None,
                                    author=None, category=None, difficulty=None, is_verified=None, variables=None,
                                    choices=None, visible_distractor_count=None, answer_text=None, distractors=None):
    if not answer and not answer_text:
        raise Exception("answer or answer_text should be provided!")

    if choices and (answer_text or distractors):
        raise Exception("choices and (answer_text or distractors) cannot be set at the same time!")

    if not choices:
        choices = {}
        choice_label = 'a'

        answer = choice_label
        choices[choice_label] = answer_text
        choice_label = increment_char(choice_label)

        for text in distractors:
            choices[choice_label] = text

        if not is_verified:
            is_verified = author.is_teacher()

    from course.models import MultipleChoiceQuestion
    question = MultipleChoiceQuestion(title=title, text=text, answer=answer,
                                      max_submission_allowed=max_submission_allowed, tutorial=tutorial, author=author,
                                      category=category, difficulty=difficulty, is_verified=is_verified,
                                      variables=variables, choices=choices,
                                      visible_distractor_count=visible_distractor_count)
    question.save()
    return question
