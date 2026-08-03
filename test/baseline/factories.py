"""
Shared fixture helpers for the baseline API / auth / permission suite.

Self-contained on purpose: nothing here imports from ``test.base`` or from the
other baseline modules, so it can be dropped on a Python 3.14 / Django 6 stack
unchanged.

Keep the fixtures SMALL: ``MyUser.save()`` and ``Question.save()`` both call
``ensure_uqj``, which creates one ``UserQuestionJunction`` per
(user, question) pair.  ``build_world()`` deliberately stays at 5 users x 6
questions.
"""

from django.utils import timezone

from accounts.models import MyUser, UserConsent
from canvas.models.goal import Goal, GoalItem
from canvas.models.models import (
    CanvasCourse,
    CanvasCourseRegistration,
    Event,
    EventSet,
    TokenUse,
    TokenUseOption,
)
from canvas.models.team import Team
from course.models.java import JavaQuestion
from course.models.models import QuestionCategory, TokenValue, UserQuestionJunction
from course.models.multiple_choice import MultipleChoiceQuestion, MultipleChoiceSubmission
from course.models.parsons import ParsonsQuestion
from general.models.action import Action, ActionObjectType, ActionStatus, ActionVerb
from general.models.faq import FAQ
from general.models.page_view import PageView
from general.models.question_report import QuestionReport
from general.models.survey import Survey

# Long enough for MinimumLengthValidator and not all-numeric, so it also works
# if a code path ever runs it through validate_password.
PASSWORD = "baseline-pass-1234"

TEACHER_ROLE = "Teacher"
STUDENT_ROLE = "Student"


# --------------------------------------------------------------------------- #
# clients
# --------------------------------------------------------------------------- #
def api_client(user=None, raise_request_exception=True):
    """
    A fresh ``APIClient``.  ``raise_request_exception=False`` makes the Django
    test client return a 500 response instead of re-raising, which is what we
    need to pin the endpoints that are currently broken.
    """
    from rest_framework.test import APIClient

    client = APIClient()
    client.raise_request_exception = raise_request_exception
    if user is not None:
        client.force_authenticate(user=user)
    return client


# --------------------------------------------------------------------------- #
# users
# --------------------------------------------------------------------------- #
def make_user(
    username,
    role=STUDENT_ROLE,
    password=PASSWORD,
    email=None,
    first_name="",
    last_name="",
    nickname="",
    is_active=True,
):
    user = MyUser(
        username=username,
        email=email if email is not None else "{}@baseline.example.com".format(username),
        role=role,
        first_name=first_name,
        last_name=last_name,
        nickname=nickname,
        is_active=is_active,
    )
    user.set_password(password)
    user.save()
    return user


def make_student(username, **kwargs):
    kwargs.setdefault("role", STUDENT_ROLE)
    return make_user(username, **kwargs)


def make_teacher(username, **kwargs):
    kwargs.setdefault("role", TEACHER_ROLE)
    return make_user(username, **kwargs)


# --------------------------------------------------------------------------- #
# categories / token values
# --------------------------------------------------------------------------- #
def make_category(name, parent=None, description="baseline category"):
    category = QuestionCategory(name=name, description=description, parent=parent)
    category.save()
    return category


def make_token_value(category, difficulty="EASY", value=2.0):
    token_value = TokenValue(category=category, difficulty=difficulty, value=value)
    token_value.save()
    return token_value


# --------------------------------------------------------------------------- #
# courses / registrations / events
# --------------------------------------------------------------------------- #
def make_course(
    name="Baseline Course",
    instructor=None,
    allow_registration=True,
    visible_to_students=True,
    registration_mode="OPEN",
    registration_code=None,
    start_date=None,
    end_date=None,
):
    course = CanvasCourse(
        name=name,
        url="http://canvas.example.com",
        instructor=instructor,
        description="baseline course",
        allow_registration=allow_registration,
        visible_to_students=visible_to_students,
        registration_mode=registration_mode,
        registration_code=registration_code,
        start_date=start_date if start_date is not None else timezone.now() - timezone.timedelta(days=1),
        end_date=end_date if end_date is not None else timezone.now() + timezone.timedelta(days=10),
    )
    course.save()
    return course


def make_registration(course, user, status="VERIFIED", registration_type="STUDENT"):
    """
    Creates or updates the (course, user) registration.  Note that plenty of
    application code calls ``get_course_registration`` which silently creates a
    row, so always go through this helper rather than a bare ``create``.
    """
    registration, _ = CanvasCourseRegistration.objects.get_or_create(course=course, user=user)
    registration.status = status
    registration.registration_type = registration_type
    registration.save()
    return registration


def make_event(
    course,
    name="Baseline Event",
    type="ASSIGNMENT",
    count_for_tokens=False,
    author=None,
    start_date=None,
    end_date=None,
    featured=False,
    challenge_type=None,
    challenge_type_value=None,
    max_team_size=3,
):
    event = Event(
        name=name,
        type=type,
        course=course,
        author=author,
        count_for_tokens=count_for_tokens,
        featured=featured,
        challenge_type=challenge_type,
        challenge_type_value=challenge_type_value,
        max_team_size=max_team_size,
        start_date=start_date if start_date is not None else timezone.now() - timezone.timedelta(days=1),
        end_date=end_date if end_date is not None else timezone.now() + timezone.timedelta(days=10),
    )
    event.save()
    return event


def make_event_set(course, events=(), name="Baseline Event Set", tokens=5.0):
    event_set = EventSet(course=course, name=name, tokens=tokens)
    event_set.save()
    if events:
        event_set.events.set(list(events))
    return event_set


def make_team(event, registrations=(), name="Baseline Team", is_private=False):
    team = Team(event=event, name=name, is_private=is_private)
    team.save()
    if registrations:
        team.course_registrations.set(list(registrations))
    return team


def make_token_use_option(course, tokens_required=1.0, points_given=1, maximum_number_of_use=2):
    option = TokenUseOption(
        course=course,
        tokens_required=tokens_required,
        points_given=points_given,
        maximum_number_of_use=maximum_number_of_use,
        assignment_name="Baseline Assignment",
        assignment_id=1,
    )
    option.save()
    return option


def make_token_use(option, user, num_used=0):
    token_use = TokenUse(option=option, user=user, num_used=num_used)
    token_use.save()
    return token_use


# --------------------------------------------------------------------------- #
# questions
# --------------------------------------------------------------------------- #
def make_mcq(
    author,
    category,
    title="Baseline MCQ",
    text="What is the answer?",
    answer="a",
    choices=None,
    visible_distractor_count=1,
    difficulty="EASY",
    is_verified=True,
    is_sample=False,
    max_submission_allowed=999,
    event=None,
    course=None,
    variables=None,
):
    question = MultipleChoiceQuestion(
        title=title,
        text=text,
        answer=answer,
        max_submission_allowed=max_submission_allowed,
        tutorial="baseline tutorial",
        author=author,
        category=category,
        difficulty=difficulty,
        is_verified=is_verified,
        is_sample=is_sample,
        variables=variables if variables is not None else [],
        choices=choices if choices is not None else {"a": "first", "b": "second"},
        visible_distractor_count=visible_distractor_count,
        course=course,
        event=event,
    )
    question.save()
    return question


def make_java_question(
    author,
    category,
    title="Baseline Java",
    text="Write some Java",
    difficulty="EASY",
    is_verified=True,
    max_submission_allowed=5,
    event=None,
    course=None,
    input_files=None,
    junit_template="",
    variables=None,
):
    question = JavaQuestion(
        title=title,
        text=text,
        max_submission_allowed=max_submission_allowed,
        tutorial="baseline tutorial",
        author=author,
        category=category,
        difficulty=difficulty,
        is_verified=is_verified,
        junit_template=junit_template,
        input_files=(
            input_files
            if input_files is not None
            else [{"name": "Main.java", "compile": True, "template": "", "hidden": False}]
        ),
        variables=variables if variables is not None else [],
        course=course,
        event=event,
    )
    question.save()
    return question


def make_parsons_question(
    author,
    category,
    title="Baseline Parsons",
    text="Order the lines",
    difficulty="EASY",
    is_verified=True,
    max_submission_allowed=5,
    event=None,
    course=None,
    input_files=None,
    junit_template="",
    variables=None,
):
    question = ParsonsQuestion(
        title=title,
        text=text,
        max_submission_allowed=max_submission_allowed,
        tutorial="baseline tutorial",
        author=author,
        category=category,
        difficulty=difficulty,
        is_verified=is_verified,
        junit_template=junit_template,
        input_files=(
            input_files
            if input_files is not None
            else [{"name": "Main.java", "compile": True, "lines": ["int a = 1;", "int b = 2;"]}]
        ),
        variables=variables if variables is not None else [],
        course=course,
        event=event,
    )
    question.save()
    return question


def get_uqj(user, question):
    """The UQJ row that ``ensure_uqj`` has already created for this pair."""
    return UserQuestionJunction.objects.get(user=user, question=question)


def make_mcq_submission(user, question, answer="a"):
    """
    Saves a MultipleChoiceSubmission directly (no HTTP).  ``Submission.save()``
    grades it, may write back UQJ tokens, and always creates an Action row.
    The MCQ grader is pure-python -- no network.
    """
    submission = MultipleChoiceSubmission(uqj=get_uqj(user, question), answer=answer)
    submission.save()
    return submission


# --------------------------------------------------------------------------- #
# goals
# --------------------------------------------------------------------------- #
def make_goal(course_reg, start_date=None, end_date=None, claimed=False):
    goal = Goal(
        course_reg=course_reg,
        start_date=start_date if start_date is not None else timezone.now() - timezone.timedelta(days=1),
        end_date=end_date if end_date is not None else timezone.now() + timezone.timedelta(days=7),
        claimed=claimed,
    )
    goal.save()
    return goal


def make_goal_item(goal, category, difficulty="EASY", number_of_questions=2):
    goal_item = GoalItem(
        goal=goal,
        category=category,
        difficulty=difficulty,
        initial_solved=0,
        number_of_questions=number_of_questions,
    )
    goal_item.save()
    return goal_item


# --------------------------------------------------------------------------- #
# general app
# --------------------------------------------------------------------------- #
def make_faq(question="Baseline question?", answer="Baseline answer."):
    faq = FAQ(question=question, answer=answer)
    faq.save()
    return faq


def make_survey(user, code="initial", response=None):
    survey = Survey(user=user, code=code, response=response if response is not None else {"q1": "a1"})
    survey.save()
    return survey


def make_page_view(user, url="/baseline/"):
    page_view = PageView(user=user, url=url)
    page_view.save()
    return page_view


def make_action(user, description="baseline action", token_change=0):
    action = Action(
        actor=user,
        description=description,
        token_change=token_change,
        status=ActionStatus.COMPLETE,
        verb=ActionVerb.LOGGED_IN,
        object_type=ActionObjectType.USER,
        object_id=user.id,
        data=None,
    )
    action.save()
    return action


def make_consent(user, consent=True):
    user_consent = UserConsent(
        user=user,
        consent=consent,
        access_submitted_course_work=consent,
        access_course_grades=consent,
        legal_first_name="Legal",
        legal_last_name="Name",
        gender="N/A",
        race="N/A",
        student_number="12345678",
    )
    user_consent.save()
    return user_consent


def make_question_report(user, question, report="OTHER", report_details="baseline report"):
    question_report = QuestionReport(user=user, question=question, report=report, report_details=report_details)
    question_report.save()
    return question_report


# --------------------------------------------------------------------------- #
# the world
# --------------------------------------------------------------------------- #
class World(object):
    """Plain attribute bag returned by :func:`build_world`."""


def build_world():
    """
    Builds one small but complete object graph covering every model the routed
    API endpoints need.  Users are created BEFORE questions so that
    ``Question.save()`` fans the UQJ rows out once, rather than the reverse.

    Roles:

    ==============  ==========  ==================================
    attribute       MyUser.role course registration
    ==============  ==========  ==================================
    ``teacher``     Teacher     none (role alone grants access)
    ``instructor``  Student     VERIFIED / INSTRUCTOR (+ owner)
    ``ta``          Student     VERIFIED / TA
    ``student``     Student     VERIFIED / STUDENT
    ``outsider``    Student     none
    ==============  ==========  ==================================
    """
    world = World()

    world.teacher = make_teacher("baseline_teacher", first_name="Terry", last_name="Teach", nickname="terry")
    world.instructor = make_student("baseline_instructor", first_name="Ingrid", last_name="Struct", nickname="ingrid")
    world.ta = make_student("baseline_ta", first_name="Tam", last_name="Assist", nickname="tam")
    world.student = make_student("baseline_student", first_name="Sam", last_name="Study", nickname="sam")
    world.outsider = make_student("baseline_outsider", first_name="Oli", last_name="Outside", nickname="oli")

    world.parent_category = make_category("Baseline Parent")
    world.category = make_category("Baseline Child", parent=world.parent_category)
    world.token_value = make_token_value(world.category, "EASY", 2.0)

    world.course = make_course(instructor=world.instructor)
    world.instructor_reg = make_registration(world.course, world.instructor, "VERIFIED", "INSTRUCTOR")
    world.ta_reg = make_registration(world.course, world.ta, "VERIFIED", "TA")
    world.student_reg = make_registration(world.course, world.student, "VERIFIED", "STUDENT")

    world.event = make_event(world.course, name="Baseline Event", author=world.instructor)
    world.event_set = make_event_set(world.course, [world.event])
    world.team = make_team(world.event, [world.student_reg])
    world.token_use_option = make_token_use_option(world.course)

    world.practice_question = make_mcq(world.teacher, world.category, title="Practice MCQ")
    world.event_question = make_mcq(world.teacher, world.category, title="Event MCQ", event=world.event)
    world.sample_question = make_mcq(world.teacher, world.category, title="Sample MCQ", is_sample=True)
    world.java_question = make_java_question(world.teacher, world.category)
    world.parsons_question = make_parsons_question(world.teacher, world.category)
    world.student_question = make_mcq(world.student, world.category, title="Student MCQ", is_verified=False)

    world.uqj = get_uqj(world.student, world.practice_question)
    world.submission = make_mcq_submission(world.student, world.practice_question, "a")

    world.goal = make_goal(world.student_reg)
    world.goal_item = make_goal_item(world.goal, world.category)

    world.faq = make_faq()
    world.survey = make_survey(world.student)
    world.page_view = make_page_view(world.student)
    world.action = make_action(world.student)
    world.consent = make_consent(world.student)
    world.question_report = make_question_report(world.student, world.practice_question)

    return world
