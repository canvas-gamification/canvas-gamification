from accounts.models import MyUser
from course.models.models import Question
from course.utils.utils import ensure_uqj


def consume(message):
    # message value and key are raw bytes -- decode if necessary!
    # e.g., for unicode: `message.value.decode('utf-8')`
    print("%s:%d:%d: key=%s value=%s" % (message.topic, message.partition,
                                         message.offset, message.key,
                                         message.value))
    if message.topic == 'USER:CREATED':
        user_id = message.value.decode()
        user = MyUser.objects.get(id=user_id)
        ensure_uqj(user, None)

    if message.topic == "QUESTION_CREATED":
        question_id = message.value.decode()
        question = Question.objects.get(id=question_id)
        ensure_uqj(None, question)
