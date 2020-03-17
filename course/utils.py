from django.template.defaultfilters import register


def get_user_question_junction(user, question):
    from course.models import UserQuestionJunction

    if user.question_junctions.filter(question=question).exists():
        return user.question_junctions.get(question=question)
    user_question_junction = UserQuestionJunction(user=user, question=question)
    user_question_junction.save()
    return user_question_junction


@register.filter
def return_item(l, i):
    try:
        return l[i]
    except:
        return None


def get_token_value(category, difficulty):
    from course.models import TokenValue

    if not category or not difficulty:
        return 0

    if not TokenValue.objects.filter(category=category, difficulty=difficulty).exists():
        token_value = TokenValue(category=category, difficulty=difficulty)
        token_value.save()
        return token_value.value
    return TokenValue.objects.get(category=category, difficulty=difficulty).value
