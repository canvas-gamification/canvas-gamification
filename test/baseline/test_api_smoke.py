"""
Baseline smoke tests for every routed API endpoint.

For each URL registered in ``api/urls.py`` we send one request per role
(anonymous / student / teacher / instructor) and pin the EXACT status code that
the current stack (Python 3.8, Django 3.0.14, DRF 3.11.2) returns.  The point is
regression detection across the Django 6 / DRF upgrade, not correctness -- where
the current behaviour is wrong it is marked ``# KNOWN-BUG:`` and pinned anyway.

``test_every_routed_url_name_is_covered`` walks the router registry so that a
route added later cannot silently escape the matrix.

Every request is wrapped in a savepoint that is rolled back afterwards, because
a surprising number of GET endpoints write to the database
(``get_course_registration``, ``get_token_values``, ``Event.update_featured``).
"""

import logging

from django.db import transaction
from django.urls import reverse
from rest_framework.test import APITestCase

try:
    from unittest import mock
except ImportError:  # pragma: no cover - Python 2 style fallback, never taken
    import mock

from test.baseline import factories

ROLES = ("anonymous", "student", "teacher", "instructor")

# ``pk`` values are resolved against the attributes of the object built by
# ``factories.build_world()``.  "self" means "the id of the requesting user".
#
# name, url kwargs, anonymous, student, teacher, instructor
GET_SMOKE = [
    ("openapi-schema", {}, 200, 200, 200, 200),
    ("docs", {}, 200, 200, 200, 200),
    ("token-auth", {}, 405, 405, 405, 405),
    ("api-root", {}, 200, 200, 200, 200),
    # -- questions ---------------------------------------------------------
    ("question-list", {}, 401, 200, 200, 200),
    ("question-download-questions", {}, 401, 200, 200, 200),
    ("question-detail", {"pk": "practice_question"}, 401, 200, 200, 200),
    ("question-get-favorite-count", {"pk": "practice_question"}, 401, 200, 200, 200),
    # no permission_classes -> public
    ("sample-multiple-choice-question-list", {}, 200, 200, 200, 200),
    ("sample-multiple-choice-question-detail", {"pk": "sample_question"}, 200, 200, 200, 200),
    ("multiple-choice-question-list", {}, 401, 200, 200, 200),
    ("multiple-choice-question-detail", {"pk": "practice_question"}, 401, 200, 200, 200),
    ("java-question-list", {}, 401, 200, 200, 200),
    ("java-question-detail", {"pk": "java_question"}, 401, 200, 200, 200),
    ("parsons-question-list", {}, 401, 200, 200, 200),
    ("parsons-question-detail", {"pk": "parsons_question"}, 401, 200, 200, 200),
    ("question-category-list", {}, 200, 200, 200, 200),
    ("question-category-detail", {"pk": "category"}, 200, 200, 200, 200),
    ("difficulty-list", {}, 200, 200, 200, 200),
    # -- uqj ---------------------------------------------------------------
    ("uqj-list", {}, 401, 200, 200, 200),
    ("uqj-get-question-ids", {}, 401, 200, 200, 200),
    ("uqj-detail", {"pk": "uqj"}, 401, 200, 404, 404),
    ("uqj-get-by-question", {"pk": "practice_question"}, 401, 200, 200, 200),
    ("uqj-update-update-is-favorite", {}, 401, 405, 405, 405),
    # -- submissions -------------------------------------------------------
    # ?question= is required; without it get_object_or_404(Question, id=None) 404s.
    ("submission-list", {}, 401, 404, 404, 404),
    ("submission-submit", {}, 401, 405, 405, 405),
    # KNOWN-BUG: SubmissionViewSet.retrieve uses get_object_or_404 directly instead
    # of self.get_object(), so HasViewSubmissionPermission.has_object_permission is
    # never called -- any authenticated user can read anybody's submission.
    ("submission-detail", {"pk": "submission"}, 401, 200, 200, 200),
    # -- courses -----------------------------------------------------------
    ("course-list", {}, 401, 200, 200, 200),
    ("course-detail", {"pk": "course"}, 401, 200, 200, 200),
    # KNOWN-BUG: CourseViewSet.course_event_sets reads ``course.eventSets`` but the
    # related_name is ``event_sets`` -> AttributeError -> 500 for every role.
    ("course-course-event-sets", {"pk": "course"}, 401, 500, 500, 500),
    ("course-course-grade-book", {"pk": "course"}, 401, 403, 200, 200),
    ("course-course-registrations", {"pk": "course"}, 401, 200, 200, 200),
    ("course-export-grade-book", {"pk": "course"}, 401, 403, 200, 200),
    ("course-leader-board", {"pk": "course"}, 401, 200, 200, 200),
    # KNOWN-BUG: my_grades raises a bare ValueError (not an APIException) when the
    # caller has no VERIFIED STUDENT registration -> 500 instead of 403/404.
    ("course-my-grades", {"pk": "course"}, 401, 200, 500, 500),
    ("course-register", {"pk": "course"}, 401, 405, 405, 405),
    ("course-user-stats", {"pk": "course", "category_pk": "category"}, 401, 200, 200, 200),
    ("course-validate-event", {"pk": "course", "event_pk": "event"}, 401, 200, 200, 200),
    ("course-registration-list", {}, 401, 200, 200, 200),
    ("course-registration-detail", {"pk": "student_reg"}, 401, 200, 404, 404),
    ("admin-course-update-status", {}, 401, 403, 405, 403),
    # The functionality map lists this as broken (a generator is passed to
    # Response).  It is NOT broken for the JSON renderer: DRF's JSONEncoder turns
    # any object with __iter__ into a list, so it returns 200 with valid JSON.
    ("admin-course-registered-users", {"pk": "course"}, 401, 403, 200, 403),
    # -- events ------------------------------------------------------------
    ("event-list", {}, 401, 200, 200, 200),
    ("event-detail", {"pk": "event"}, 401, 200, 200, 200),
    ("event-get-challenge-types", {}, 401, 200, 200, 200),
    ("event-get-event-types", {}, 401, 200, 200, 200),
    ("event-import-event", {}, 401, 405, 405, 405),
    ("event-limits", {}, 401, 200, 200, 200),
    ("event-add-question", {"pk": "event"}, 401, 405, 405, 405),
    ("event-add-question-set", {"pk": "event"}, 401, 405, 405, 405),
    ("event-clear-featured", {"pk": "event"}, 401, 405, 405, 405),
    ("event-set-featured", {"pk": "event"}, 401, 405, 405, 405),
    ("event-remove-question", {"pk": "event"}, 401, 405, 405, 405),
    ("event-leader-board", {"pk": "event"}, 401, 200, 200, 200),
    ("event-stats", {"pk": "event"}, 401, 200, 200, 200),
    ("event-set-view-list", {}, 401, 200, 200, 200),
    ("event-set-view-detail", {"pk": "event_set"}, 401, 200, 200, 200),
    # -- teams -------------------------------------------------------------
    # TeamPermission.has_permission is hardcoded True, so the list route is public.
    ("team-list", {}, 200, 200, 200, 200),
    ("team-create-and-join", {}, 405, 405, 405, 405),
    ("team-join", {}, 405, 405, 405, 405),
    ("team-my-team", {}, 404, 404, 404, 404),
    # KNOWN-BUG: TeamPermission.has_permission returns True even for AnonymousUser,
    # then has_object_permission filters course_registrations by an AnonymousUser
    # -> TypeError -> 500 instead of 401.
    ("team-detail", {"pk": "team"}, 500, 200, 403, 403),
    # -- goals -------------------------------------------------------------
    ("goal-list", {}, 401, 200, 200, 200),
    ("goal-limits", {}, 401, 200, 200, 200),
    ("goal-suggestions", {}, 401, 200, 200, 200),
    ("goal-detail", {"pk": "goal"}, 401, 200, 404, 404),
    ("goal-claim", {"pk": "goal"}, 401, 405, 405, 405),
    ("goal-stats", {"pk": "goal"}, 401, 200, 404, 404),
    ("goal-item-list", {}, 401, 200, 200, 200),
    ("goal-item-detail", {"pk": "goal_item"}, 401, 200, 404, 404),
    # -- tokens ------------------------------------------------------------
    ("token-values-list", {}, 401, 403, 200, 403),
    ("token-values-nested", {}, 401, 403, 200, 403),
    ("token-values-detail", {"pk": "token_value"}, 401, 403, 200, 403),
    ("token-values-update-bulk", {}, 401, 403, 405, 403),
    ("token-use-use-tokens", {"course_pk": "course"}, 401, 405, 405, 405),
    # -- users / auth / profile -------------------------------------------
    ("user-consent-list", {}, 401, 200, 200, 200),
    # teacher: the object is in the queryset but is not theirs -> 403.
    # instructor: the queryset is filtered to their own consents -> 404.
    ("user-consent-detail", {"pk": "consent"}, 401, 200, 403, 404),
    ("contact-us-list", {}, 405, 405, 405, 405),
    ("register-list", {}, 405, 405, 405, 405),
    ("register-activate", {}, 405, 405, 405, 405),
    ("reset-password-list", {}, 405, 405, 405, 405),
    ("reset-password-send-email", {}, 405, 405, 405, 405),
    ("change-password-list", {}, 401, 405, 405, 405),
    ("update-profile-list", {}, 401, 200, 200, 200),
    ("update-profile-detail", {"pk": "self"}, 401, 200, 200, 200),
    ("user-stats-list", {}, 401, 200, 200, 200),
    ("user-stats-difficulty", {"category_pk": "category"}, 401, 200, 200, 200),
    ("user-stats-detail", {"pk": "self"}, 401, 200, 200, 200),
    ("user-actions-list", {}, 401, 200, 200, 200),
    ("user-actions-detail", {"pk": "action"}, 401, 200, 404, 404),
    ("page-view-list", {}, 401, 200, 200, 200),
    ("page-view-detail", {"pk": "page_view"}, 401, 200, 404, 404),
    ("survey-list", {}, 401, 200, 200, 200),
    ("survey-check-survey", {}, 401, 200, 200, 200),
    ("question-report-list", {}, 401, 200, 200, 200),
    ("question-report-detail", {"pk": "question_report"}, 401, 200, 200, 404),
    ("faq-list", {}, 200, 200, 200, 200),
    ("faq-detail", {"pk": "faq"}, 200, 200, 200, 200),
    # -- admin / export ----------------------------------------------------
    ("admin-list", {}, 401, 403, 200, 403),
    ("admin-category-stats", {}, 401, 403, 200, 403),
    ("admin-courses", {}, 401, 403, 200, 403),
    ("admin-question-count", {}, 401, 403, 200, 403),
    ("export-action-list", {}, 401, 403, 200, 403),
    ("export-consent-list", {}, 401, 403, 200, 403),
    ("export-page-view-list", {}, 401, 403, 200, 403),
    ("export-survey-list", {}, 401, 403, 200, 403),
    ("export-user-list", {}, 401, 403, 200, 403),
]

# The write-only routes only answer 405 to GET, so they are smoke tested a second
# time with their real verb and an EMPTY body.  Full-body behaviour lives in
# test_permissions.py.
#
# name, url kwargs, http method, anonymous, student, teacher, instructor
POST_SMOKE = [
    ("contact-us-list", {}, "post", 400, 400, 400, 400),
    ("register-list", {}, "post", 400, 400, 400, 400),
    ("register-activate", {}, "post", 400, 400, 400, 400),
    ("reset-password-list", {}, "post", 400, 400, 400, 400),
    ("reset-password-send-email", {}, "post", 404, 404, 404, 404),
    ("change-password-list", {}, "post", 401, 400, 400, 400),
    ("course-register", {"pk": "course"}, "post", 401, 200, 200, 200),
    ("submission-submit", {}, "post", 401, 400, 400, 400),
    ("event-import-event", {}, "post", 401, 404, 404, 404),
    ("event-add-question", {"pk": "event"}, "post", 401, 404, 404, 404),
    ("event-add-question-set", {"pk": "event"}, "post", 401, 200, 200, 200),
    ("event-remove-question", {"pk": "event"}, "post", 401, 404, 404, 404),
    ("event-clear-featured", {"pk": "event"}, "post", 401, 200, 200, 200),
    ("event-set-featured", {"pk": "event"}, "post", 401, 200, 200, 200),
    ("token-use-use-tokens", {"course_pk": "course"}, "post", 401, 400, 400, 400),
    ("token-values-update-bulk", {}, "patch", 401, 403, 200, 403),
    ("admin-course-update-status", {}, "post", 401, 403, 404, 403),
    ("uqj-update-update-is-favorite", {}, "post", 401, 404, 404, 404),
    ("team-create-and-join", {}, "post", 404, 404, 404, 404),
    ("team-join", {}, "post", 404, 404, 404, 404),
    ("goal-claim", {"pk": "goal"}, "post", 401, 400, 404, 404),
]


class SmokeTestCaseBase(APITestCase):
    def setUp(self):
        super(SmokeTestCaseBase, self).setUp()
        # No network, ever: both live-HTTP call sites are replaced.
        recaptcha_patch = mock.patch("utils.recaptcha.requests")
        grader_patch = mock.patch("course.grader.grader.requests")
        self.recaptcha_requests = recaptcha_patch.start()
        self.grader_requests = grader_patch.start()
        self.addCleanup(recaptcha_patch.stop)
        self.addCleanup(grader_patch.stop)
        self.recaptcha_requests.post.return_value.json.return_value = {"success": True}

        # Several endpoints are currently 500s; keep their tracebacks out of the
        # test output.
        logging.disable(logging.CRITICAL)
        self.addCleanup(logging.disable, logging.NOTSET)

        self.world = factories.build_world()

    def user_for(self, role):
        if role == "anonymous":
            return None
        return getattr(self.world, role)

    def url_for(self, name, kwargs_spec, user):
        kwargs = {}
        for key, token in kwargs_spec.items():
            if token == "self":
                kwargs[key] = user.id if user is not None else 0
            else:
                kwargs[key] = getattr(self.world, token).id
        return reverse("api:" + name, kwargs=kwargs)

    def request(self, role, name, kwargs_spec, method="get"):
        """Issues one request inside a savepoint that is rolled back afterwards."""
        user = self.user_for(role)
        client = factories.api_client(user=user, raise_request_exception=False)
        url = self.url_for(name, kwargs_spec, user)
        sid = transaction.savepoint()
        try:
            if method == "get":
                response = client.get(url)
            else:
                response = getattr(client, method)(url, {}, format="json")
        finally:
            transaction.savepoint_rollback(sid)
        return response


class ApiGetSmokeTest(SmokeTestCaseBase):
    def _run(self, role):
        index = ROLES.index(role)
        for row in GET_SMOKE:
            name, kwargs_spec = row[0], row[1]
            expected = row[2 + index]
            with self.subTest(route=name, role=role):
                response = self.request(role, name, kwargs_spec)
                self.assertEqual(
                    expected,
                    response.status_code,
                    "GET {} as {}".format(name, role),
                )

    def test_get_smoke_anonymous(self):
        self._run("anonymous")

    def test_get_smoke_student(self):
        self._run("student")

    def test_get_smoke_teacher(self):
        self._run("teacher")

    def test_get_smoke_instructor(self):
        self._run("instructor")


class ApiWriteSmokeTest(SmokeTestCaseBase):
    def _run(self, role):
        index = ROLES.index(role)
        for row in POST_SMOKE:
            name, kwargs_spec, method = row[0], row[1], row[2]
            expected = row[3 + index]
            with self.subTest(route=name, role=role, method=method):
                response = self.request(role, name, kwargs_spec, method=method)
                self.assertEqual(
                    expected,
                    response.status_code,
                    "{} {} as {} with an empty body".format(method.upper(), name, role),
                )

    def test_write_smoke_anonymous(self):
        self._run("anonymous")

    def test_write_smoke_student(self):
        self._run("student")

    def test_write_smoke_teacher(self):
        self._run("teacher")

    def test_write_smoke_instructor(self):
        self._run("instructor")


class RouteCoverageTest(APITestCase):
    """Drives the assertion that the smoke matrix keeps up with api/urls.py."""

    def routed_names(self):
        from api.urls import urlpatterns

        names = set()
        for pattern in urlpatterns:
            # DefaultRouter registers a ``.json``-style twin for every route.
            if "format" in str(pattern.pattern):
                continue
            names.add(pattern.name)
        return names

    def test_every_routed_url_name_is_covered(self):
        covered = set(row[0] for row in GET_SMOKE)
        routed = self.routed_names()
        self.assertEqual(
            set(),
            routed - covered,
            "new routes are missing from GET_SMOKE",
        )
        self.assertEqual(
            set(),
            covered - routed,
            "GET_SMOKE names routes that no longer exist",
        )

    def test_write_smoke_names_are_real_routes(self):
        self.assertEqual(set(), set(row[0] for row in POST_SMOKE) - self.routed_names())

    def test_router_registry_is_unchanged(self):
        from api.urls import router

        self.assertEqual(
            [
                "questions",
                "sample-multiple-choice-question",
                "multiple-choice-question",
                "java-question",
                "parsons-question",
                "user-consent",
                "contact-us",
                "question-category",
                "token-values",
                "user-stats",
                "user-actions",
                "uqj",
                "faq",
                "course",
                "course-registration",
                "change-password",
                "reset-password",
                "register",
                "update-profile",
                "submission",
                "event",
                "token-use",
                "difficulty",
                "admin",
                "course-admin",
                "uqj-update",
                "question-report",
                "team",
                "goal",
                "goal-item",
                "page-view",
                "survey",
                "export/page-view",
                "export/action",
                "event-set",
                "export/consent",
                "export/user",
                "export/survey",
            ],
            [prefix for prefix, viewset, basename in router.registry],
        )

    def test_root_urlconf_shape(self):
        """
        The root URLconf branches on ``settings.DEBUG`` at import time, and the
        Django test runner forces ``DEBUG = False``, so under the test runner the
        PRODUCTION branch is always active: no ``/api-auth/`` and an Angular
        catch-all that swallows unknown paths.
        """
        from django.conf import settings
        from django.urls import resolve

        self.assertFalse(settings.DEBUG)
        self.assertEqual("admin:index", resolve("/admin/").view_name)
        self.assertEqual("api:api-root", resolve("/api/").view_name)
        self.assertEqual("canvas_gamification.views.angular", resolve("/anything-else/").view_name)


class KnownBrokenEndpointTest(SmokeTestCaseBase):
    """The 500s above, asserted as real exceptions rather than as status codes."""

    def test_course_event_sets_raises_attribute_error(self):
        # KNOWN-BUG: api/views/course.py course_event_sets() uses
        # ``course.eventSets``; EventSet's related_name is ``event_sets``.
        client = factories.api_client(user=self.world.teacher)
        url = reverse("api:course-course-event-sets", kwargs={"pk": self.world.course.id})
        with self.assertRaises(AttributeError):
            client.get(url)

    def test_my_grades_raises_value_error_without_a_student_registration(self):
        # KNOWN-BUG: api/views/course.py my_grades() raises a bare ValueError,
        # which DRF does not translate into a 4xx.
        client = factories.api_client(user=self.world.teacher)
        url = reverse("api:course-my-grades", kwargs={"pk": self.world.course.id})
        with self.assertRaises(ValueError):
            client.get(url)

    def test_my_grades_succeeds_for_a_registered_student(self):
        client = factories.api_client(user=self.world.student)
        url = reverse("api:course-my-grades", kwargs={"pk": self.world.course.id})
        response = client.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.data))
        self.assertEqual(
            {"grade", "total", "name", "event_name", "question_details"},
            set(response.data[0].keys()),
        )

    def test_team_detail_blows_up_for_anonymous_users(self):
        # KNOWN-BUG: TeamPermission.has_permission is hardcoded to True, so an
        # AnonymousUser reaches the object-level filter and explodes.
        client = factories.api_client()
        url = reverse("api:team-detail", kwargs={"pk": self.world.team.id})
        with self.assertRaises(TypeError):
            client.get(url)

    def test_registered_users_returns_a_generator_that_the_json_renderer_flattens(self):
        # The generator handed to Response() renders fine as JSON (DRF's
        # JSONEncoder calls tuple() on anything iterable) -- pinned because the
        # encoder's fallback is exactly the kind of thing an upgrade changes.
        client = factories.api_client(user=self.world.teacher)
        url = reverse("api:admin-course-registered-users", kwargs={"pk": self.world.course.id})
        response = client.get(url)
        self.assertEqual(200, response.status_code)
        payload = response.json()
        self.assertIsInstance(payload, list)
        self.assertEqual(3, len(payload))


class SmokeSideEffectTest(SmokeTestCaseBase):
    """A couple of read endpoints that write; pinned because they are load-bearing."""

    def test_course_list_creates_a_registration_row_for_the_caller(self):
        from canvas.models.models import CanvasCourseRegistration

        before = CanvasCourseRegistration.objects.count()
        client = factories.api_client(user=self.world.outsider)
        self.assertEqual(200, client.get(reverse("api:course-list")).status_code)
        self.assertEqual(before + 1, CanvasCourseRegistration.objects.count())
        self.assertEqual(
            "UNREGISTERED",
            CanvasCourseRegistration.objects.get(user=self.world.outsider, course=self.world.course).status,
        )

    def test_token_values_list_creates_missing_token_value_rows(self):
        from course.models.models import TokenValue

        TokenValue.objects.all().delete()
        client = factories.api_client(user=self.world.teacher)
        response = client.get(reverse("api:token-values-list"))
        self.assertEqual(200, response.status_code)
        # one row per (non-root category, difficulty)
        self.assertEqual(3, TokenValue.objects.count())
