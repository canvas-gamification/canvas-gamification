"""
Regression tests for the security fixes that followed PR #404's "bugs found but
deliberately not fixed" list. Each test names the hole it closes; if one of these
starts failing, the hole is open again.
"""

import base64

from django.core import mail
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import MyUser
from canvas.models.models import CanvasCourseRegistration, EventSet
from course.models.models import Question, UserQuestionJunction
from general.models.action import Action
from test.baseline import factories as fx


class SecurityWorld(TestCase):
    """Two registered students, an instructor, an outsider and an open exam."""

    def setUp(self):
        self.teacher = fx.make_teacher("sec_teacher")
        self.instructor = fx.make_user("sec_instructor")
        self.alice = fx.make_student("sec_alice")
        self.bob = fx.make_student("sec_bob")
        self.outsider = fx.make_student("sec_outsider")
        self.category = fx.make_category("sec cat")
        fx.make_token_value(self.category, "EASY", 2.0)
        self.course = fx.make_course(name="Sec Course", instructor=self.instructor)
        fx.make_registration(self.course, self.instructor, registration_type="INSTRUCTOR")
        self.alice_reg = fx.make_registration(self.course, self.alice)
        self.bob_reg = fx.make_registration(self.course, self.bob)
        self.exam = fx.make_event(self.course, name="Sec Exam", type="EXAM", author=self.instructor)
        self.practice_q = fx.make_mcq(self.teacher, self.category, title="practice", answer="a")
        self.exam_q = fx.make_mcq(self.instructor, self.category, title="exam q", answer="b", event=self.exam)
        self.event_set = fx.make_event_set(self.course, events=[self.exam])

    def client_for(self, user):
        return fx.api_client(user)


class TokenLedgerTest(SecurityWorld):
    def test_client_supplied_token_change_is_ignored(self):
        response = self.client_for(self.alice).post(
            reverse("api:user-actions-list"),
            {"description": "minted", "token_change": 9999, "status": "Complete", "verb": "Clicked"},
            format="json",
        )
        self.assertEqual(201, response.status_code)
        self.assertEqual(0, response.data["token_change"])
        self.assertEqual(0, Action.objects.get(pk=response.data["id"]).token_change)
        self.assertEqual(0, self.alice.tokens)


class SubmissionVisibilityTest(SecurityWorld):
    def setUp(self):
        super().setUp()
        self.bob_submission = fx.make_mcq_submission(self.bob, self.practice_q, answer="a")
        self.bob_exam_submission = fx.make_mcq_submission(self.bob, self.exam_q, answer="b")

    def url(self, submission):
        return reverse("api:submission-detail", kwargs={"pk": submission.id})

    def test_another_student_cannot_read_a_submission(self):
        self.assertEqual(403, self.client_for(self.alice).get(self.url(self.bob_submission)).status_code)
        self.assertEqual(403, self.client_for(self.outsider).get(self.url(self.bob_exam_submission)).status_code)

    def test_the_owner_still_can(self):
        # Regression for ``self.user is user`` -- a freshly loaded owner must pass.
        fresh_bob = MyUser.objects.get(pk=self.bob.pk)
        self.assertTrue(self.bob_submission.has_view_permission(fresh_bob))
        self.assertEqual(200, self.client_for(fresh_bob).get(self.url(self.bob_submission)).status_code)

    def test_teachers_course_staff_and_team_mates_can(self):
        self.assertEqual(200, self.client_for(self.teacher).get(self.url(self.bob_exam_submission)).status_code)
        self.assertEqual(200, self.client_for(self.instructor).get(self.url(self.bob_exam_submission)).status_code)
        self.assertEqual(403, self.client_for(self.alice).get(self.url(self.bob_exam_submission)).status_code)
        fx.make_team(self.exam, registrations=[self.alice_reg, self.bob_reg])
        self.assertEqual(200, self.client_for(self.alice).get(self.url(self.bob_exam_submission)).status_code)


class QuestionAnswerExposureTest(SecurityWorld):
    def test_download_questions_is_teacher_only(self):
        url = reverse("api:question-download-questions")
        self.assertEqual(403, self.client_for(self.alice).get(url).status_code)
        self.assertEqual(403, self.client_for(self.instructor).get(url).status_code)
        response = self.client_for(self.teacher).get(url)
        self.assertEqual(200, response.status_code)
        self.assertIn("answer", response.data[0])

    def test_students_only_list_their_own_questions(self):
        response = self.client_for(self.alice).get(reverse("api:question-list"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(0, response.data["count"])
        response = self.client_for(self.teacher).get(reverse("api:question-list"))
        self.assertEqual(2, response.data["count"])

    def test_registered_student_does_not_get_the_answer_of_an_open_exam_question(self):
        url = reverse("api:multiple-choice-question-detail", kwargs={"pk": self.exam_q.id})
        response = self.client_for(self.alice).get(url)
        self.assertEqual(200, response.status_code)
        self.assertNotIn("answer", response.data)
        self.assertIn("choices", response.data)

    def test_editors_still_get_the_answer(self):
        url = reverse("api:multiple-choice-question-detail", kwargs={"pk": self.exam_q.id})
        for user in (self.teacher, self.instructor):
            with self.subTest(user=user.username):
                response = self.client_for(user).get(url)
                self.assertEqual(200, response.status_code)
                self.assertEqual("b", response.data["answer"])

    def test_sample_questions_keep_their_answer_for_the_public_demo(self):
        sample = fx.make_mcq(self.teacher, self.category, title="sample", answer="c", is_sample=True)
        response = fx.api_client().get(reverse("api:sample-multiple-choice-question-detail", kwargs={"pk": sample.id}))
        self.assertEqual(200, response.status_code)
        self.assertEqual("c", response.data["answer"])


class ExamGradeMaskingTest(SecurityWorld):
    def test_uqj_hides_correctness_while_the_exam_is_open(self):
        fx.make_mcq_submission(self.alice, self.exam_q, answer="b")
        response = self.client_for(self.alice).get(reverse("api:uqj-list") + "?question={}".format(self.exam_q.id))
        self.assertEqual(200, response.status_code)
        row = response.data["results"][0]
        self.assertIsNone(row["tokens_received"])
        self.assertIsNone(row["is_solved"])
        self.assertIsNone(row["is_partially_solved"])
        self.assertEqual("Submitted", row["status"])
        self.assertEqual(str(self.exam_q.token_value), row["formatted_current_tokens_received"])

    def test_practice_questions_are_not_masked(self):
        fx.make_mcq_submission(self.alice, self.practice_q, answer="a")
        response = self.client_for(self.alice).get(reverse("api:uqj-list") + "?question={}".format(self.practice_q.id))
        row = response.data["results"][0]
        # Not masked: real values come back (their exact content is the grader's business).
        self.assertIsNotNone(row["is_solved"])
        self.assertIsNotNone(row["is_partially_solved"])
        self.assertIsNotNone(row["tokens_received"])
        self.assertNotIn(row["status"], ("Submitted", "Not Submitted"))


class EventPermissionTest(SecurityWorld):
    def test_outsiders_and_students_cannot_change_an_event(self):
        for user in (self.outsider, self.alice):
            client = self.client_for(user)
            with self.subTest(user=user.username):
                self.assertEqual(
                    403,
                    client.post(
                        reverse("api:event-add-question-set", kwargs={"pk": self.exam.id}),
                        {"category": self.category.id, "difficulty": "EASY", "number_of_questions": 1},
                        format="json",
                    ).status_code,
                )
                self.assertEqual(
                    403,
                    client.post(
                        reverse("api:event-remove-question", kwargs={"pk": self.exam.id}),
                        {"question_id": self.exam_q.id},
                        format="json",
                    ).status_code,
                )
                self.assertEqual(
                    403, client.post(reverse("api:event-set-featured", kwargs={"pk": self.exam.id})).status_code
                )
                self.assertEqual(403, client.get(reverse("api:event-stats", kwargs={"pk": self.exam.id})).status_code)
        self.assertEqual(Question.CREATED, Question.objects.get(pk=self.exam_q.id).question_status)

    def test_the_instructor_can(self):
        client = self.client_for(self.instructor)
        self.assertEqual(200, client.get(reverse("api:event-stats", kwargs={"pk": self.exam.id})).status_code)
        self.assertEqual(200, client.post(reverse("api:event-set-featured", kwargs={"pk": self.exam.id})).status_code)

    def test_event_leader_board_is_for_course_members(self):
        url = reverse("api:event-leader-board", kwargs={"pk": self.exam.id})
        self.assertEqual(403, self.client_for(self.outsider).get(url).status_code)
        self.assertEqual(200, self.client_for(self.alice).get(url).status_code)


class EventSetPermissionTest(SecurityWorld):
    def test_only_course_staff_may_change_or_delete(self):
        url = reverse("api:event-set-view-detail", kwargs={"pk": self.event_set.id})
        self.assertEqual(403, self.client_for(self.alice).patch(url, {"name": "x"}, format="json").status_code)
        self.assertEqual(403, self.client_for(self.alice).delete(url).status_code)
        self.assertEqual(
            200, self.client_for(self.instructor).patch(url, {"name": "renamed"}, format="json").status_code
        )
        self.assertEqual("renamed", EventSet.objects.get(pk=self.event_set.id).name)
        self.assertEqual(204, self.client_for(self.teacher).delete(url).status_code)


class RosterAndTeamExposureTest(SecurityWorld):
    def test_roster_is_for_members_and_names_only(self):
        url = reverse("api:course-course-registrations", kwargs={"pk": self.course.id})
        self.assertEqual(403, self.client_for(self.outsider).get(url).status_code)
        response = self.client_for(self.alice).get(url)
        self.assertEqual(200, response.status_code)
        self.assertEqual({"id", "name"}, set(response.data[0].keys()))

    def test_leader_board_is_for_members(self):
        url = reverse("api:course-leader-board", kwargs={"pk": self.course.id})
        self.assertEqual(403, self.client_for(self.outsider).get(url).status_code)
        self.assertEqual(200, self.client_for(self.alice).get(url).status_code)
        self.assertEqual(200, self.client_for(self.teacher).get(url).status_code)

    def test_teams_need_authentication_and_course_membership(self):
        team = fx.make_team(self.exam, registrations=[self.alice_reg])
        self.assertEqual(401, fx.api_client().get(reverse("api:team-list")).status_code)
        self.assertEqual([], self.client_for(self.outsider).get(reverse("api:team-list")).data)
        self.assertEqual(1, len(self.client_for(self.bob).get(reverse("api:team-list")).data))
        detail = reverse("api:team-detail", kwargs={"pk": team.id})
        self.assertEqual(404, self.client_for(self.outsider).get(detail).status_code)
        self.assertEqual(200, self.client_for(self.bob).get(detail).status_code)
        self.assertEqual(200, self.client_for(self.teacher).get(detail).status_code)

    def test_unregistered_users_cannot_create_a_team(self):
        response = self.client_for(self.outsider).post(
            reverse("api:team-create-and-join"), {"event_id": self.exam.id, "name": "x"}, format="json"
        )
        self.assertEqual(403, response.status_code)


class SmallOwnershipGapsTest(SecurityWorld):
    def test_favourite_flag_is_owner_only(self):
        uqj = UserQuestionJunction.objects.get(user=self.bob, question=self.practice_q)
        url = reverse("api:uqj-update-update-is-favorite")
        self.assertEqual(
            404, self.client_for(self.alice).post(url, {"id": uqj.id, "status": True}, format="json").status_code
        )
        self.assertEqual(
            200, self.client_for(self.bob).post(url, {"id": uqj.id, "status": True}, format="json").status_code
        )
        self.assertTrue(UserQuestionJunction.objects.get(pk=uqj.id).is_favorite)
        self.assertEqual(
            400, self.client_for(self.bob).post(url, {"id": uqj.id, "status": "maybe"}, format="json").status_code
        )

    def test_token_use_requires_registration(self):
        option = fx.make_token_use_option(self.course)
        url = reverse("api:token-use-use-tokens", kwargs={"course_pk": self.course.id})
        self.assertEqual(403, self.client_for(self.outsider).post(url, {str(option.id): 0}, format="json").status_code)
        self.assertEqual(200, self.client_for(self.alice).post(url, {str(option.id): 0}, format="json").status_code)

    def test_change_status_rejects_unknown_values(self):
        response = self.client_for(self.teacher).post(
            reverse("api:admin-course-update-status"), {"id": self.alice_reg.id, "status": "NONSENSE"}, format="json"
        )
        self.assertEqual(400, response.status_code)
        self.assertEqual("VERIFIED", CanvasCourseRegistration.objects.get(pk=self.alice_reg.id).status)

    def test_my_grades_is_404_not_500_for_staff(self):
        url = reverse("api:course-my-grades", kwargs={"pk": self.course.id})
        self.assertEqual(404, self.client_for(self.instructor).get(url).status_code)
        self.assertEqual(200, self.client_for(self.alice).get(url).status_code)


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend", FRONTEND_URL="")
class PasswordResetLinkTest(TestCase):
    def setUp(self):
        self.user = fx.make_student("reset_me")
        self.url = reverse("api:reset-password-send-email")

    def test_a_forged_origin_does_not_reach_the_email(self):
        response = fx.api_client().post(
            self.url, {"email": self.user.email}, format="json", HTTP_ORIGIN="https://evil.example"
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(mail.outbox))
        self.assertNotIn("evil.example", mail.outbox[0].body)
        self.assertIn("http://testserver/accounts/reset-password/", mail.outbox[0].body)

    @override_settings(ALLOWED_HOSTS=["testserver", "app.example.com"])
    def test_an_allowed_origin_is_used(self):
        fx.api_client().post(self.url, {"email": self.user.email}, format="json", HTTP_ORIGIN="https://app.example.com")
        self.assertIn("https://app.example.com/accounts/reset-password/", mail.outbox[0].body)

    @override_settings(FRONTEND_URL="https://frontend.example.com/")
    def test_frontend_url_wins(self):
        fx.api_client().post(self.url, {"email": self.user.email}, format="json", HTTP_ORIGIN="https://evil.example")
        self.assertIn("https://frontend.example.com/accounts/reset-password/", mail.outbox[0].body)

    def test_no_origin_header_is_fine(self):
        self.assertEqual(200, fx.api_client().post(self.url, {"email": self.user.email}, format="json").status_code)
        self.assertEqual(1, len(mail.outbox))

    def test_unknown_addresses_get_the_same_answer_and_no_email(self):
        response = fx.api_client().post(
            self.url, {"email": "nobody@example.com"}, format="json", HTTP_ORIGIN="https://x.example"
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(0, len(mail.outbox))

    def test_registration_link_ignores_a_forged_origin_too(self):
        payload = {
            "email": "new@example.com",
            "first_name": "New",
            "last_name": "User",
            "nickname": "newbie",
            "password": "Str0ng-passw0rd!",
            "password2": "Str0ng-passw0rd!",
            "recaptcha_key": "x",
        }
        with override_settings(DEBUG=True):  # skips reCAPTCHA
            response = fx.api_client().post(
                reverse("api:register-list"), payload, format="json", HTTP_ORIGIN="https://evil.example"
            )
        self.assertEqual(201, response.status_code)
        self.assertNotIn("evil.example", mail.outbox[-1].body)


class AuthenticationHardeningTest(TestCase):
    def setUp(self):
        self.student = fx.make_student("hardened")
        self.protected_url = reverse("api:user-stats-list")

    def test_basic_auth_is_no_longer_accepted(self):
        raw = "{}:{}".format(self.student.username, fx.PASSWORD)
        encoded = base64.b64encode(raw.encode("utf-8")).decode("ascii")
        client = fx.api_client()
        client.credentials(HTTP_AUTHORIZATION="Basic " + encoded)
        self.assertEqual(401, client.get(self.protected_url).status_code)

    @override_settings(API_THROTTLING_ENABLED=True)
    def test_login_is_rate_limited(self):
        cache.clear()
        client = fx.api_client()
        statuses = []
        for _ in range(21):
            response = client.post(reverse("api:token-auth"), {"username": self.student.username, "password": "wrong"})
            statuses.append(response.status_code)
        self.assertEqual(400, statuses[0])
        self.assertEqual(429, statuses[-1])
        cache.clear()

    def test_throttling_is_off_when_disabled(self):
        client = fx.api_client()
        for _ in range(25):
            self.assertEqual(
                400,
                client.post(
                    reverse("api:token-auth"), {"username": self.student.username, "password": "wrong"}
                ).status_code,
            )
