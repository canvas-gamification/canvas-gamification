"""Self-contained fixture helpers for the questions / UQJ / randomisation baseline tests.

Deliberately does NOT import from ``test/questions.py``, ``test/base.py`` or any other
agent's fixture module: these tests must keep working even if those files change.

Everything here is plain model construction so the tests can control -- exactly -- how
many users and questions exist, which matters because ``MyUser.save()`` and
``Question.save()`` both fan out ``ensure_uqj``.
"""

from django.utils import timezone

from accounts.models import MyUser
from canvas.models.models import CanvasCourse, Event
from course.models.java import JavaQuestion
from course.models.models import QuestionCategory
from course.models.multiple_choice import MultipleChoiceQuestion
from course.models.parsons import ParsonsQuestion

STUDENT = "Student"
TEACHER = "Teacher"


def make_user(username, role=STUDENT, password="aaaaaaaa", **kwargs):
    """Create a MyUser. NOTE: MyUser.save() calls ensure_uqj -> one UQJ per question."""
    return MyUser.objects.create_user(
        username=username,
        email=kwargs.pop("email", "{}@example.com".format(username)),
        password=password,
        role=role,
        **kwargs,
    )


def make_student(username="bl_student", **kwargs):
    return make_user(username, role=STUDENT, **kwargs)


def make_teacher(username="bl_teacher", **kwargs):
    return make_user(username, role=TEACHER, **kwargs)


def make_category(name="bl_category", parent=None):
    category = QuestionCategory(name=name, description=name, parent=parent)
    category.save()
    return category


def make_course(instructor=None, name="BL Course", **kwargs):
    course = CanvasCourse(
        name=name,
        url="http://canvas.example.com",
        instructor=instructor,
        allow_registration=True,
        visible_to_students=True,
        start_date=kwargs.pop("start_date", timezone.now() - timezone.timedelta(days=1)),
        end_date=kwargs.pop("end_date", timezone.now() + timezone.timedelta(days=10)),
        **kwargs,
    )
    course.save()
    return course


def make_event(course, name="bl_event", event_type="ASSIGNMENT", count_for_tokens=False, **kwargs):
    event = Event(
        name=name,
        type=event_type,
        course=course,
        count_for_tokens=count_for_tokens,
        start_date=kwargs.pop("start_date", timezone.now() - timezone.timedelta(days=1)),
        end_date=kwargs.pop("end_date", timezone.now() + timezone.timedelta(days=10)),
        **kwargs,
    )
    event.save()
    return event


DEFAULT_CHOICES = {"a": "alpha", "b": "bravo", "c": "charlie", "d": "delta", "e": "echo", "f": "foxtrot"}


def make_mcq(
    author=None,
    category=None,
    event=None,
    title="mcq title",
    text="mcq text",
    answer="a",
    choices=None,
    visible_distractor_count=2,
    variables=None,
    difficulty="EASY",
    is_verified=True,
    **kwargs,
):
    question = MultipleChoiceQuestion(
        title=title,
        text=text,
        answer=answer,
        author=author,
        category=category,
        event=event,
        difficulty=difficulty,
        is_verified=is_verified,
        variables=[] if variables is None else variables,
        choices=dict(DEFAULT_CHOICES) if choices is None else choices,
        visible_distractor_count=visible_distractor_count,
        **kwargs,
    )
    question.save()
    return question


DEFAULT_JAVA_INPUT_FILES = [
    {"name": "Main.java", "compile": True, "template": "public class Main {}", "hidden": False},
    {"name": "Helper.java", "compile": False, "template": "class Helper {}", "hidden": True},
]


def make_java(
    author=None,
    category=None,
    event=None,
    title="java title",
    text="java text",
    junit_template="// junit template",
    input_files=None,
    variables=None,
    difficulty="EASY",
    is_verified=True,
    **kwargs,
):
    question = JavaQuestion(
        title=title,
        text=text,
        author=author,
        category=category,
        event=event,
        difficulty=difficulty,
        is_verified=is_verified,
        variables=[] if variables is None else variables,
        junit_template=junit_template,
        input_files=[dict(f) for f in DEFAULT_JAVA_INPUT_FILES] if input_files is None else input_files,
        **kwargs,
    )
    question.save()
    return question


DEFAULT_PARSONS_INPUT_FILES = [
    {
        "name": "Main.java",
        "compile": True,
        "lines": ["line one", "line two", "line three", "line four", "line five"],
    },
    {
        "name": "Second.java",
        "compile": False,
        "lines": ["s1", "s2", "s3", "s4"],
    },
]


def make_parsons(
    author=None,
    category=None,
    event=None,
    title="parsons title",
    text="parsons text",
    junit_template="// junit template",
    input_files=None,
    variables=None,
    difficulty="EASY",
    is_verified=True,
    **kwargs,
):
    question = ParsonsQuestion(
        title=title,
        text=text,
        author=author,
        category=category,
        event=event,
        difficulty=difficulty,
        is_verified=is_verified,
        variables=[] if variables is None else variables,
        junit_template=junit_template,
        input_files=[dict(f) for f in DEFAULT_PARSONS_INPUT_FILES] if input_files is None else input_files,
        **kwargs,
    )
    question.save()
    return question


def uqj_for(user, question, random_seed=None):
    """Fetch the UQJ that ensure_uqj already created, optionally pinning random_seed."""
    uqj = user.question_junctions.get(question=question)
    if random_seed is not None:
        uqj.random_seed = random_seed
        uqj.save()
    return uqj
