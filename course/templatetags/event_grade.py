from django import template

register = template.Library()


@register.filter
def total_event_grade(event, user):
    # calculate the total grade from all question submissions for an event, for this user
    total_event_grade = 0
    for question in event.question_set.all():
        for uqj in question.user_junctions.all():
            if not user == uqj.user:
                continue
            curr_uqj_grade = 0
            for submission in uqj.submissions.all():
                curr_grade = submission.grade
                if curr_grade > curr_uqj_grade:
                    curr_uqj_grade = curr_grade
            total_event_grade += curr_uqj_grade
    return total_event_grade