class EventCreateException(Exception):

    def __init__(self, message, user_message):
        super().__init__()
        self.message = message
        self.user_message = user_message


def create_event(name=None, course=None, count_for_tokens=None, start_date=None, end_date=None):
    try:
        from canvas.models import Event
        new_event = Event(name=name, course=course,
                          count_for_tokens=count_for_tokens,
                          start_date=start_date,
                          end_date=end_date)
        new_event.save()
    except Exception as e:
        print(e)
        raise EventCreateException(
            message="Invalid list of arguments to create MultipleChoiceQuestion",
            user_message="Cannot create question due to an unknown error, please contact developers"
        )
