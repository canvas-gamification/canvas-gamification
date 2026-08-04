"""
Baseline permission matrix for every custom permission class in
``api/permissions.py``.

Six callers are exercised against each guarded endpoint:

``anonymous``   not authenticated
``outsider``    role=Student, no registration in the course
``student``     role=Student, VERIFIED / STUDENT registration
``ta``          role=Student, VERIFIED / TA registration
``instructor``  role=Student, VERIFIED / INSTRUCTOR registration, owns the course
``teacher``     role=Teacher, no registration (the role alone is the bypass)

Each request runs inside a savepoint that is rolled back afterwards, so the six
roles never see each other's writes and the matrices stay order-independent.

Where the current behaviour is a security or robustness bug it is flagged with
``# KNOWN-BUG:`` and pinned as-is -- this suite exists to detect CHANGE, not to
bless the behaviour.
"""

import logging

from django.db import transaction
from django.urls import reverse
from rest_framework.test import APITestCase

try:
    from unittest import mock
except ImportError:  # pragma: no cover
    import mock

from test.baseline import factories

ROLES = ("anonymous", "outsider", "student", "ta", "instructor", "teacher")

ALL_AUTHENTICATED_ALLOWED = {
    "anonymous": 401,
    "outsider": 200,
    "student": 200,
    "ta": 200,
    "instructor": 200,
    "teacher": 200,
}

TEACHER_ONLY = {
    "anonymous": 401,
    "outsider": 403,
    "student": 403,
    "ta": 403,
    "instructor": 403,
    "teacher": 200,
}

COURSE_STAFF_ONLY = {
    "anonymous": 401,
    "outsider": 403,
    "student": 403,
    "ta": 200,
    "instructor": 200,
    "teacher": 200,
}

INSTRUCTOR_ONLY = {
    "anonymous": 401,
    "outsider": 403,
    "student": 403,
    "ta": 403,
    "instructor": 200,
    "teacher": 200,
}


class PermissionTestCase(APITestCase):
    def setUp(self):
        super(PermissionTestCase, self).setUp()
        recaptcha_patch = mock.patch("utils.recaptcha.requests")
        grader_patch = mock.patch("course.grader.grader.requests")
        recaptcha_patch.start()
        grader_patch.start()
        self.addCleanup(recaptcha_patch.stop)
        self.addCleanup(grader_patch.stop)

        logging.disable(logging.CRITICAL)
        self.addCleanup(logging.disable, logging.NOTSET)

        self.world = factories.build_world()

    def user_for(self, role):
        if role == "anonymous":
            return None
        return getattr(self.world, role)

    def call(self, role, method, url, body=None):
        client = factories.api_client(user=self.user_for(role), raise_request_exception=False)
        if method in ("get", "delete"):
            return getattr(client, method)(url)
        return getattr(client, method)(url, body if body is not None else {}, format="json")

    def assert_matrix(self, method, url, expected, body=None, label=None):
        """
        ``expected`` maps role -> status code.  ``body`` may be a dict or a
        callable taking the role (useful when a payload must stay unique).
        """
        for role in ROLES:
            with self.subTest(role=role, method=method, url=label or url):
                sid = transaction.savepoint()
                try:
                    payload = body(role) if callable(body) else body
                    response = self.call(role, method, url, payload)
                    self.assertEqual(
                        expected[role],
                        response.status_code,
                        "{} {} as {}".format(method.upper(), label or url, role),
                    )
                finally:
                    transaction.savepoint_rollback(sid)


# --------------------------------------------------------------------------- #
# TeacherAccessPermission
# --------------------------------------------------------------------------- #
class TeacherAccessPermissionTest(PermissionTestCase):
    def test_admin_and_export_and_token_value_endpoints_are_teacher_only(self):
        urls = [
            reverse("api:admin-list"),
            reverse("api:admin-question-count"),
            reverse("api:admin-category-stats"),
            reverse("api:admin-courses"),
            reverse("api:admin-course-registered-users", kwargs={"pk": self.world.course.id}),
            reverse("api:token-values-list"),
            reverse("api:token-values-nested"),
            reverse("api:token-values-detail", kwargs={"pk": self.world.token_value.id}),
            reverse("api:export-action-list"),
            reverse("api:export-consent-list"),
            reverse("api:export-page-view-list"),
            reverse("api:export-survey-list"),
            reverse("api:export-user-list"),
        ]
        for url in urls:
            self.assert_matrix("get", url, TEACHER_ONLY)

    def test_token_values_bulk_update_is_teacher_only(self):
        expected = dict(TEACHER_ONLY)
        self.assert_matrix(
            "patch",
            reverse("api:token-values-update-bulk"),
            expected,
            body={"data": [{"id": self.world.token_value.id, "value": 7.0}]},
        )

    def test_token_values_bulk_update_writes_the_new_value(self):
        from course.models.models import TokenValue

        response = self.call(
            "teacher",
            "patch",
            reverse("api:token-values-update-bulk"),
            {"data": [{"id": self.world.token_value.id, "value": 7.0}]},
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(7.0, TokenValue.objects.get(pk=self.world.token_value.id).value)

    def test_course_admin_change_status_is_teacher_only(self):
        expected = dict(TEACHER_ONLY)
        self.assert_matrix(
            "post",
            reverse("api:admin-course-update-status"),
            expected,
            body={"id": self.world.student_reg.id, "status": "BLOCKED"},
        )

    def test_course_admin_change_status_updates_the_registration(self):
        from canvas.models.models import CanvasCourseRegistration

        response = self.call(
            "teacher",
            "post",
            reverse("api:admin-course-update-status"),
            {"id": self.world.student_reg.id, "status": "BLOCKED"},
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual("BLOCKED", CanvasCourseRegistration.objects.get(pk=self.world.student_reg.id).status)

    def test_unknown_status_silently_does_nothing(self):
        # KNOWN-BUG: CourseAdminViewSet.update_status does not validate `status`;
        # an unrecognised value is a 200 no-op instead of a 400.
        from canvas.models.models import CanvasCourseRegistration

        response = self.call(
            "teacher",
            "post",
            reverse("api:admin-course-update-status"),
            {"id": self.world.student_reg.id, "status": "NONSENSE"},
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual("VERIFIED", CanvasCourseRegistration.objects.get(pk=self.world.student_reg.id).status)


# --------------------------------------------------------------------------- #
# QuestionPermission / HasDeletePermission
# --------------------------------------------------------------------------- #
class QuestionPermissionTest(PermissionTestCase):
    def mcq_body(self, role, event=None):
        body = {
            "title": "Created by " + role,
            "text": "text",
            "answer": "a",
            "difficulty": "EASY",
            "visible_distractor_count": 1,
            "choices": {"a": "x", "b": "y"},
            "variables": [],
            "category": self.world.category.id,
        }
        if event is not None:
            body["event"] = event
        return body

    def test_creating_a_practice_question_is_teacher_only(self):
        # QuestionPermission requires an `event` in the body for non-teachers, so
        # a practice (event-less) question can only ever be created by a Teacher.
        expected = dict(TEACHER_ONLY)
        expected["teacher"] = 201
        self.assert_matrix(
            "post",
            reverse("api:multiple-choice-question-list"),
            expected,
            body=lambda role: self.mcq_body(role),
            label="create practice question",
        )

    def test_creating_a_question_inside_an_event_needs_event_edit_rights(self):
        expected = dict(COURSE_STAFF_ONLY)
        for role in ("ta", "instructor", "teacher"):
            expected[role] = 201
        self.assert_matrix(
            "post",
            reverse("api:multiple-choice-question-list"),
            expected,
            body=lambda role: self.mcq_body(role, event=self.world.event.id),
            label="create question in event",
        )

    def test_editing_an_event_question_needs_event_edit_rights(self):
        self.assert_matrix(
            "patch",
            reverse("api:multiple-choice-question-detail", kwargs={"pk": self.world.event_question.id}),
            COURSE_STAFF_ONLY,
            body={"title": "edited"},
            label="edit event question",
        )

    def test_editing_a_practice_question_is_teacher_only(self):
        # Question.has_edit_permission short-circuits to False when there is no
        # event, so course staff cannot touch practice questions.
        self.assert_matrix(
            "patch",
            reverse("api:multiple-choice-question-detail", kwargs={"pk": self.world.practice_question.id}),
            TEACHER_ONLY,
            body={"title": "edited"},
            label="edit practice question",
        )

    def test_viewing_an_event_question_needs_view_rights_on_the_event(self):
        expected = dict(ALL_AUTHENTICATED_ALLOWED)
        expected["outsider"] = 403
        self.assert_matrix(
            "get",
            reverse("api:multiple-choice-question-detail", kwargs={"pk": self.world.event_question.id}),
            expected,
            label="retrieve event question",
        )

    def test_viewing_a_practice_question_is_open_to_every_authenticated_user(self):
        self.assert_matrix(
            "get",
            reverse("api:multiple-choice-question-detail", kwargs={"pk": self.world.practice_question.id}),
            ALL_AUTHENTICATED_ALLOWED,
            label="retrieve practice question",
        )

    def test_deleting_a_question_requires_being_its_author(self):
        # HasDeletePermission -> author check, AND QuestionPermission -> edit
        # rights.  The event question's author is the teacher.
        expected = dict(TEACHER_ONLY)
        self.assert_matrix(
            "delete",
            reverse("api:question-detail", kwargs={"pk": self.world.event_question.id}),
            expected,
            label="delete event question",
        )

    def test_nobody_can_delete_a_students_own_practice_question(self):
        # KNOWN-BUG: the author (a student) fails QuestionPermission because the
        # question has no event, and the teacher fails HasDeletePermission
        # because they are not the author -- so the row can never be soft
        # deleted through the API.
        expected = dict((role, 403) for role in ROLES)
        expected["anonymous"] = 401
        self.assert_matrix(
            "delete",
            reverse("api:question-detail", kwargs={"pk": self.world.student_question.id}),
            expected,
            label="delete student-authored practice question",
        )

    def test_delete_is_a_soft_delete_returning_200_and_the_object(self):
        from course.models.models import Question

        url = reverse("api:question-detail", kwargs={"pk": self.world.event_question.id})
        response = self.call("teacher", "delete", url)
        self.assertEqual(200, response.status_code)
        self.assertEqual(self.world.event_question.id, response.data["id"])
        question = Question.objects.get(pk=self.world.event_question.id)
        self.assertEqual(Question.DELETED, question.question_status)


# --------------------------------------------------------------------------- #
# CoursePermission
# --------------------------------------------------------------------------- #
class CoursePermissionTest(PermissionTestCase):
    def test_retrieving_a_course_is_open_to_every_authenticated_user(self):
        # CoursePermission.has_object_permission returns True unconditionally for
        # GET; the has_view_permission() check is commented out in the source.
        self.assert_matrix(
            "get",
            reverse("api:course-detail", kwargs={"pk": self.world.course.id}),
            ALL_AUTHENTICATED_ALLOWED,
        )

    def test_any_authenticated_user_can_create_a_course(self):
        # KNOWN-BUG (by design?): there is no role check on course creation, and
        # perform_create() makes the caller the instructor.
        expected = dict((role, 201) for role in ROLES)
        expected["anonymous"] = 401
        self.assert_matrix(
            "post",
            reverse("api:course-list"),
            expected,
            body=lambda role: {
                "name": "Course by " + role,
                "start_date": "2026-01-01T00:00:00Z",
                "end_date": "2026-12-01T00:00:00Z",
            },
        )

    def test_course_creation_registers_the_creator_as_instructor(self):
        from canvas.models.models import CanvasCourse, CanvasCourseRegistration

        response = self.call(
            "student",
            "post",
            reverse("api:course-list"),
            {"name": "Student Course", "start_date": "2026-01-01T00:00:00Z", "end_date": "2026-12-01T00:00:00Z"},
        )
        self.assertEqual(201, response.status_code)
        course = CanvasCourse.objects.get(name="Student Course")
        self.assertEqual(self.world.student, course.instructor)
        registration = CanvasCourseRegistration.objects.get(course=course, user=self.world.student)
        self.assertEqual("INSTRUCTOR", registration.registration_type)
        self.assertEqual("VERIFIED", registration.status)

    def test_editing_a_course_needs_an_instructor_registration(self):
        self.assert_matrix(
            "patch",
            reverse("api:course-detail", kwargs={"pk": self.world.course.id}),
            INSTRUCTOR_ONLY,
            body={"name": "Edited"},
        )

    def test_deleting_a_course_needs_an_instructor_registration(self):
        expected = dict(INSTRUCTOR_ONLY)
        expected["instructor"] = 204
        expected["teacher"] = 204
        self.assert_matrix(
            "delete",
            reverse("api:course-detail", kwargs={"pk": self.world.course.id}),
            expected,
        )


# --------------------------------------------------------------------------- #
# GradeBookPermission / StudentsMustBeRegisteredPermission
# --------------------------------------------------------------------------- #
class GradeBookPermissionTest(PermissionTestCase):
    def test_gradebook_needs_course_edit_rights(self):
        self.assert_matrix(
            "get",
            reverse("api:course-course-grade-book", kwargs={"pk": self.world.course.id}),
            INSTRUCTOR_ONLY,
        )

    def test_gradebook_export_needs_course_edit_rights(self):
        self.assert_matrix(
            "get",
            reverse("api:course-export-grade-book", kwargs={"pk": self.world.course.id}),
            INSTRUCTOR_ONLY,
        )

    def test_gradebook_export_is_csv_with_a_content_disposition(self):
        response = self.call(
            "teacher",
            "get",
            reverse("api:course-export-grade-book", kwargs={"pk": self.world.course.id}),
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual("text/csv", response["Content-Type"])
        self.assertEqual(
            'attachment; filename="Baseline Course course gradebook.csv"',
            response["Content-Disposition"],
        )
        first_line = response.content.decode("utf-8").splitlines()[0]
        self.assertEqual("Event Name,Student Name,Grade,Total", first_line)


class StudentsMustBeRegisteredPermissionTest(PermissionTestCase):
    def test_my_grades_rejects_unregistered_students_and_explodes_for_staff(self):
        # KNOWN-BUG: a caller that passes the permission but has no VERIFIED
        # STUDENT registration (teacher / TA / instructor) hits a bare
        # ValueError -> 500.
        expected = {
            "anonymous": 401,
            "outsider": 403,
            "student": 200,
            "ta": 500,
            "instructor": 500,
            "teacher": 500,
        }
        self.assert_matrix(
            "get",
            reverse("api:course-my-grades", kwargs={"pk": self.world.course.id}),
            expected,
        )

    def test_token_use_never_checks_the_registration(self):
        # KNOWN-BUG: StudentsMustBeRegisteredPermission is object-level only and
        # TokenUseViewSet.use_tokens never calls get_object(), so an unregistered
        # user reaches update_token_use().
        expected = dict(ALL_AUTHENTICATED_ALLOWED)
        self.assert_matrix(
            "post",
            reverse("api:token-use-use-tokens", kwargs={"course_pk": self.world.course.id}),
            expected,
            body={str(self.world.token_use_option.id): 0},
        )


# --------------------------------------------------------------------------- #
# EventCreatePermission / EventEditPermission / IsOwnerOrReadOnly
# --------------------------------------------------------------------------- #
class EventPermissionTest(PermissionTestCase):
    def event_body(self, role, type="ASSIGNMENT", course=True):
        body = {
            "name": "Event by " + role,
            "type": type,
            "count_for_tokens": False,
            "start_date": "2026-01-01T00:00:00Z",
            "end_date": "2026-12-01T00:00:00Z",
        }
        if course:
            body["course"] = self.world.course.id
        return body

    def test_creating_an_assignment_needs_ta_or_instructor_rights(self):
        expected = dict(COURSE_STAFF_ONLY)
        for role in ("ta", "instructor", "teacher"):
            expected[role] = 201
        self.assert_matrix(
            "post",
            reverse("api:event-list"),
            expected,
            body=lambda role: self.event_body(role),
            label="create assignment event",
        )

    def test_creating_a_challenge_only_needs_a_verified_registration(self):
        expected = dict((role, 201) for role in ROLES)
        expected["anonymous"] = 401
        expected["outsider"] = 403
        self.assert_matrix(
            "post",
            reverse("api:event-list"),
            expected,
            body=lambda role: self.event_body(role, type="CHALLENGE"),
            label="create challenge event",
        )

    def test_creating_an_event_without_a_course_id_passes_the_permission(self):
        # KNOWN-BUG: EventCreatePermission returns True when the course cannot be
        # resolved, so the request is only stopped by serializer validation.
        expected = dict((role, 400) for role in ROLES)
        expected["anonymous"] = 401
        self.assert_matrix(
            "post",
            reverse("api:event-list"),
            expected,
            body=lambda role: self.event_body(role, course=False),
            label="create event without course",
        )

    def test_put_edit_needs_ta_or_instructor_rights(self):
        self.assert_matrix(
            "put",
            reverse("api:event-detail", kwargs={"pk": self.world.event.id}),
            COURSE_STAFF_ONLY,
            body=lambda role: self.event_body(role),
            label="PUT event",
        )

    def test_patch_edit_is_guarded_only_by_is_owner_or_read_only(self):
        # EventEditPermission looks at PUT alone; PATCH survives purely because
        # IsOwnerOrReadOnly also runs.
        self.assert_matrix(
            "patch",
            reverse("api:event-detail", kwargs={"pk": self.world.event.id}),
            COURSE_STAFF_ONLY,
            body={"name": "Renamed"},
            label="PATCH event",
        )

    def test_delete_is_guarded_only_by_is_owner_or_read_only(self):
        expected = dict(COURSE_STAFF_ONLY)
        for role in ("ta", "instructor", "teacher"):
            expected[role] = 204
        self.assert_matrix(
            "delete",
            reverse("api:event-detail", kwargs={"pk": self.world.event.id}),
            expected,
            label="DELETE event",
        )


class EventSetPermissionTest(PermissionTestCase):
    def test_creating_an_event_set_is_broken_for_everyone_allowed_through(self):
        # KNOWN-BUG: EventSetSerializer declares a writable nested
        # ``events = EventSerializer(many=True)``, so ModelSerializer.create()
        # raises -> 500 for every caller that clears the permission check.
        expected = {
            "anonymous": 401,
            "outsider": 403,
            "student": 403,
            "ta": 500,
            "instructor": 500,
            "teacher": 500,
        }
        self.assert_matrix(
            "post",
            reverse("api:event-set-view-list"),
            expected,
            body=lambda role: {"name": "ES " + role, "course": self.world.course.id, "tokens": 1.0, "events": []},
        )

    def test_patching_an_event_set_is_completely_unguarded(self):
        # KNOWN-BUG: EventCreatePermission only guards POST and EventEditPermission
        # only guards PUT, so ANY authenticated user can rename any event set --
        # EventSet.has_edit_permission is never consulted.
        self.assert_matrix(
            "patch",
            reverse("api:event-set-view-detail", kwargs={"pk": self.world.event_set.id}),
            ALL_AUTHENTICATED_ALLOWED,
            body={"name": "Renamed"},
        )

    def test_deleting_an_event_set_is_completely_unguarded(self):
        # KNOWN-BUG: same hole as above, for DELETE.
        expected = dict((role, 204) for role in ROLES)
        expected["anonymous"] = 401
        self.assert_matrix(
            "delete",
            reverse("api:event-set-view-detail", kwargs={"pk": self.world.event_set.id}),
            expected,
        )


# --------------------------------------------------------------------------- #
# UserConsentPermission
# --------------------------------------------------------------------------- #
class UserConsentPermissionTest(PermissionTestCase):
    def test_only_the_owner_can_read_a_consent(self):
        # teacher: the viewset queryset is unfiltered for teachers, so the object
        # is found and then rejected -> 403.  Everyone else is filtered out -> 404.
        expected = {
            "anonymous": 401,
            "outsider": 404,
            "student": 200,
            "ta": 404,
            "instructor": 404,
            "teacher": 403,
        }
        self.assert_matrix(
            "get",
            reverse("api:user-consent-detail", kwargs={"pk": self.world.consent.id}),
            expected,
        )

    def test_nobody_can_delete_a_consent(self):
        # has_object_permission allows GET and POST only.
        expected = {
            "anonymous": 401,
            "outsider": 404,
            "student": 403,
            "ta": 404,
            "instructor": 404,
            "teacher": 403,
        }
        self.assert_matrix(
            "delete",
            reverse("api:user-consent-detail", kwargs={"pk": self.world.consent.id}),
            expected,
        )

    def test_creating_a_consent_copies_the_legal_name_onto_the_user(self):
        response = self.call(
            "outsider",
            "post",
            reverse("api:user-consent-list"),
            {
                "consent": True,
                "access_submitted_course_work": True,
                "access_course_grades": True,
                "legal_first_name": "Olivia",
                "legal_last_name": "Outside",
                "gender": "N/A",
                "race": "N/A",
                "student_number": "99999999",
                "date": "2026-08-03",
            },
        )
        self.assertEqual(201, response.status_code)
        self.world.outsider.refresh_from_db()
        self.assertEqual("Olivia", self.world.outsider.first_name)
        self.assertEqual("Outside", self.world.outsider.last_name)


# --------------------------------------------------------------------------- #
# HasViewSubmissionPermission
# --------------------------------------------------------------------------- #
class SubmissionPermissionTest(PermissionTestCase):
    def test_any_authenticated_user_can_retrieve_any_submission(self):
        # KNOWN-BUG: SubmissionViewSet.retrieve() bypasses self.get_object(), so
        # HasViewSubmissionPermission.has_object_permission never runs.
        self.assert_matrix(
            "get",
            reverse("api:submission-detail", kwargs={"pk": self.world.submission.id}),
            ALL_AUTHENTICATED_ALLOWED,
        )

    def test_listing_submissions_is_scoped_by_the_queryset_not_the_permission(self):
        url = reverse("api:submission-list") + "?question={}".format(self.world.practice_question.id)
        for role, expected_count in [("student", 1), ("outsider", 0), ("ta", 0), ("instructor", 0)]:
            with self.subTest(role=role):
                response = self.call(role, "get", url)
                self.assertEqual(200, response.status_code)
                self.assertEqual(expected_count, len(response.data))

    def test_teachers_see_every_submission_in_the_list(self):
        url = reverse("api:submission-list") + "?question={}".format(self.world.practice_question.id)
        response = self.call("teacher", "get", url)
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.data))


# --------------------------------------------------------------------------- #
# TeamPermission
# --------------------------------------------------------------------------- #
class TeamPermissionTest(PermissionTestCase):
    def test_team_list_is_public(self):
        # KNOWN-BUG: TeamPermission.has_permission is hardcoded to True.
        expected = dict(ALL_AUTHENTICATED_ALLOWED)
        expected["anonymous"] = 200
        self.assert_matrix("get", reverse("api:team-list"), expected)

    def test_team_detail_requires_membership_and_500s_for_anonymous(self):
        # KNOWN-BUG: the anonymous case reaches the object filter with an
        # AnonymousUser and raises instead of returning 401.
        expected = {
            "anonymous": 500,
            "outsider": 403,
            "student": 403,
            "ta": 403,
            "instructor": 403,
            "teacher": 403,
        }
        expected["student"] = 200  # the only member of world.team
        self.assert_matrix(
            "get",
            reverse("api:team-detail", kwargs={"pk": self.world.team.id}),
            expected,
        )


# --------------------------------------------------------------------------- #
# Endpoints with no object-level protection at all
# --------------------------------------------------------------------------- #
class UnguardedEndpointTest(PermissionTestCase):
    def test_any_authenticated_user_can_flip_any_uqj_favourite_flag(self):
        # KNOWN-BUG: UpdateUQJViewSet.update_is_favorite looks the UQJ up by id
        # with no ownership check.
        from course.models.models import UserQuestionJunction

        url = reverse("api:uqj-update-update-is-favorite")
        body = {"id": self.world.uqj.id, "status": True}
        self.assert_matrix("post", url, ALL_AUTHENTICATED_ALLOWED, body=body)

        response = self.call("outsider", "post", url, body)
        self.assertEqual(200, response.status_code)
        self.assertTrue(UserQuestionJunction.objects.get(pk=self.world.uqj.id).is_favorite)

    def test_a_client_can_post_an_action_with_an_arbitrary_token_change(self):
        # KNOWN-BUG: ActionsSerializer excludes nothing, so token_change is
        # writable and MyUser.tokens (the ledger) can be inflated at will.
        url = reverse("api:user-actions-list")
        body = {
            "description": "minted",
            "token_change": 99,
            "status": "Complete",
            "verb": "Completed",
            "object_type": "User",
        }
        self.assertIsNone(self.world.outsider.tokens)
        response = self.call("outsider", "post", url, body)
        self.assertEqual(201, response.status_code)
        self.assertEqual(self.world.outsider.id, response.data["actor"])
        self.assertEqual(99, self.world.outsider.tokens)

    def test_actor_is_forced_to_the_requesting_user(self):
        url = reverse("api:user-actions-list")
        body = {
            "description": "spoofed",
            "token_change": 5,
            "status": "Complete",
            "verb": "Completed",
            "object_type": "User",
            "actor": self.world.teacher.id,
        }
        response = self.call("outsider", "post", url, body)
        self.assertEqual(201, response.status_code)
        self.assertEqual(self.world.outsider.id, response.data["actor"])
        self.assertIsNone(self.world.teacher.tokens)


# --------------------------------------------------------------------------- #
# Anonymous sweep
# --------------------------------------------------------------------------- #
class AnonymousAccessTest(PermissionTestCase):
    """One representative endpoint per custom permission class."""

    def test_anonymous_requests_are_401_on_every_guarded_endpoint(self):
        cases = [
            ("TeacherAccessPermission", "get", reverse("api:admin-list")),
            ("QuestionPermission", "get", reverse("api:question-list")),
            (
                "UserConsentPermission",
                "get",
                reverse("api:user-consent-detail", kwargs={"pk": self.world.consent.id}),
            ),
            (
                "StudentsMustBeRegisteredPermission",
                "get",
                reverse("api:course-my-grades", kwargs={"pk": self.world.course.id}),
            ),
            (
                "GradeBookPermission",
                "get",
                reverse("api:course-course-grade-book", kwargs={"pk": self.world.course.id}),
            ),
            ("CoursePermission", "get", reverse("api:course-list")),
            ("EventCreatePermission", "post", reverse("api:event-list")),
            (
                "EventEditPermission",
                "put",
                reverse("api:event-detail", kwargs={"pk": self.world.event.id}),
            ),
            (
                "HasDeletePermission",
                "delete",
                reverse("api:question-detail", kwargs={"pk": self.world.event_question.id}),
            ),
            (
                "IsOwnerOrReadOnly",
                "patch",
                reverse("api:event-detail", kwargs={"pk": self.world.event.id}),
            ),
            (
                "HasViewSubmissionPermission",
                "get",
                reverse("api:submission-detail", kwargs={"pk": self.world.submission.id}),
            ),
        ]
        for permission_class, method, url in cases:
            with self.subTest(permission_class=permission_class):
                response = self.call("anonymous", method, url)
                self.assertEqual(401, response.status_code)
                self.assertEqual('Basic realm="api"', response["WWW-Authenticate"])

    def test_the_publicly_readable_endpoints_stay_public(self):
        cases = [
            reverse("api:api-root"),
            reverse("api:faq-list"),
            reverse("api:difficulty-list"),
            reverse("api:question-category-list"),
            reverse("api:sample-multiple-choice-question-list"),
            reverse("api:team-list"),
            reverse("api:openapi-schema"),
            reverse("api:docs"),
        ]
        for url in cases:
            with self.subTest(url=url):
                self.assertEqual(200, self.call("anonymous", "get", url).status_code)
