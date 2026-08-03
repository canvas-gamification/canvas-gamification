"""Self-contained fixture helpers for the reporting / export baseline tests.

These helpers are deliberately duplicated (rather than imported from other
baseline modules) so that this area of the suite has no cross-agent coupling.

Performance note: ``MyUser.save()`` and ``Question.save()`` both fan out and
create a ``UserQuestionJunction`` for every (user, question) pair, so every
fixture here is intentionally tiny.
"""

from django.utils import timezone

from accounts.models import MyUser, UserConsent
from canvas.models.models import CanvasCourse, CanvasCourseRegistration, Event, EventSet
from canvas.models.team import Team
from course.models.java import JavaQuestion
from course.models.models import QuestionCategory, Submission, TokenValue
from course.models.multiple_choice import MultipleChoiceQuestion, MultipleChoiceSubmission
from course.utils.utils import get_user_question_junction
from general.models.action import Action
from general.models.page_view import PageView
from general.models.survey import Survey

DEFAULT_PASSWORD = "baseline-pass-1234"


# --------------------------------------------------------------------------
# time helpers
# --------------------------------------------------------------------------


def past(days=10):
    return timezone.now() - timezone.timedelta(days=days)


def future(days=10):
    return timezone.now() + timezone.timedelta(days=days)


def set_auto_now_field(instance, **fields):
    """Overwrite ``auto_now_add`` / ``auto_now`` columns via a raw UPDATE.

    Needed because those fields ignore values assigned before ``save()``.
    """
    type(instance)._default_manager.filter(pk=instance.pk).update(**fields)
    instance.refresh_from_db()
    return instance


# --------------------------------------------------------------------------
# accounts
# --------------------------------------------------------------------------


def make_user(
    username,
    role="Student",
    first_name="",
    last_name="",
    nickname="",
    email=None,
    date_joined=None,
):
    user = MyUser(
        username=username,
        email=email if email is not None else "{}@example.com".format(username),
        role=role,
        first_name=first_name,
        last_name=last_name,
        nickname=nickname,
    )
    user.set_password(DEFAULT_PASSWORD)
    if date_joined is not None:
        user.date_joined = date_joined
    user.save()
    return user


def make_teacher(username="teacher", **kwargs):
    kwargs.setdefault("first_name", "Tina")
    kwargs.setdefault("last_name", "Teacher")
    kwargs.setdefault("nickname", "tina")
    return make_user(username, role="Teacher", **kwargs)


def make_student(username="student", **kwargs):
    return make_user(username, role="Student", **kwargs)


def make_consent(user, **kwargs):
    values = dict(
        consent=True,
        access_submitted_course_work=True,
        access_course_grades=True,
        legal_first_name="Legal",
        legal_last_name="Name",
        gender="MALE",
        race="N/A",
        student_number="00000001",
        date="2020-01-01",
    )
    values.update(kwargs)
    consent = UserConsent(user=user, **values)
    consent.save()
    return consent


def make_page_view(user, url="/questions", time_created=None):
    page_view = PageView(user=user, url=url)
    page_view.save()
    if time_created is not None:
        set_auto_now_field(page_view, time_created=time_created)
    return page_view


def make_survey(user, code="baseline", response=None, time_created=None):
    survey = Survey(user=user, code=code, response=response if response is not None else {"q1": "a"})
    survey.save()
    if time_created is not None:
        set_auto_now_field(survey, time_created=time_created)
    return survey


def make_action(user, description="baseline action", token_change=0, verb="LOGIN", time_created=None, **kwargs):
    action = Action(actor=user, description=description, token_change=token_change, verb=verb, **kwargs)
    action.save()
    if time_created is not None:
        set_auto_now_field(action, time_created=time_created)
    return action


# --------------------------------------------------------------------------
# course content
# --------------------------------------------------------------------------


def make_category(name="category", parent=None):
    category = QuestionCategory(name=name, description=name, parent=parent)
    category.save()
    return category


def make_token_value(category, difficulty, value):
    token_value = TokenValue(category=category, difficulty=difficulty, value=value)
    token_value.save()
    return token_value


def make_course(name="Baseline Course", instructor=None, **kwargs):
    values = dict(
        url="http://canvas.ubc.ca",
        allow_registration=True,
        visible_to_students=True,
        start_date=past(),
        end_date=future(),
    )
    values.update(kwargs)
    course = CanvasCourse(name=name, instructor=instructor, **values)
    course.save()
    return course


def make_event(course, name="Event", type="ASSIGNMENT", count_for_tokens=True, **kwargs):
    values = dict(
        featured=False,
        start_date=past(),
        end_date=future(),
    )
    values.update(kwargs)
    event = Event(course=course, name=name, type=type, count_for_tokens=count_for_tokens, **values)
    event.save()
    return event


def make_event_set(course, name="Set", tokens=5.0, events=()):
    event_set = EventSet(course=course, name=name, tokens=tokens)
    event_set.save()
    for event in events:
        event_set.events.add(event)
    return event_set


def register(course, user, status="VERIFIED", registration_type="STUDENT"):
    course_reg = CanvasCourseRegistration(
        course=course,
        user=user,
        status=status,
        registration_type=registration_type,
    )
    course_reg.save()
    return course_reg


def make_mcq(
    category,
    title="Question",
    answer="a",
    choices=None,
    visible_distractor_count=1,
    event=None,
    course=None,
    author=None,
    difficulty="EASY",
    is_verified=True,
    variables=None,
    max_submission_allowed=10,
    text="question text",
):
    question = MultipleChoiceQuestion(
        title=title,
        text=text,
        answer=answer,
        max_submission_allowed=max_submission_allowed,
        tutorial="tutorial",
        author=author,
        category=category,
        difficulty=difficulty,
        is_verified=is_verified,
        variables=[] if variables is None else variables,
        choices={"a": "A", "b": "B", "c": "C"} if choices is None else choices,
        visible_distractor_count=visible_distractor_count,
        course=course,
        event=event,
    )
    question.save()
    return question


def make_java_question(
    category,
    title="Java Question",
    event=None,
    course=None,
    author=None,
    difficulty="EASY",
    is_verified=True,
    variables=None,
    max_submission_allowed=5,
):
    question = JavaQuestion(
        title=title,
        text="java question text",
        max_submission_allowed=max_submission_allowed,
        tutorial="tutorial",
        author=author,
        category=category,
        difficulty=difficulty,
        is_verified=is_verified,
        variables=[] if variables is None else variables,
        junit_template="",
        input_files=[{"name": "A.java", "compile": True, "template": ""}],
        course=course,
        event=event,
    )
    question.save()
    return question


# --------------------------------------------------------------------------
# submissions / junctions
# --------------------------------------------------------------------------


def uqj_for(user, question):
    return get_user_question_junction(user, question)


def submit_mcq(user, question, answer):
    """Mirror ``course.services.submission.submit_mcq_solution`` without its
    permission checks: save the submission, then re-save the UQJ (the service
    does the same, because ``UQJ.save()`` inside ``Submission.save()`` runs
    before the submission row exists)."""
    uqj = get_user_question_junction(user, question)
    submission = MultipleChoiceSubmission(uqj=uqj, answer=answer)
    submission.save()
    uqj.save()
    uqj.refresh_from_db()
    return submission


def force_partially_solved(uqj):
    """Put a UQJ into the ``is_partially_solved`` state.

    The MCQ grader never returns ``is_correct=False`` together with a non-zero
    grade, so this state is unreachable through normal MCQ grading; we write it
    at the DB level instead.
    """
    submission = uqj.submissions.order_by("id").last()
    Submission.objects.filter(pk=submission.pk).update(
        is_correct=False,
        is_partially_correct=True,
        grade=0.5,
        finalized=True,
    )
    uqj.refresh_from_db()
    uqj.is_solved = False
    uqj.solved_at = None
    uqj.save()
    uqj.refresh_from_db()
    return uqj


def set_uqj_tokens(uqj, tokens_received, is_solved=None):
    """Set token/solved state directly, bypassing the grader."""
    fields = {"tokens_received": tokens_received}
    if is_solved is not None:
        fields["is_solved"] = is_solved
        fields["solved_at"] = timezone.now() if is_solved else None
    type(uqj)._default_manager.filter(pk=uqj.pk).update(**fields)
    uqj.refresh_from_db()
    return uqj


def make_team(event, name="Team", course_registrations=(), is_private=False):
    team = Team(event=event, name=name, is_private=is_private)
    team.save()
    for course_reg in course_registrations:
        team.course_registrations.add(course_reg)
    return team
