"""Self-contained fixture helpers for the submission / grading baseline suite.

These helpers are intentionally duplicated rather than shared with ``test/base.py``
or with the other baseline modules: the baseline suite must keep working unchanged
across the Python 3.8/Django 3.0 -> Python 3.14/Django 6.0 upgrade, so nothing here
may depend on another agent's file.

Everything is deliberately tiny: ``MyUser.save()`` and ``Question.save()`` both fan
out through ``ensure_uqj`` and create one ``UserQuestionJunction`` per
(user, question) pair, so every extra user or question costs real inserts.
"""

from datetime import timedelta

from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import MyUser, STUDENT, TEACHER
from canvas.models.models import CanvasCourse, Event
from course.models.models import QuestionCategory, UserQuestionJunction
from course.models.multiple_choice import MultipleChoiceQuestion, MultipleChoiceSubmission
from course.utils.utils import get_user_question_junction

PASSWORD = "baseline-pass-1234"

#: A fixed UQJ seed so that ``get_rendered_choices`` ordering never varies between runs.
#: (The grader only depends on the *number* of rendered choices, but pinning the seed
#: keeps ``answer_display`` and ``rendered_choices`` deterministic too.)
FIXED_SEED = 12345678

#: Four choices with ``visible_distractor_count=3`` and a single answer renders 4 keys.
CHOICES_4 = {"a": "a", "b": "b", "c": "c", "d": "d"}
CHOICES_5 = {"a": "a", "b": "b", "c": "c", "d": "d", "e": "e"}
CHOICES_6 = {"a": "a", "b": "b", "c": "c", "d": "d", "e": "e", "f": "f"}


class _Counter(object):
    value = 0


def _uniq(prefix):
    _Counter.value += 1
    return "{}_{}".format(prefix, _Counter.value)


def make_user(username=None, role=STUDENT, **extra):
    """Create a student (by default) user. Triggers ``ensure_uqj`` for every question."""
    username = username or _uniq("baseline_user")
    return MyUser.objects.create_user(
        username=username, email="{}@example.com".format(username), password=PASSWORD, role=role, **extra
    )


def make_teacher(username=None):
    return make_user(username=username, role=TEACHER)


def make_category(name=None):
    return QuestionCategory.objects.create(name=name or _uniq("baseline_cat"), description="baseline category")


def make_course(name=None, instructor=None):
    now = timezone.now()
    return CanvasCourse.objects.create(
        name=name or _uniq("baseline_course"),
        url="http://canvas.example.com",
        instructor=instructor,
        allow_registration=True,
        visible_to_students=True,
        start_date=now - timedelta(days=1),
        end_date=now + timedelta(days=10),
    )


def make_event(course, event_type="ASSIGNMENT", name=None, start_days=-1, end_days=10, count_for_tokens=False):
    """``start_days``/``end_days`` are offsets in days from *now*."""
    now = timezone.now()
    return Event.objects.create(
        name=name or _uniq("baseline_event"),
        type=event_type,
        course=course,
        count_for_tokens=count_for_tokens,
        start_date=now + timedelta(days=start_days),
        end_date=now + timedelta(days=end_days),
    )


def close_event(event):
    """Push an event fully into the past so ``is_open`` becomes False."""
    now = timezone.now()
    event.start_date = now - timedelta(days=10)
    event.end_date = now - timedelta(days=1)
    event.save()
    return event


def make_mcq(
    author,
    category,
    event=None,
    answer="a",
    choices=None,
    visible_distractor_count=3,
    max_submission_allowed=100,
    difficulty="EASY",
    title=None,
    tutorial="tutorial text",
    is_verified=True,
    course=None,
):
    """Create a MultipleChoiceQuestion directly (no ``create_multiple_choice_question``
    defaulting), so every grading-relevant knob is explicit in the test."""
    question = MultipleChoiceQuestion(
        title=title or _uniq("baseline_question"),
        text="question text",
        answer=answer,
        max_submission_allowed=max_submission_allowed,
        tutorial=tutorial,
        author=author,
        category=category,
        difficulty=difficulty,
        is_verified=is_verified,
        variables=[],
        choices=CHOICES_4 if choices is None else choices,
        visible_distractor_count=visible_distractor_count,
        course=course,
        event=event,
    )
    question.save()
    return question


def get_uqj(user, question, random_seed=FIXED_SEED):
    uqj = get_user_question_junction(user, question)
    if random_seed is not None and uqj.random_seed != random_seed:
        uqj.random_seed = random_seed
        uqj.save()
    return uqj


def reload_uqj(uqj):
    """Re-read a UQJ from the DB; ``Submission.save()`` writes tokens through its own
    instance, so an in-memory copy held by a test goes stale."""
    return UserQuestionJunction.objects.get(pk=uqj.pk)


def make_mcq_submission(uqj, answer):
    """Model-level submission (bypasses ``is_allowed_to_submit``), mirroring
    ``course.utils.utils.create_mcq_submission``."""
    submission = MultipleChoiceSubmission(uqj=UserQuestionJunction.objects.get(pk=uqj.pk), answer=answer)
    submission.save()
    return submission


def grades_for(uqj, answers):
    """Submit ``answers`` in order and return the resulting grade of each submission."""
    return [make_mcq_submission(uqj, answer).grade for answer in answers]


def api_client(user=None):
    client = APIClient()
    if user is not None:
        client.force_authenticate(user=user)
    return client
