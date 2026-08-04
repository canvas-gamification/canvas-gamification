"""Exact field-name-set snapshots for the main serializers.

Silent field drift is the most common DRF-upgrade regression, so every assertion here
is an exact ``set`` comparison rather than a subset check. Values are only asserted
where they are cheap and stable; the point of this file is the *shape*.

The six submission serializers are covered by a sibling baseline module and are
deliberately not repeated here.
"""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import UserConsent
from api.serializers import (
    ActionsSerializer,
    CanvasCourseRegistrationSerializer,
    ChangePasswordSerializer,
    ContactUsSerializer,
    CourseListSerializer,
    CourseSerializer,
    EventSerializer,
    FAQSerializer,
    JavaQuestionSerializer,
    MultipleChoiceQuestionSerializer,
    ParsonsQuestionSerializer,
    QuestionCategorySerializer,
    QuestionReportSerializer,
    QuestionSerializer,
    ResetPasswordSerializer,
    TokenUseOptionSerializer,
    TokenUseSerializer,
    TokenValueSerializer,
    UpdateProfileSerializer,
    UQJSerializer,
    UserConsentSerializer,
    UserRegistrationSerializer,
)
from api.serializers.course import CourseCreateSerializer
from api.serializers.eventSet import EventSetSerializer
from api.serializers.page_view import PageViewSerializer
from api.serializers.survey import SurveySerializer
from api.serializers.user import UserSerializer
from canvas.models.models import EventSet, TokenUseOption
from general.models.action import Action, ActionStatus, ActionVerb
from general.models.faq import FAQ
from general.models.page_view import PageView
from general.models.question_report import QuestionReport
from general.models.survey import Survey
from test.baseline.fixtures_accounts import (
    make_category,
    make_course,
    make_event,
    make_mcq_question,
    make_teacher,
    make_user,
)

# ---------------------------------------------------------------------------
# Expected field-name sets (baseline snapshots).
# ---------------------------------------------------------------------------

QUESTION_FIELDS = {
    "id",
    "title",
    "text",
    "max_submission_allowed",
    "time_created",
    "time_modified",
    "author",
    "author_name",
    "difficulty",
    "is_verified",
    "token_value",
    "type_name",
    "event",
    "event_obj",
    "category",
    "parent_category_name",
    "full_category_name",
    "category_name",
    "course",
    "status",
    "is_sample",
    "is_open",
    "is_exam",
    "is_exam_and_open",
    "is_author",
    "is_practice",
}

UQJ_FIELDS = {
    "id",
    "last_viewed",
    "opened_tutorial",
    "tokens_received",
    "is_solved",
    "is_partially_solved",
    "question",
    "question_id",
    "num_attempts",
    "status",
    "formatted_current_tokens_received",
    "is_allowed_to_submit",
    "variables",
    "variables_errors",
    "rendered_text",
    "rendered_choices",
    "rendered_lines",
    "input_files",
    "is_checkbox",
    "report",
    "is_favorite",
}

EVENT_FIELDS = {
    "id",
    "name",
    "type",
    "count_for_tokens",
    "start_date",
    "end_date",
    "course",
    "author",
    "is_allowed_to_open",
    "has_edit_permission",
    "is_open",
    "is_exam",
    "total_tokens",
    "total_event_grade",
    "is_not_available_yet",
    "is_closed",
    "max_team_size",
    "featured",
    "challenge_type",
    "challenge_type_value",
    "has_solved_event",
}

# CourseSerializer declares registration_code write_only, so it is absent from output.
COURSE_INPUT_FIELDS = {
    "id",
    "name",
    "url",
    "allow_registration",
    "visible_to_students",
    "start_date",
    "end_date",
    "instructor",
    "status",
    "is_registered",
    "token_use_options",
    "events",
    "course_reg",
    "has_create_event_permission",
    "has_create_challenge_permission",
    "has_view_permission",
    "description",
    "registration_mode",
    "registration_code",
    "secret_registration_code",
}
COURSE_OUTPUT_FIELDS = COURSE_INPUT_FIELDS - {"registration_code"}

COURSE_LIST_FIELDS = {
    "id",
    "name",
    "url",
    "allow_registration",
    "visible_to_students",
    "start_date",
    "end_date",
    "instructor",
    "status",
    "is_registered",
    "events",
    "description",
    "registration_mode",
    "has_view_permission",
}

COURSE_CREATE_FIELDS = {
    "id",
    "name",
    "description",
    "url",
    "start_date",
    "end_date",
    "registration_mode",
    "registration_code",
}

USER_FIELDS = {"first_name", "last_name", "username", "email", "role", "date_joined"}

UPDATE_PROFILE_FIELDS = {"id", "first_name", "last_name", "email", "nickname"}

USER_CONSENT_FIELDS = {
    "user",
    "consent",
    "legal_first_name",
    "legal_last_name",
    "student_number",
    "date",
    "access_submitted_course_work",
    "access_course_grades",
    "is_student",
    "gender",
    "race",
}

ACTION_FIELDS = {
    "id",
    "time_created",
    "time_modified",
    "actor",
    "description",
    "token_change",
    "status",
    "verb",
    "object_type",
    "object_id",
    "data",
}

PAGE_VIEW_FIELDS = {"id", "user", "time_created", "url"}
SURVEY_FIELDS = {"user", "time_created", "code", "response"}
FAQ_FIELDS = {"question", "answer"}
QUESTION_REPORT_FIELDS = {"id", "question", "created_at", "updated_at", "report", "report_details"}
CONTACT_US_INPUT_FIELDS = {"fullname", "email", "comment", "recaptcha_key"}
CONTACT_US_OUTPUT_FIELDS = CONTACT_US_INPUT_FIELDS - {"recaptcha_key"}


def _input_fields(serializer_class):
    return set(serializer_class().fields.keys())


class SerializerShapeTestCase(APITestCase):
    """Shared minimal object graph. Only two users and one question: MyUser.save() and
    Question.save() both fan out UserQuestionJunction rows."""

    def setUp(self):
        super().setUp()
        self.teacher = make_teacher(username="shape-teacher", email="shape-teacher@example.com")
        self.student = make_user(username="shape-student", email="shape-student@example.com")
        self.category = make_category()
        self.course = make_course(instructor=self.teacher)
        self.event = make_event(self.course)
        self.question = make_mcq_question(author=self.teacher, category=self.category, event=self.event)
        self.uqj = self.student.question_junctions.get(question=self.question)
        # KNOWN-BUG: canvas/utils/utils.py:6-14 (get_total_event_tokens) feeds a category
        # *id* into course/utils/utils.py:47-59 (get_token_value_object), which does
        # ``TokenValue(category=<int>)`` when the row does not exist yet -> ValueError,
        # so Event.total_tokens (and therefore EventSerializer / CourseSerializer) 500s
        # until some other code path has created the TokenValue row. Reading
        # Question.token_value passes a real model instance and creates it.
        self.token_value = self.question.token_value


class QuestionSerializerShapeTest(SerializerShapeTestCase):
    def test_question_serializer_output_fields(self):
        data = QuestionSerializer(self.question).data
        self.assertEqual(set(data.keys()), QUESTION_FIELDS)

    def test_question_serializer_input_fields(self):
        self.assertEqual(_input_fields(QuestionSerializer), QUESTION_FIELDS)

    def test_question_serializer_without_request_context_defaults(self):
        data = QuestionSerializer(self.question).data
        # get_uqj_status / get_is_author both short-circuit when there is no request.
        self.assertEqual(data["status"], "")
        self.assertFalse(data["is_author"])
        self.assertEqual(data["id"], self.question.id)
        self.assertEqual(data["type_name"], "multiple choice question")

    def test_question_serializer_nests_the_full_event_serializer(self):
        data = QuestionSerializer(self.question).data
        self.assertEqual(set(data["event_obj"].keys()), EVENT_FIELDS)

    def test_multiple_choice_question_serializer_fields(self):
        expected = {
            "id",
            "title",
            "text",
            "answer",
            "max_submission_allowed",
            "time_created",
            "time_modified",
            "author",
            "author_name",
            "difficulty",
            "is_verified",
            "token_value",
            "type_name",
            "event",
            "event_obj",
            "category",
            "category_obj",
            "parent_category_name",
            "course",
            "is_sample",
            "choices",
            "variables",
            "variation_types",
            "visible_distractor_count",
            "is_checkbox",
        }
        self.assertEqual(_input_fields(MultipleChoiceQuestionSerializer), expected)
        self.assertEqual(set(MultipleChoiceQuestionSerializer(self.question).data.keys()), expected)

    def test_java_question_serializer_fields(self):
        self.assertEqual(
            _input_fields(JavaQuestionSerializer),
            {
                "id",
                "title",
                "text",
                "answer",
                "max_submission_allowed",
                "time_created",
                "time_modified",
                "author",
                "author_name",
                "difficulty",
                "is_verified",
                "token_value",
                "type_name",
                "event",
                "event_obj",
                "category",
                "category_obj",
                "parent_category_name",
                "course",
                "is_sample",
                "variables",
                "variation_types",
                "junit_template",
                "input_files",
            },
        )

    def test_parsons_question_serializer_fields(self):
        # NOTE: unlike the Java/MCQ variants this one also exposes category_name and
        # event_name.
        self.assertEqual(
            _input_fields(ParsonsQuestionSerializer),
            {
                "id",
                "title",
                "text",
                "answer",
                "max_submission_allowed",
                "time_created",
                "time_modified",
                "author",
                "author_name",
                "difficulty",
                "is_verified",
                "token_value",
                "type_name",
                "event",
                "event_obj",
                "event_name",
                "category",
                "category_obj",
                "category_name",
                "parent_category_name",
                "course",
                "is_sample",
                "variables",
                "variation_types",
                "junit_template",
                "input_files",
            },
        )

    def test_question_category_serializer_fields(self):
        expected = {"pk", "name", "description", "parent", "full_name", "question_count", "next_category_ids"}
        self.assertEqual(_input_fields(QuestionCategorySerializer), expected)
        self.assertEqual(set(QuestionCategorySerializer(self.category).data.keys()), expected)


class UQJSerializerShapeTest(SerializerShapeTestCase):
    def test_uqj_serializer_output_fields(self):
        data = UQJSerializer(self.uqj).data
        self.assertEqual(set(data.keys()), UQJ_FIELDS)

    def test_uqj_serializer_input_fields(self):
        self.assertEqual(_input_fields(UQJSerializer), UQJ_FIELDS)

    def test_uqj_serializer_nests_the_question_serializer(self):
        data = UQJSerializer(self.uqj).data
        self.assertEqual(set(data["question"].keys()), QUESTION_FIELDS)

    def test_uqj_serializer_method_field_types(self):
        data = UQJSerializer(self.uqj).data
        self.assertEqual(data["variables"], {})
        self.assertEqual(data["variables_errors"], [])
        # get_lines() returns {} for non-Parsons questions despite the "lines" name.
        self.assertEqual(data["rendered_lines"], {})
        self.assertEqual(data["input_files"], [])
        # No QuestionReport for this user/question pair yet.
        self.assertEqual(data["report"], {})
        self.assertEqual(set(data["rendered_choices"].keys()), {"a", "b"})

    def test_uqj_report_field_uses_the_question_report_serializer(self):
        QuestionReport.objects.create(user=self.student, question=self.question, report="OTHER")
        data = UQJSerializer(self.uqj).data
        self.assertEqual(set(data["report"].keys()), QUESTION_REPORT_FIELDS)


class CourseAndEventSerializerShapeTest(SerializerShapeTestCase):
    def test_course_serializer_fields(self):
        self.assertEqual(_input_fields(CourseSerializer), COURSE_INPUT_FIELDS)
        self.assertEqual(set(CourseSerializer(self.course).data.keys()), COURSE_OUTPUT_FIELDS)

    def test_course_serializer_anonymous_defaults(self):
        data = CourseSerializer(self.course).data
        # Without a request the serializer falls back to MyAnonymousUser.
        self.assertFalse(data["is_registered"])
        self.assertIsNone(data["course_reg"])
        self.assertFalse(data["has_create_event_permission"])
        self.assertFalse(data["has_create_challenge_permission"])
        self.assertFalse(data["has_view_permission"])
        self.assertFalse(data["secret_registration_code"])

    def test_course_serializer_nests_events_and_token_use_options(self):
        TokenUseOption.objects.create(
            course=self.course, tokens_required=1, points_given=1, assignment_name="A1", assignment_id=1
        )
        data = CourseSerializer(self.course).data

        self.assertEqual(len(data["events"]), 1)
        self.assertEqual(set(data["events"][0].keys()), EVENT_FIELDS)
        self.assertEqual(len(data["token_use_options"]), 1)
        self.assertEqual(
            set(data["token_use_options"][0].keys()),
            {
                "id",
                "course",
                "tokens_required",
                "points_given",
                "maximum_number_of_use",
                "assignment_name",
                "assignment_id",
            },
        )

    def test_course_list_serializer_fields(self):
        self.assertEqual(_input_fields(CourseListSerializer), COURSE_LIST_FIELDS)
        self.assertEqual(set(CourseListSerializer(self.course).data.keys()), COURSE_LIST_FIELDS)

    def test_course_create_serializer_fields(self):
        self.assertEqual(_input_fields(CourseCreateSerializer), COURSE_CREATE_FIELDS)
        self.assertEqual(set(CourseCreateSerializer(self.course).data.keys()), COURSE_CREATE_FIELDS)

    def test_event_serializer_fields(self):
        self.assertEqual(_input_fields(EventSerializer), EVENT_FIELDS)
        self.assertEqual(set(EventSerializer(self.event).data.keys()), EVENT_FIELDS)

    def test_event_serializer_anonymous_defaults(self):
        data = EventSerializer(self.event).data
        self.assertFalse(data["is_allowed_to_open"])
        self.assertFalse(data["has_edit_permission"])
        self.assertFalse(data["has_solved_event"])
        self.assertEqual(data["total_event_grade"], 0)

    def test_event_set_serializer_fields(self):
        event_set = EventSet.objects.create(name="set-1", course=self.course, tokens=5)
        event_set.events.add(self.event)

        expected = {"id", "name", "course", "events", "tokens", "has_earn_tokens"}
        self.assertEqual(_input_fields(EventSetSerializer), expected)

        data = EventSetSerializer(event_set).data
        self.assertEqual(set(data.keys()), expected)
        self.assertEqual(set(data["events"][0].keys()), EVENT_FIELDS)

    def test_canvas_course_registration_serializer_fields(self):
        from canvas.utils.utils import get_course_registration

        course_reg = get_course_registration(self.student, self.course)
        expected = {
            "id",
            "canvas_user_id",
            "status",
            "is_verified",
            "is_blocked",
            "token_uses",
            "available_tokens",
            "username",
            "name",
        }
        self.assertEqual(_input_fields(CanvasCourseRegistrationSerializer), expected)
        self.assertEqual(set(CanvasCourseRegistrationSerializer(course_reg).data.keys()), expected)

    def test_token_use_serializers_fields(self):
        self.assertEqual(_input_fields(TokenUseSerializer), {"option", "num_used"})
        self.assertEqual(
            _input_fields(TokenUseOptionSerializer),
            {
                "id",
                "course",
                "tokens_required",
                "points_given",
                "maximum_number_of_use",
                "assignment_name",
                "assignment_id",
            },
        )

    def test_token_value_serializer_fields(self):
        self.assertEqual(_input_fields(TokenValueSerializer), {"pk", "category", "difficulty", "value"})


class AccountSerializerShapeTest(SerializerShapeTestCase):
    def test_user_serializer_fields(self):
        self.assertEqual(_input_fields(UserSerializer), USER_FIELDS)
        self.assertEqual(set(UserSerializer(self.student).data.keys()), USER_FIELDS)

    def test_update_profile_serializer_fields(self):
        self.assertEqual(_input_fields(UpdateProfileSerializer), UPDATE_PROFILE_FIELDS)
        self.assertEqual(set(UpdateProfileSerializer(self.student).data.keys()), UPDATE_PROFILE_FIELDS)

    def test_user_consent_serializer_fields(self):
        consent = UserConsent.objects.create(
            user=self.student,
            consent=True,
            legal_first_name="Legal",
            legal_last_name="Name",
            student_number="12345",
            date="2026-01-01",
        )
        self.assertEqual(_input_fields(UserConsentSerializer), USER_CONSENT_FIELDS)
        self.assertEqual(set(UserConsentSerializer(consent).data.keys()), USER_CONSENT_FIELDS)

    def test_user_registration_serializer_fields(self):
        self.assertEqual(
            _input_fields(UserRegistrationSerializer),
            {"email", "first_name", "last_name", "nickname", "password", "password2", "recaptcha_key"},
        )
        self.assertEqual(
            {name for name, field in UserRegistrationSerializer().fields.items() if field.write_only},
            {"password", "password2", "recaptcha_key"},
        )

    def test_reset_password_serializer_fields_are_all_write_only(self):
        fields = ResetPasswordSerializer().fields
        self.assertEqual(set(fields.keys()), {"uid", "token", "password", "password2"})
        self.assertTrue(all(field.write_only for field in fields.values()))

    def test_change_password_serializer_fields_are_all_write_only(self):
        fields = ChangePasswordSerializer().fields
        self.assertEqual(set(fields.keys()), {"old_password", "password", "password2"})
        self.assertTrue(all(field.write_only for field in fields.values()))


class GeneralAppSerializerShapeTest(SerializerShapeTestCase):
    def test_actions_serializer_fields(self):
        Action.create_action(
            actor=self.student,
            description="d",
            token_change=0,
            status=ActionStatus.COMPLETE,
            verb=ActionVerb.CLICKED,
        )
        self.assertEqual(_input_fields(ActionsSerializer), ACTION_FIELDS)
        self.assertEqual(set(ActionsSerializer(Action.objects.get()).data.keys()), ACTION_FIELDS)

    def test_page_view_serializer_fields(self):
        page_view = PageView.objects.create(user=self.student, url="/x")
        self.assertEqual(_input_fields(PageViewSerializer), PAGE_VIEW_FIELDS)
        self.assertEqual(set(PageViewSerializer(page_view).data.keys()), PAGE_VIEW_FIELDS)

    def test_survey_serializer_fields(self):
        survey = Survey.objects.create(user=self.student, code="initial", response={"a": 1})
        self.assertEqual(_input_fields(SurveySerializer), SURVEY_FIELDS)
        self.assertEqual(set(SurveySerializer(survey).data.keys()), SURVEY_FIELDS)

    def test_faq_serializer_fields(self):
        faq = FAQ.objects.create(question="q", answer="a")
        self.assertEqual(_input_fields(FAQSerializer), FAQ_FIELDS)
        self.assertEqual(set(FAQSerializer(faq).data.keys()), FAQ_FIELDS)

    def test_question_report_serializer_fields(self):
        report = QuestionReport.objects.create(user=self.student, question=self.question, report="OTHER")
        self.assertEqual(_input_fields(QuestionReportSerializer), QUESTION_REPORT_FIELDS)
        self.assertEqual(set(QuestionReportSerializer(report).data.keys()), QUESTION_REPORT_FIELDS)

    def test_contact_us_serializer_fields(self):
        self.assertEqual(_input_fields(ContactUsSerializer), CONTACT_US_INPUT_FIELDS)


class ResponsePayloadShapeTest(SerializerShapeTestCase):
    """The same snapshots, but observed through the HTTP layer (context + pagination)."""

    def test_uqj_list_payload(self):
        self.client.force_authenticate(self.student)

        response = self.client.get(reverse("api:uqj-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data.keys()), {"count", "next", "previous", "results"})
        row = response.data["results"][0]
        self.assertEqual(set(row.keys()), UQJ_FIELDS)
        self.assertEqual(set(row["question"].keys()), QUESTION_FIELDS)
        # With a request in context QuestionSerializer.status resolves the real UQJ status.
        self.assertEqual(row["question"]["status"], "New")

    def test_question_list_payload_uses_the_base_question_serializer(self):
        self.client.force_authenticate(self.teacher)

        response = self.client.get(reverse("api:question-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data["results"][0].keys()), QUESTION_FIELDS)

    def test_question_detail_payload_uses_the_polymorphic_serializer(self):
        self.client.force_authenticate(self.teacher)

        response = self.client.get(reverse("api:question-detail", args=[self.question.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("choices", response.data)
        self.assertIn("visible_distractor_count", response.data)
        self.assertNotIn("status", response.data)

    def test_course_detail_payload(self):
        self.client.force_authenticate(self.student)

        response = self.client.get(reverse("api:course-detail", args=[self.course.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data.keys()), COURSE_OUTPUT_FIELDS)
        self.assertEqual(set(response.data["course_reg"].keys()), CanvasCourseRegistrationSerializer().fields.keys())

    def test_course_list_payload(self):
        self.client.force_authenticate(self.student)

        response = self.client.get(reverse("api:course-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data[0].keys()), COURSE_LIST_FIELDS)

    def test_event_detail_payload(self):
        self.client.force_authenticate(self.teacher)

        response = self.client.get(reverse("api:event-detail", args=[self.event.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data.keys()), EVENT_FIELDS)

    def test_update_profile_payload(self):
        self.client.force_authenticate(self.student)

        response = self.client.get(reverse("api:update-profile-detail", args=[self.student.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data.keys()), UPDATE_PROFILE_FIELDS)
