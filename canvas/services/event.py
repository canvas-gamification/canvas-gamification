from course.models.models import Submission


def get_question_stats(question):
    submissions = Submission.objects.filter(uqj__question=question).values("answer")
    choices = question.choices

    answers = {}
    for submission in submissions:
        answer = choices[submission["answer"]]
        if answer not in answers:
            answers[answer] = 0
        answers[answer] += 1

    return {
        "question": {
            "title": question.title,
        },
        "answers": answers,
    }


def get_event_stats(event):
    return [get_question_stats(question) for question in event.question_set.all()]
