"""Baseline tests for the ``general`` app models and their API endpoints.

Covers Action, PageView, Survey, FAQ, ContactUs and QuestionReport behaviour that
``general/tests.py`` does NOT already cover (that file only smoke-tests the 20
``general/services/action.py`` wrappers).
"""

from unittest import mock

from django.core import mail
from django.db import IntegrityError, transaction
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from general.models.action import Action, ActionObjectType, ActionStatus, ActionVerb
from general.models.contact_us import ContactUs
from general.models.faq import FAQ
from general.models.page_view import PageView
from general.models.question_report import QuestionReport
from general.models.survey import Survey
from test.baseline.fixtures_accounts import make_category, make_mcq_question, make_teacher, make_user


class ActionModelTest(APITestCase):
    def setUp(self):
        super().setUp()
        self.user = make_user(username="action-user", email="action-user@example.com")

    def test_create_action_persists_every_field(self):
        Action.create_action(
            actor=self.user,
            description="a description",
            token_change=3.5,
            status=ActionStatus.COMPLETE,
            verb=ActionVerb.SUBMITTED,
            object_type=ActionObjectType.QUESTION,
            object_id=42,
            data={"answer": "a", "nested": {"x": [1, 2]}},
        )

        action = Action.objects.get(actor=self.user)
        self.assertEqual(action.description, "a description")
        self.assertEqual(action.token_change, 3.5)
        self.assertEqual(action.status, ActionStatus.COMPLETE)
        self.assertEqual(action.verb, ActionVerb.SUBMITTED)
        self.assertEqual(action.object_type, ActionObjectType.QUESTION)
        self.assertEqual(action.object_id, 42)
        # jsonfield round-trips nested structures.
        self.assertEqual(action.data, {"answer": "a", "nested": {"x": [1, 2]}})
        self.assertIsNotNone(action.time_created)
        self.assertIsNotNone(action.time_modified)

    def test_create_action_defaults(self):
        Action.create_action(
            actor=self.user,
            description="minimal",
            token_change=0,
            status=ActionStatus.PENDING,
            verb=ActionVerb.CLICKED,
        )

        action = Action.objects.get(actor=self.user)
        self.assertIsNone(action.object_type)
        self.assertIsNone(action.object_id)
        self.assertIsNone(action.data)

    def test_actions_reverse_accessor(self):
        for _ in range(3):
            Action.create_action(
                actor=self.user,
                description="x",
                token_change=1,
                status=ActionStatus.COMPLETE,
                verb=ActionVerb.CLICKED,
            )
        self.assertEqual(self.user.actions.count(), 3)

    def test_actions_cascade_on_user_delete(self):
        Action.create_action(
            actor=self.user,
            description="x",
            token_change=1,
            status=ActionStatus.COMPLETE,
            verb=ActionVerb.CLICKED,
        )
        self.user.delete()
        self.assertEqual(Action.objects.count(), 0)


class UserActionsEndpointTest(APITestCase):
    def setUp(self):
        super().setUp()
        self.user = make_user(username="ua-student", email="ua-student@example.com")
        self.other = make_user(username="ua-other", email="ua-other@example.com")
        self.url = reverse("api:user-actions-list")

    def _action(self, actor, verb=ActionVerb.CLICKED, token_change=0):
        Action.create_action(
            actor=actor,
            description="desc",
            token_change=token_change,
            status=ActionStatus.COMPLETE,
            verb=verb,
        )

    def test_list_requires_authentication(self):
        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_is_scoped_to_the_requesting_user_and_paginated(self):
        self._action(self.user)
        self._action(self.other)
        self.client.force_authenticate(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data.keys()), {"count", "next", "previous", "results"})
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(
            set(response.data["results"][0].keys()),
            {
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
            },
        )
        self.assertEqual(response.data["results"][0]["actor"], self.user.id)

    def test_query_fields_mixin_narrows_the_payload(self):
        self._action(self.user)
        self.client.force_authenticate(self.user)

        response = self.client.get(self.url, {"fields": "id,verb"})

        self.assertEqual(set(response.data["results"][0].keys()), {"id", "verb"})

    def test_ordering_query_param(self):
        self._action(self.user, verb=ActionVerb.CLICKED)
        self._action(self.user, verb=ActionVerb.SUBMITTED)
        self.client.force_authenticate(self.user)

        ascending = self.client.get(self.url, {"ordering": "id"}).data["results"]
        descending = self.client.get(self.url, {"ordering": "-id"}).data["results"]

        self.assertEqual([row["id"] for row in ascending], sorted(row["id"] for row in ascending))
        self.assertEqual([row["id"] for row in descending], list(reversed([row["id"] for row in ascending])))

    def test_retrieve_other_users_action_returns_404(self):
        self._action(self.other)
        other_action = Action.objects.get(actor=self.other)
        self.client.force_authenticate(self.user)

        response = self.client.get(reverse("api:user-actions-detail", args=[other_action.id]))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_forces_actor_to_the_request_user(self):
        self.client.force_authenticate(self.user)

        response = self.client.post(
            self.url,
            {
                "actor": self.other.id,
                "description": "client supplied",
                "status": ActionStatus.COMPLETE,
                "verb": ActionVerb.CLICKED,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Action.objects.get(description="client supplied").actor_id, self.user.id)

    def test_create_accepts_client_supplied_token_change(self):
        # KNOWN-BUG: ActionsSerializer has ``exclude = []`` and only ``actor`` is
        # read-only, so an authenticated client can POST an arbitrary ``token_change``
        # and mint tokens that show up in MyUser.tokens (api/views/action.py:13-45).
        self.client.force_authenticate(self.user)

        response = self.client.post(
            self.url,
            {
                "description": "free money",
                "token_change": 9999,
                "status": ActionStatus.COMPLETE,
                "verb": ActionVerb.CLICKED,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.user.tokens, 9999.0)

    def test_delete_is_not_routed(self):
        self._action(self.user)
        action = Action.objects.get(actor=self.user)
        self.client.force_authenticate(self.user)

        response = self.client.delete(reverse("api:user-actions-detail", args=[action.id]))

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class PageViewEndpointTest(APITestCase):
    def setUp(self):
        super().setUp()
        self.user = make_user(username="pv-student", email="pv-student@example.com")
        self.other = make_user(username="pv-other", email="pv-other@example.com")
        self.url = reverse("api:page-view-list")

    def test_requires_authentication(self):
        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self.client.post(self.url, {"url": "/x"}).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_forces_user_and_returns_the_full_field_set(self):
        self.client.force_authenticate(self.user)

        response = self.client.post(self.url, {"user": self.other.id, "url": "/questions/1"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(set(response.data.keys()), {"id", "user", "time_created", "url"})
        page_view = PageView.objects.get()
        self.assertEqual(page_view.user_id, self.user.id)
        self.assertEqual(page_view.url, "/questions/1")
        self.assertIsNotNone(page_view.time_created)

    def test_list_is_scoped_to_the_requesting_user(self):
        PageView.objects.create(user=self.user, url="/mine")
        PageView.objects.create(user=self.other, url="/theirs")
        self.client.force_authenticate(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["url"], "/mine")

    def test_page_views_cascade_on_user_delete(self):
        PageView.objects.create(user=self.user, url="/mine")
        self.user.delete()
        self.assertEqual(PageView.objects.count(), 0)


class SurveyEndpointTest(APITestCase):
    def setUp(self):
        super().setUp()
        self.user = make_user(username="survey-student", email="survey-student@example.com")
        self.teacher = make_teacher(username="survey-teacher", email="survey-teacher@example.com")
        self.url = reverse("api:survey-list")

    def test_requires_authentication(self):
        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_forces_user_and_stores_the_json_response(self):
        self.client.force_authenticate(self.user)

        response = self.client.post(
            self.url,
            {"code": "initial", "response": {"q1": "yes", "q2": [1, 2]}},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(set(response.data.keys()), {"user", "time_created", "code", "response"})
        survey = Survey.objects.get()
        self.assertEqual(survey.user_id, self.user.id)
        self.assertEqual(survey.code, "initial")
        self.assertEqual(survey.response, {"q1": "yes", "q2": [1, 2]})

    def test_create_replaces_an_existing_survey_with_the_same_code(self):
        self.client.force_authenticate(self.user)
        self.client.post(self.url, {"code": "initial", "response": {"v": 1}}, format="json")
        self.client.post(self.url, {"code": "initial", "response": {"v": 2}}, format="json")

        self.assertEqual(Survey.objects.filter(user=self.user, code="initial").count(), 1)
        self.assertEqual(Survey.objects.get(user=self.user, code="initial").response, {"v": 2})

    def test_create_does_not_replace_a_different_code(self):
        self.client.force_authenticate(self.user)
        self.client.post(self.url, {"code": "initial", "response": {"v": 1}}, format="json")
        self.client.post(self.url, {"code": "final", "response": {"v": 2}}, format="json")

        self.assertEqual(Survey.objects.filter(user=self.user).count(), 2)

    def test_create_without_code_returns_400(self):
        # SurveyViewSet.perform_create reads request.data["code"] directly
        # (api/views/survey.py:186), but the serializer's required `code` field rejects
        # the payload first, so the unguarded lookup is not reachable through the API.
        self.client.force_authenticate(self.user)

        response = self.client.post(self.url, {"response": {"v": 1}}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("code", response.data)
        self.assertEqual(Survey.objects.count(), 0)

    def test_list_is_scoped_for_students_and_unscoped_for_teachers(self):
        Survey.objects.create(user=self.user, code="initial", response={})
        Survey.objects.create(user=self.teacher, code="initial", response={})

        self.client.force_authenticate(self.user)
        self.assertEqual(len(self.client.get(self.url).data), 1)

        self.client.force_authenticate(self.teacher)
        self.assertEqual(len(self.client.get(self.url).data), 2)

    def test_list_filters_on_code_and_user(self):
        Survey.objects.create(user=self.user, code="initial", response={})
        Survey.objects.create(user=self.user, code="final", response={})
        self.client.force_authenticate(self.user)

        self.assertEqual(len(self.client.get(self.url, {"code": "final"}).data), 1)
        self.assertEqual(len(self.client.get(self.url, {"user": self.user.id}).data), 2)

    def test_check_endpoint_always_returns_a_null_code(self):
        # The real logic is commented out (api/views/survey.py:201-211).
        self.client.force_authenticate(self.user)
        Survey.objects.create(user=self.user, code="final", response={})

        response = self.client.get(reverse("api:survey-check-survey"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"code": None})


class FAQEndpointTest(APITestCase):
    def setUp(self):
        super().setUp()
        self.faq = FAQ.objects.create(question="What is this?", answer="A baseline test.")
        self.url = reverse("api:faq-list")

    def test_list_is_public(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(set(response.data[0].keys()), {"question", "answer"})

    def test_retrieve_is_public(self):
        response = self.client.get(reverse("api:faq-detail", args=[self.faq.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"question": "What is this?", "answer": "A baseline test."})

    def test_is_read_only(self):
        response = self.client.post(self.url, {"question": "q", "answer": "a"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class ContactUsEndpointTest(APITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("api:contact-us-list")
        ok = mock.Mock()
        ok.json.return_value = {"success": True}
        patcher = mock.patch("utils.recaptcha.requests.post", return_value=ok)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_create_is_public_and_sends_an_email(self):
        response = self.client.post(
            self.url,
            {"fullname": "Ada", "email": "ada@example.com", "comment": "hi", "recaptcha_key": "tok"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # recaptcha_key is write_only and popped in create().
        self.assertEqual(set(response.data.keys()), {"fullname", "email", "comment"})
        self.assertEqual(ContactUs.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Contact Us Question")

    def test_missing_fields_return_400_and_send_nothing(self):
        response = self.client.post(self.url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(set(response.data.keys()), {"fullname", "email", "comment", "recaptcha_key"})
        self.assertEqual(ContactUs.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_list_is_not_routed(self):
        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class QuestionReportEndpointTest(APITestCase):
    def setUp(self):
        super().setUp()
        self.user = make_user(username="qr-student", email="qr-student@example.com")
        self.teacher = make_teacher(username="qr-teacher", email="qr-teacher@example.com")
        self.category = make_category()
        self.question = make_mcq_question(author=self.teacher, category=self.category)
        self.url = reverse("api:question-report-list")

    def test_requires_authentication(self):
        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_sets_user_sends_email_and_logs_an_action(self):
        self.client.force_authenticate(self.user)

        response = self.client.post(
            self.url,
            {"question": self.question.id, "report": "TYPO_TEXT", "report_details": "line 2"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            set(response.data.keys()),
            {"id", "question", "created_at", "updated_at", "report", "report_details"},
        )
        report = QuestionReport.objects.get()
        self.assertEqual(report.user_id, self.user.id)
        self.assertEqual(report.question_id, self.question.id)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "A question was reported")
        self.assertTrue(
            Action.objects.filter(
                actor=self.user, verb=ActionVerb.CREATED, object_type=ActionObjectType.QUESTION
            ).exists()
        )

    def test_duplicate_report_for_the_same_question_raises_integrity_error(self):
        # KNOWN-BUG: QuestionReport has unique_together ("user", "question") but
        # QuestionReportSerializer does not expose ``user``, so DRF cannot build a
        # UniqueTogetherValidator. A second report therefore escapes validation and
        # blows up at the database layer with an IntegrityError (HTTP 500) instead of
        # returning 400.
        QuestionReport.objects.create(user=self.user, question=self.question, report="OTHER")
        self.client.force_authenticate(self.user)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.client.post(self.url, {"question": self.question.id, "report": "OTHER"}, format="json")

        self.assertEqual(QuestionReport.objects.count(), 1)

    def test_invalid_report_choice_is_rejected(self):
        self.client.force_authenticate(self.user)

        response = self.client.post(self.url, {"question": self.question.id, "report": "NOT_A_CHOICE"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("report", response.data)
        self.assertEqual(len(mail.outbox), 0)

    def test_students_see_only_their_own_reports_teachers_see_all(self):
        QuestionReport.objects.create(user=self.user, question=self.question, report="OTHER")
        QuestionReport.objects.create(user=self.teacher, question=self.question, report="OTHER")

        self.client.force_authenticate(self.user)
        self.assertEqual(len(self.client.get(self.url).data), 1)

        self.client.force_authenticate(self.teacher)
        self.assertEqual(len(self.client.get(self.url).data), 2)

    def test_report_cascades_on_question_delete(self):
        QuestionReport.objects.create(user=self.user, question=self.question, report="OTHER")
        self.question.delete()
        self.assertEqual(QuestionReport.objects.count(), 0)
