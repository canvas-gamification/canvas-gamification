from django.db.models import OuterRef, Subquery, F

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


def _get_submission_status(submissions, students):
    return {
        "Correct": submissions.filter(is_correct=True).count(),
        "Partially Correct": submissions.filter(is_correct=False, is_partially_correct=True).count(),
        "Incorrect": submissions.filter(is_correct=False, is_partially_correct=False).count(),
        "Unattempted": students - submissions.count(),
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

    most_recent_submission_time_for_submission_author = (
        submissions
        .filter(uqj__user=OuterRef('uqj__user'))
        .order_by('-submission_time')
        .values('submission_time')[:1]
    )

    recent_submissions = (
        submissions
        .filter(uqj__user__role="Student")
        .annotate(recent_timestamp=Subquery(most_recent_submission_time_for_submission_author))
        .filter(submission_time=F('recent_timestamp'))
    )

    student_course_registrations = question.course.verified_course_registration.filter(registration_type="STUDENT")\
        .count()

    return {
        "question": {
            "title": question.title,
            "text": question.text,
        },
        "has_variables": len(question.variables) > 0,
        "answers": answers,
        "error_messages": _get_error_messages(submissions),
        "submissions": _get_submission_status(recent_submissions, student_course_registrations),
        "status_messages": _get_status_messages(submissions),
        "total_submissions": submissions.count(),
        "student_course_registrations": student_course_registrations,  # this feels like it should not go here
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
