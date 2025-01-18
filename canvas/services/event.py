from django.db.models import Count

from course.models.models import Submission, Question, UserQuestionJunction
from course.models.multiple_choice import MultipleChoiceQuestion
import re
import json


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


def _get_submission_details(question, submissions):
    if not question.event.featured or isinstance(question, MultipleChoiceQuestion):
        return

    details = []
    for s in submissions.all():
        if not s.in_progress:
            details.append({
                "name": s.user.nickname,
                "status": s.status,
                "grade": s.grade,
                "answer_files": s.answer_files,
                "passed_results": s.get_passed_test_results(),
                "failed_results": s.get_failed_test_results(),
                "decoded_stderr": s.get_decoded_stderr(),
            })
    return details


def get_question_stats(question):
    submissions = Submission.objects.filter(uqj__question=question)

    answers = {}
    if isinstance(question, MultipleChoiceQuestion):
        choices = json.loads(question.choices) if type(question.choices) == str else question.choices
        for submission in submissions:
            answer = choices[submission.answer]
            if answer not in answers:
                answers[answer] = 0
            answers[answer] += 1

    uqjs = (
        UserQuestionJunction.objects.filter(question=question)
        .annotate(submissions_count=Count("submissions"))
        .filter(submissions_count__gt=0)
    )

    return {
        "question": {
            "title": question.title,
            "text": question.text,
        },
        "has_variables": len(question.variables) > 0,
        "answers": answers,
        "error_messages": _get_error_messages(submissions),
        "submissions": {
            "Correct": uqjs.filter(is_solved=True).count(),
            "Partially Correct": uqjs.filter(is_partially_solved=True).count(),
            "Incorrect": uqjs.filter(is_solved=False, is_partially_solved=False).count(),
        },
        "submission_details": _get_submission_details(question, submissions),
        "status_messages": _get_status_messages(submissions),
        "total_submissions": submissions.count(),
        "num_students_attempted": uqjs.count(),
    }


def get_event_stats(event):
    return [get_question_stats(question) for question in event.question_set.all().order_by("title")]


def set_featured(event):
    event.course.events.update(featured=False)
    event.featured = True
    event.save()


def clear_featured(event):
    event.featured = False
    event.save()


def add_question_set(event, category_id, difficulty, number_of_questions):
    def extract_1st_number(string):
        g = re.search(r"\d+", string)
        return g.group() if g else -1

    questions = Question.objects.filter(
        event=None,
        course=None,
        is_verified=True,
        question_status=Question.CREATED,
        category_id=category_id,
        difficulty=difficulty,
    )[:number_of_questions]

    used_titles = [extract_1st_number(question["title"]) for question in event.question_set.values("title")]

    title = 1
    for q in questions:
        while str(title) in used_titles:
            title += 1
        q.copy_to_event(event, str(title))
        title += 1
