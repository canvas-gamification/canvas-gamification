"""Self-contained fixture helpers for the canvas-app baseline tests.

Deliberately does not import from any other baseline test module so that the
canvas baseline suite stays independent.  Everything here builds *small*
object graphs: ``MyUser.save()`` and ``Question.save()`` both fan out a
``UserQuestionJunction`` per (user, question) pair, so every extra user or
question multiplies the row count.

Only stdlib / Django / app APIs that exist on both Django 3.0 and Django 6.0
are used (``django.utils.timezone``, no ``zoneinfo``, no ``pytz``).
"""

from django.utils import timezone

from accounts.models import STUDENT, TEACHER, MyUser
from canvas.models.models import (
    CanvasCourse,
    CanvasCourseRegistration,
    Event,
    EventSet,
    TokenUse,
    TokenUseOption,
)
from canvas.models.team import Team
from course.models.models import DIFFICULTY_CHOICES, QuestionCategory, UserQuestionJunction
from course.models.multiple_choice import MultipleChoiceQuestion
from course.utils.utils import get_token_value_object

DEFAULT_PASSWORD = "aaaaaaaa1234"


def days(n):
    """Timezone-aware datetime ``n`` days from now (negative == in the past)."""
    return timezone.now() + timezone.timedelta(days=n)


def make_user(username, role=STUDENT, nickname=None, first_name="", last_name=""):
    user = MyUser.objects.create_user(
        username=username,
        email="{}@example.com".format(username),
        password=DEFAULT_PASSWORD,
    )
    user.role = role
    user.nickname = nickname if nickname is not None else username
    user.first_name = first_name
    user.last_name = last_name
    user.save()
    return user


def make_teacher(username="teacher", **kwargs):
    return make_user(username, role=TEACHER, **kwargs)


def make_category(name="category"):
    category = QuestionCategory(name=name, description=name)
    category.save()
    return category


def ensure_token_values(category):
    """Create the three TokenValue rows for a category (EASY=1, MEDIUM=2, HARD=3).

    ``get_total_event_tokens`` (canvas/utils/utils.py:6-14) passes a *category
    id* into ``get_token_value``, which blows up when the row has to be created
    (see the ValueError pinned in test_events.py).  Pre-creating the rows keeps
    unrelated tests off that landmine.
    """
    return [get_token_value_object(category, difficulty) for difficulty, _ in DIFFICULTY_CHOICES]


def make_course(
    name="Test Course",
    instructor=None,
    registration_mode="OPEN",
    registration_code=None,
    start_offset=-1,
    end_offset=10,
    allow_registration=True,
    visible_to_students=True,
):
    course = CanvasCourse(
        name=name,
        url="http://canvas.ubc.ca",
        instructor=instructor,
        registration_mode=registration_mode,
        registration_code=registration_code,
        allow_registration=allow_registration,
        visible_to_students=visible_to_students,
        start_date=days(start_offset),
        end_date=days(end_offset),
    )
    course.save()
    return course


def make_event(
    course,
    name="event",
    type="ASSIGNMENT",
    count_for_tokens=True,
    start_offset=-1,
    end_offset=10,
    challenge_type=None,
    challenge_type_value=None,
    max_team_size=3,
    author=None,
    featured=False,
):
    event = Event(
        name=name,
        type=type,
        course=course,
        count_for_tokens=count_for_tokens,
        challenge_type=challenge_type,
        challenge_type_value=challenge_type_value,
        max_team_size=max_team_size,
        author=author,
        featured=featured,
        start_date=days(start_offset),
        end_date=days(end_offset),
    )
    event.save()
    return event


def make_event_set(course, name="set", tokens=10.0, events=()):
    event_set = EventSet(name=name, course=course, tokens=tokens)
    event_set.save()
    if events:
        event_set.events.set(list(events))
    return event_set


def make_registration(user, course, status="VERIFIED", registration_type="STUDENT"):
    """Create/refresh the registration row without going through the API."""
    course_reg, _ = CanvasCourseRegistration.objects.get_or_create(user=user, course=course)
    course_reg.status = status
    course_reg.registration_type = registration_type
    course_reg.save()
    return course_reg


def make_question(
    category,
    title="title",
    event=None,
    course=None,
    difficulty="EASY",
    is_verified=True,
    author=None,
    answer="a",
    choices=None,
    ensure_token_value=True,
):
    """A minimal saved MultipleChoiceQuestion.

    ``event=None`` and ``course=None`` (the default) makes it a *practice*
    question, which is what ``total_tokens_received`` counts.
    """
    question = MultipleChoiceQuestion(
        title=title,
        text="text",
        answer=answer,
        max_submission_allowed=10,
        tutorial="tutorial",
        author=author,
        category=category,
        difficulty=difficulty,
        is_verified=is_verified,
        variables=[],
        choices=choices if choices is not None else {"a": "a", "b": "b"},
        visible_distractor_count=1,
        course=course,
        event=event,
    )
    question.save()
    if ensure_token_value:
        get_token_value_object(category, difficulty)
    return question


def set_uqj(user, question, tokens_received=0.0, is_solved=False):
    """Set the token/solved state of the (already auto-created) UQJ row."""
    uqj = UserQuestionJunction.objects.get(user=user, question=question)
    uqj.tokens_received = tokens_received
    uqj.is_solved = is_solved
    if is_solved and uqj.solved_at is None:
        uqj.solved_at = timezone.now()
    uqj.save()
    return uqj


def make_team(event, name, course_regs=(), is_private=False, who_can_join=()):
    team = Team(event=event, name=name, is_private=is_private)
    team.save()
    if course_regs:
        team.course_registrations.set(list(course_regs))
    if who_can_join:
        team.who_can_join.set(list(who_can_join))
    return team


def make_token_use_option(course, tokens_required=2.0, points_given=1, maximum_number_of_use=1, assignment_name="a1"):
    option = TokenUseOption(
        course=course,
        tokens_required=tokens_required,
        points_given=points_given,
        maximum_number_of_use=maximum_number_of_use,
        assignment_name=assignment_name,
    )
    option.save()
    return option


def make_token_use(user, option, num_used=1):
    token_use = TokenUse(user=user, option=option, num_used=num_used)
    token_use.save()
    return token_use
