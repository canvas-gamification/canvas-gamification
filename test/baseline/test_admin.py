"""Baseline tests for the Django admin registrations.

Driven from ``django.contrib.admin.site._registry`` so that any newly registered
model is covered automatically: for a superuser every changelist and every add
form must return 200.  Also pins ``QuestionAdmin.verify``.
"""

from django.contrib import admin
from django.test import TestCase
from django.urls import reverse

from course.admin import QuestionAdmin
from course.models.models import Question
from test.baseline.fixtures_grader import (
    create_category,
    create_java_question,
    create_superuser,
    create_user,
)


def registered_models():
    """(model, model_admin) for every model in the default admin site."""
    return sorted(
        admin.site._registry.items(),
        key=lambda item: (item[0]._meta.app_label, item[0]._meta.model_name),
    )


def admin_url(model, view_name):
    return reverse("admin:{}_{}_{}".format(model._meta.app_label, model._meta.model_name, view_name))


class AdminRegistrationTests(TestCase):
    """The registry itself -- if a model is added or dropped this test notices."""

    def test_expected_models_are_registered(self):
        names = sorted("{}.{}".format(m._meta.app_label, m._meta.model_name) for m in admin.site._registry)
        self.assertEqual(
            names,
            [
                "accounts.myuser",
                "accounts.userconsent",
                "analytics.submissionanalytics",
                "auth.group",
                # DRF 3.14+ registers authtoken.TokenProxy (a proxy of Token) in the admin
                # instead of authtoken.Token -- same table, same admin functionality, only
                # the registry label changed.
                "authtoken.tokenproxy",
                "canvas.canvascourse",
                "canvas.canvascourseregistration",
                "canvas.event",
                "canvas.eventset",
                "canvas.goal",
                "canvas.goalitem",
                "canvas.team",
                "canvas.tokenuse",
                "canvas.tokenuseoption",
                "course.javaquestion",
                "course.javasubmission",
                "course.multiplechoicequestion",
                "course.multiplechoicesubmission",
                "course.parsonsquestion",
                "course.parsonssubmission",
                "course.question",
                "course.questioncategory",
                "course.submission",
                "course.tokenvalue",
                "course.userquestionjunction",
                "course.variablequestion",
                "general.action",
                "general.contactus",
                "general.faq",
                "general.pageview",
                "general.questionreport",
                "general.survey",
            ],
        )

    def test_third_party_registrations(self):
        # django.contrib.auth registers Group (but not User, since AUTH_USER_MODEL
        # is accounts.MyUser and accounts/admin.py registers it itself), and DRF's
        # authtoken app registers a token model.  Permission is deliberately not exposed.
        # DRF 3.14+ registers authtoken.TokenProxy (a proxy of Token) rather than
        # authtoken.Token -- same table and admin behaviour, different registry label.
        labels = [m._meta.label_lower for m in admin.site._registry]
        self.assertIn("auth.group", labels)
        self.assertIn("authtoken.tokenproxy", labels)
        self.assertNotIn("auth.permission", labels)
        self.assertNotIn("auth.user", labels)


class AdminPagesTests(TestCase):
    """Every registered model's changelist and add form renders for a superuser."""

    @classmethod
    def setUpTestData(cls):
        cls.password = "aaaaaaaa"
        cls.admin_user = create_superuser("admin_baseline", cls.password)
        cls.category = create_category("Admin Category")
        # one question + one non-admin user so the changelists are not all empty
        cls.student = create_user("admin_student")
        cls.question = create_java_question(author=cls.admin_user, category=cls.category)

    def setUp(self):
        self.assertTrue(self.client.login(username="admin_baseline", password=self.password))

    def test_admin_index(self):
        self.assertEqual(self.client.get(reverse("admin:index")).status_code, 200)

    def test_every_changelist_returns_200(self):
        for model, _ in registered_models():
            with self.subTest(model=model._meta.label_lower):
                response = self.client.get(admin_url(model, "changelist"))
                self.assertEqual(response.status_code, 200)

    def test_every_add_form_returns_200(self):
        for model, _ in registered_models():
            with self.subTest(model=model._meta.label_lower):
                response = self.client.get(admin_url(model, "add"))
                self.assertEqual(response.status_code, 200)

    def test_every_changelist_search_and_filter_query_returns_200(self):
        # exercises list_filter / list_display rendering with a query string
        for model, _ in registered_models():
            with self.subTest(model=model._meta.label_lower):
                response = self.client.get(admin_url(model, "changelist"), {"o": "1"})
                self.assertEqual(response.status_code, 200)

    def test_change_form_for_an_existing_question_returns_200(self):
        url = reverse("admin:course_javaquestion_change", args=[self.question.pk])
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_anonymous_user_is_redirected_to_login(self):
        self.client.logout()
        response = self.client.get(admin_url(Question, "changelist"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("admin:login"), response["Location"])


class QuestionAdminVerifyActionTests(TestCase):
    """``QuestionAdmin.verify`` flips is_verified on the selected queryset."""

    @classmethod
    def setUpTestData(cls):
        cls.password = "aaaaaaaa"
        cls.admin_user = create_superuser("admin_verify", cls.password)
        cls.category = create_category("Verify Category")
        cls.question = create_java_question(author=cls.admin_user, category=cls.category, title="Needs verifying")

    def setUp(self):
        Question.objects.filter(pk=self.question.pk).update(is_verified=False)
        self.assertTrue(self.client.login(username="admin_verify", password=self.password))

    def test_verify_is_registered_as_an_action(self):
        self.assertIn("verify", QuestionAdmin.actions)

    def test_verify_called_directly_updates_the_queryset(self):
        model_admin = admin.site._registry[Question]
        model_admin.verify(None, Question.objects.filter(pk=self.question.pk))
        self.question.refresh_from_db()
        self.assertTrue(self.question.is_verified)

    def test_verify_through_the_changelist_post(self):
        response = self.client.post(
            admin_url(Question, "changelist"),
            {"action": "verify", "_selected_action": [str(self.question.pk)], "index": "0"},
        )
        self.assertEqual(response.status_code, 302)
        self.question.refresh_from_db()
        self.assertTrue(self.question.is_verified)

    def test_verify_only_touches_the_selected_rows(self):
        other = create_java_question(author=self.admin_user, category=self.category, title="Untouched")
        Question.objects.filter(pk=other.pk).update(is_verified=False)

        model_admin = admin.site._registry[Question]
        model_admin.verify(None, Question.objects.filter(pk=self.question.pk))

        self.question.refresh_from_db()
        other.refresh_from_db()
        self.assertTrue(self.question.is_verified)
        self.assertFalse(other.is_verified)

    def test_verify_returns_none(self):
        model_admin = admin.site._registry[Question]
        self.assertIsNone(model_admin.verify(None, Question.objects.none()))
