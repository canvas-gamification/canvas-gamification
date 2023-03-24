from course.models.models import Submission, Question
from course.models.multiple_choice import MultipleChoiceQuestion
import re


def _get_status_messages(submissions):
    status_messages = {}

    for s in submissions.all():
        if hasattr(s, "get_status_message"):
            message = s.get_status_message()
            if message not in status_messages:
                status_messages[message] = 0
            status_messages[message] += 1

    return status_messages


def _get_error_messages(submissions):
    error_messages = {}

    for s in submissions.all():
        if hasattr(s, "get_failed_test_results"):
            results = s.get_failed_test_results()
            for result in results:
                message = result["message"]
                if message not in error_messages:
                    error_messages[message] = 0
                error_messages[message] += 1

    return error_messages


def _get_submission_status(submissions):
    return {
        "Correct": submissions.filter(is_correct=True).count(),
        "Partially Correct": submissions.filter(is_correct=False, is_partially_correct=True).count(),
        "Incorrect": submissions.filter(is_correct=False, is_partially_correct=False).count(),
    }


def get_question_stats(question):
    submissions = Submission.objects.filter(uqj__question=question)

    answers = {}
    if isinstance(question, MultipleChoiceQuestion):
        for submission in submissions:
            answer = submission.uqj.get_rendered_choices()[submission.answer]
            if answer not in answers:
                answers[answer] = 0
            answers[answer] += 1

    return {
        "question": {
            "title": question.title,
        },
        "has_variables": len(question.variables) > 0,
        "answers": answers,
        "error_messages": _get_error_messages(submissions),
        "submissions": _get_submission_status(submissions),
        "status_messages": _get_status_messages(submissions),
        "total_submissions": submissions.count(),
    }


def get_event_stats(event):
    return [get_question_stats(question) for question in event.question_set.all()]


def set_featured(event):
    event.course.events.update(featured=False)
    event.featured = True
    event.save()


def add_question_set(event, category_id, difficulty, number_of_questions):
    def begins_with_numbers(string):
        # return any(char.isdigit() for char in string)
        return string[0].isdigit()

    def extract_1st_number(string):
        # return re.search('[0-9]+', string).group()
        return re.findall(r"\d+", string)[0]

    questions = Question.objects.filter(
        event=None,
        course=None,
        is_verified=True,
        question_status=Question.CREATED,
        category_id=category_id,
        difficulty=difficulty,
    )[:number_of_questions]

    used_titles = [question["title"] for question in event.question_set.values("title")]
    used_titles = [extract_1st_number(title) for title in used_titles if begins_with_numbers(title)]
    used_titles.sort()
    print(used_titles)

    if len(used_titles) == 0:
        idx = 0  # in case items is empty, and you need it after the loop
        for idx, q in enumerate(questions, start=1):
            q.copy_to_event(event, str(idx))
        return

    title = 1
    for idx, q in enumerate(questions):
        while used_titles.count(str(title)) != 0:
            title += 1
        q.copy_to_event(event, str(title))
        title += 1
