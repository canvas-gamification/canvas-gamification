from canvas.utils.utils import get_course_registration


class TokenUseException(Exception):
    pass


def get_token_use(user, token_use_option_id):
    from canvas.models import TokenUse

    token_use = user.token_uses.filter(option__id=token_use_option_id)
    if token_use.exists():
        return token_use.get()

    token_use = TokenUse()
    token_use.user = user
    token_use.option_id = token_use_option_id
    token_use.save()
    return token_use


def update_token_use(user, course, data):
    from canvas.models import TokenUseOption

    course_reg = get_course_registration(user, course)

    total_tokens_used = 0
    for token_use_option_id, num in data.items():
        total_tokens_used += TokenUseOption.objects.get(id=token_use_option_id).tokens_required * num

    if total_tokens_used > course_reg.total_tokens_received:
        raise TokenUseException()

    for token_use_option_id, num in data.items():
        token_use = get_token_use(user, token_use_option_id)
        token_use.num_used = num
        token_use.apply()
        token_use.save()
