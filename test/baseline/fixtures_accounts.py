"""Self-contained fixture helpers for the accounts / general / serializer-shape baseline tests.

Deliberately NOT importing from ``test.base`` or from any sibling agent's fixture
module: these helpers create the smallest possible object graph, because
``MyUser.save()`` and ``Question.save()`` both fan out a ``UserQuestionJunction``
row per (user, question) pair.
"""

from django.utils import timezone

from accounts.models import MyUser, STUDENT, TEACHER
from canvas.models.models import CanvasCourse, Event
from course.models.models import QuestionCategory
from course.models.multiple_choice import MultipleChoiceQuestion

# Long enough for MinimumLengthValidator and not all-numeric for NumericPasswordValidator.
STRONG_PASSWORD = "baseline-pw-7Q"
OTHER_STRONG_PASSWORD = "baseline-pw-8R"

# The front-end origin the activation / reset emails are built from.
ORIGIN = "http://frontend.example.com"


def make_user(username="acct_student", email=None, password=STRONG_PASSWORD, role=STUDENT, **extra):
    """Create (and save) a MyUser. Keep the number of these small."""
    fields = {
        "first_name": "Test",
        "last_name": "Person",
        "nickname": username,
    }
    fields.update(extra)
    return MyUser.objects.create_user(
        username=username,
        email=email if email is not None else "{}@example.com".format(username),
        password=password,
        role=role,
        **fields,
    )


def make_teacher(username="acct_teacher", email=None, password=STRONG_PASSWORD, **extra):
    return make_user(username=username, email=email, password=password, role=TEACHER, **extra)


def make_category(name="baseline-category"):
    category = QuestionCategory(name=name, description=name)
    category.save()
    return category


def make_course(instructor=None, name="Baseline Course", **extra):
    fields = {
        "url": "http://canvas.example.com",
        "allow_registration": True,
        "visible_to_students": True,
        "start_date": timezone.now() - timezone.timedelta(days=1),
        "end_date": timezone.now() + timezone.timedelta(days=10),
    }
    fields.update(extra)
    course = CanvasCourse(name=name, instructor=instructor, **fields)
    course.save()
    return course


def make_event(course, name="baseline-event", event_type="ASSIGNMENT", **extra):
    fields = {
        "count_for_tokens": False,
        "start_date": timezone.now() - timezone.timedelta(days=1),
        "end_date": timezone.now() + timezone.timedelta(days=10),
    }
    fields.update(extra)
    event = Event(name=name, type=event_type, course=course, **fields)
    event.save()
    return event


def make_mcq_question(author=None, category=None, event=None, title="baseline-question", **extra):
    """One multiple-choice question. Creates one UQJ per existing user."""
    fields = {
        "text": "What is the answer to {{title}}?",
        "answer": "a",
        "choices": {"a": "choice a", "b": "choice b"},
        "visible_distractor_count": 1,
        "variables": [],
        "variation_types": [],
        "difficulty": "EASY",
        "is_verified": True,
        "max_submission_allowed": 10,
        "tutorial": "tutorial text",
    }
    fields.update(extra)
    question = MultipleChoiceQuestion(title=title, author=author, category=category, event=event, **fields)
    question.save()
    return question
