"""Baseline tests for the canvas token economy.

Covers ``CanvasCourseRegistration.total_tokens_received`` (its three separate
contributions plus the ``end_date < now`` gate and the no-team case),
``CanvasCourseRegistration.available_tokens`` and
``canvas.utils.token_use.update_token_use``.

These pin *current* behaviour (Django 3.0 / DRF 3.11) so a later upgrade can be
checked for behaviour preservation.  Bugs are pinned, never fixed.
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase

from canvas.models.models import CanvasCourseRegistration, TokenUse
from canvas.utils.token_use import TokenUseException, update_token_use
from test.baseline import fixtures_canvas as fx


class TotalTokensReceivedTests(TestCase):
    """canvas/models/models.py:127-156"""

    def setUp(self):
        super().setUp()
        self.category = fx.make_category()
        self.course = fx.make_course()
        self.student = fx.make_user("student")
        self.course_reg = fx.make_registration(self.student, self.course)

    # ------------------------------------------------------------------
    # baseline / practice contribution
    # ------------------------------------------------------------------
    def test_no_contributions_is_zero(self):
        self.assertEqual(self.course_reg.total_tokens_received, 0)

    def test_practice_tokens_only(self):
        q1 = fx.make_question(self.category, title="p1")
        q2 = fx.make_question(self.category, title="p2")
        fx.set_uqj(self.student, q1, tokens_received=3.0)
        fx.set_uqj(self.student, q2, tokens_received=4.5)

        self.assertEqual(self.course_reg.total_tokens_received, 7.5)

    def test_practice_tokens_ignore_unverified_and_non_practice_questions(self):
        unverified = fx.make_question(self.category, title="unverified", is_verified=False)
        course_question = fx.make_question(self.category, title="course-bound", course=self.course)
        event = fx.make_event(self.course, name="e1", count_for_tokens=False)
        event_question = fx.make_question(self.category, title="event-bound", event=event)

        fx.set_uqj(self.student, unverified, tokens_received=100.0)
        fx.set_uqj(self.student, course_question, tokens_received=100.0)
        fx.set_uqj(self.student, event_question, tokens_received=100.0)

        self.assertEqual(self.course_reg.total_tokens_received, 0)

    def test_practice_tokens_are_not_scoped_to_the_course(self):
        """Practice tokens are global: a second course's registration sees them too."""
        practice = fx.make_question(self.category, title="p1")
        fx.set_uqj(self.student, practice, tokens_received=6.0)

        other_course = fx.make_course(name="Other")
        other_reg = fx.make_registration(self.student, other_course)

        self.assertEqual(self.course_reg.total_tokens_received, 6.0)
        self.assertEqual(other_reg.total_tokens_received, 6.0)

    def test_soft_deleted_practice_question_is_excluded(self):
        practice = fx.make_question(self.category, title="p1")
        fx.set_uqj(self.student, practice, tokens_received=6.0)
        self.assertEqual(self.course_reg.total_tokens_received, 6.0)

        practice.soft_delete()
        self.assertEqual(self.course_reg.total_tokens_received, 0)

    # ------------------------------------------------------------------
    # event contribution
    # ------------------------------------------------------------------
    def _ended_token_event(self, name="ended"):
        return fx.make_event(
            self.course,
            name=name,
            count_for_tokens=True,
            start_offset=-10,
            end_offset=-1,
        )

    def test_ended_count_for_tokens_event_with_team(self):
        event = self._ended_token_event()
        question = fx.make_question(self.category, title="q1", event=event)
        fx.set_uqj(self.student, question, tokens_received=5.0)
        fx.make_team(event, "team", [self.course_reg])

        self.assertEqual(self.course_reg.total_tokens_received, 5.0)

    def test_event_not_ended_yet_is_gated_out(self):
        event = fx.make_event(
            self.course,
            name="open",
            count_for_tokens=True,
            start_offset=-1,
            end_offset=10,
        )
        question = fx.make_question(self.category, title="q1", event=event)
        fx.set_uqj(self.student, question, tokens_received=5.0)
        fx.make_team(event, "team", [self.course_reg])

        self.assertEqual(self.course_reg.total_tokens_received, 0)

    def test_event_with_count_for_tokens_false_is_excluded(self):
        event = fx.make_event(
            self.course,
            name="not-counted",
            count_for_tokens=False,
            start_offset=-10,
            end_offset=-1,
        )
        question = fx.make_question(self.category, title="q1", event=event)
        fx.set_uqj(self.student, question, tokens_received=5.0)
        fx.make_team(event, "team", [self.course_reg])

        self.assertEqual(self.course_reg.total_tokens_received, 0)

    def test_no_team_contributes_zero(self):
        event = self._ended_token_event()
        question = fx.make_question(self.category, title="q1", event=event)
        fx.set_uqj(self.student, question, tokens_received=5.0)
        # no team at all for this user

        self.assertEqual(self.course_reg.total_tokens_received, 0)

    def test_event_tokens_use_best_of_team(self):
        event = self._ended_token_event()
        question = fx.make_question(self.category, title="q1", event=event)
        team_mate = fx.make_user("mate")
        mate_reg = fx.make_registration(team_mate, self.course)

        fx.set_uqj(self.student, question, tokens_received=2.0)
        fx.set_uqj(team_mate, question, tokens_received=9.0)
        fx.make_team(event, "team", [self.course_reg, mate_reg])

        # both members receive the team best-of score
        self.assertEqual(self.course_reg.total_tokens_received, 9.0)
        self.assertEqual(mate_reg.total_tokens_received, 9.0)

    def test_event_from_another_course_is_excluded(self):
        other_course = fx.make_course(name="Other")
        other_reg = fx.make_registration(self.student, other_course)
        event = fx.make_event(
            other_course,
            name="other-ended",
            count_for_tokens=True,
            start_offset=-10,
            end_offset=-1,
        )
        question = fx.make_question(self.category, title="q1", event=event)
        fx.set_uqj(self.student, question, tokens_received=7.0)
        fx.make_team(event, "team", [other_reg])

        self.assertEqual(self.course_reg.total_tokens_received, 0)
        self.assertEqual(other_reg.total_tokens_received, 7.0)

    # ------------------------------------------------------------------
    # event-set contribution
    # ------------------------------------------------------------------
    def test_event_set_tokens_awarded_only_when_every_event_solved(self):
        # neither event counts for tokens, so the only contribution is the set
        event_a = fx.make_event(self.course, name="a", count_for_tokens=False)
        event_b = fx.make_event(self.course, name="b", count_for_tokens=False)
        q_a = fx.make_question(self.category, title="qa", event=event_a)
        q_b = fx.make_question(self.category, title="qb", event=event_b)
        fx.make_event_set(self.course, name="set", tokens=12.0, events=[event_a, event_b])

        self.assertEqual(self.course_reg.total_tokens_received, 0)

        fx.set_uqj(self.student, q_a, is_solved=True)
        self.assertEqual(self.course_reg.total_tokens_received, 0)

        fx.set_uqj(self.student, q_b, is_solved=True)
        self.assertEqual(self.course_reg.total_tokens_received, 12.0)

    def test_event_set_with_no_events_awards_tokens_vacuously(self):
        # KNOWN-BUG: all() over an empty event list is vacuously True, so an
        # EventSet with no events (or containing an event with no questions)
        # hands out its tokens to every registered user for free.
        fx.make_event_set(self.course, name="empty-set", tokens=4.0, events=[])
        self.assertEqual(self.course_reg.total_tokens_received, 4.0)

    def test_event_set_with_empty_event_awards_tokens_vacuously(self):
        # KNOWN-BUG: Event.has_solved_event is vacuously True for an event with
        # zero questions (0 == 0), so the set is awarded without any work.
        empty_event = fx.make_event(self.course, name="empty", count_for_tokens=False)
        fx.make_event_set(self.course, name="set", tokens=3.0, events=[empty_event])
        self.assertEqual(self.course_reg.total_tokens_received, 3.0)

    def test_event_set_from_another_course_is_excluded(self):
        other_course = fx.make_course(name="Other")
        fx.make_event_set(other_course, name="other-set", tokens=50.0, events=[])
        self.assertEqual(self.course_reg.total_tokens_received, 0)

    # ------------------------------------------------------------------
    # combined
    # ------------------------------------------------------------------
    def test_all_three_contributions_combined(self):
        practice = fx.make_question(self.category, title="p1")
        fx.set_uqj(self.student, practice, tokens_received=1.5)

        event = self._ended_token_event(name="ended")
        event_question = fx.make_question(self.category, title="q1", event=event)
        fx.set_uqj(self.student, event_question, tokens_received=5.0, is_solved=True)
        fx.make_team(event, "team", [self.course_reg])

        set_event = fx.make_event(self.course, name="set-event", count_for_tokens=False)
        set_question = fx.make_question(self.category, title="qs", event=set_event)
        fx.set_uqj(self.student, set_question, is_solved=True)
        fx.make_event_set(self.course, name="set", tokens=10.0, events=[set_event])

        self.assertEqual(self.course_reg.total_tokens_received, 1.5 + 5.0 + 10.0)


class AvailableTokensTests(TestCase):
    """canvas/models/models.py:158-170"""

    def setUp(self):
        super().setUp()
        self.category = fx.make_category()
        self.course = fx.make_course()
        self.student = fx.make_user("student")
        self.course_reg = fx.make_registration(self.student, self.course)
        practice = fx.make_question(self.category, title="p1")
        fx.set_uqj(self.student, practice, tokens_received=20.0)

    def test_available_tokens_with_no_token_uses_coerces_none_to_zero(self):
        # aggregate() returns None with no rows; the property coerces to 0.
        self.assertFalse(TokenUse.objects.filter(user=self.student).exists())
        self.assertEqual(self.course_reg.available_tokens, 20.0)

    def test_available_tokens_with_zero_num_used(self):
        option = fx.make_token_use_option(self.course, tokens_required=2.0)
        fx.make_token_use(self.student, option, num_used=0)
        self.assertEqual(self.course_reg.available_tokens, 20.0)

    def test_available_tokens_with_several_uses(self):
        option_a = fx.make_token_use_option(self.course, tokens_required=2.0, assignment_name="a1")
        option_b = fx.make_token_use_option(self.course, tokens_required=5.0, assignment_name="a2")
        fx.make_token_use(self.student, option_a, num_used=3)  # 6
        fx.make_token_use(self.student, option_b, num_used=1)  # 5

        self.assertEqual(self.course_reg.available_tokens, 20.0 - 11.0)

    def test_available_tokens_ignores_other_courses_options(self):
        other_course = fx.make_course(name="Other")
        other_option = fx.make_token_use_option(other_course, tokens_required=7.0)
        fx.make_token_use(self.student, other_option, num_used=2)

        self.assertEqual(self.course_reg.available_tokens, 20.0)

    def test_available_tokens_can_go_negative(self):
        option = fx.make_token_use_option(self.course, tokens_required=30.0)
        fx.make_token_use(self.student, option, num_used=1)
        self.assertEqual(self.course_reg.available_tokens, -10.0)


class UpdateTokenUseTests(TestCase):
    """canvas/utils/token_use.py:22-38"""

    def setUp(self):
        super().setUp()
        self.category = fx.make_category()
        self.course = fx.make_course()
        self.student = fx.make_user("student")
        self.course_reg = fx.make_registration(self.student, self.course)
        practice = fx.make_question(self.category, title="p1")
        fx.set_uqj(self.student, practice, tokens_received=10.0)
        self.option = fx.make_token_use_option(
            self.course, tokens_required=3.0, maximum_number_of_use=1, assignment_name="a1"
        )

    def test_update_token_use_success_creates_row(self):
        update_token_use(self.student, self.course, {self.option.id: 2})

        token_use = TokenUse.objects.get(user=self.student, option=self.option)
        self.assertEqual(token_use.num_used, 2)
        self.assertEqual(self.course_reg.available_tokens, 10.0 - 6.0)

    def test_update_token_use_accepts_string_keys(self):
        update_token_use(self.student, self.course, {str(self.option.id): 1})
        self.assertEqual(TokenUse.objects.get(user=self.student, option=self.option).num_used, 1)

    def test_update_token_use_over_budget_raises(self):
        with self.assertRaises(TokenUseException):
            update_token_use(self.student, self.course, {self.option.id: 4})  # 12 > 10

        # nothing was written
        self.assertFalse(TokenUse.objects.filter(user=self.student).exists())

    def test_update_token_use_exactly_at_budget_is_allowed(self):
        # the guard is a strict ">" comparison
        option = fx.make_token_use_option(self.course, tokens_required=10.0, assignment_name="exact")
        update_token_use(self.student, self.course, {option.id: 1})
        self.assertEqual(TokenUse.objects.get(user=self.student, option=option).num_used, 1)

    def test_update_token_use_sets_rather_than_increments(self):
        update_token_use(self.student, self.course, {self.option.id: 2})
        update_token_use(self.student, self.course, {self.option.id: 1})

        self.assertEqual(TokenUse.objects.get(user=self.student, option=self.option).num_used, 1)
        self.assertEqual(TokenUse.objects.filter(user=self.student).count(), 1)

    def test_update_token_use_compares_against_total_not_available(self):
        # KNOWN-BUG: the budget check uses total_tokens_received, not
        # available_tokens, so a second call can overspend across options.
        option_b = fx.make_token_use_option(self.course, tokens_required=4.0, assignment_name="a2")

        update_token_use(self.student, self.course, {self.option.id: 3})  # 9 of 10
        self.assertEqual(self.course_reg.available_tokens, 1.0)

        # only 1 token is actually left, yet an 8-token purchase is accepted
        update_token_use(self.student, self.course, {option_b.id: 2})
        self.assertEqual(TokenUse.objects.get(user=self.student, option=option_b).num_used, 2)
        self.assertEqual(self.course_reg.available_tokens, 10.0 - 9.0 - 8.0)

    def test_update_token_use_ignores_maximum_number_of_use(self):
        # KNOWN-BUG: maximum_number_of_use (1 here) is never enforced.
        update_token_use(self.student, self.course, {self.option.id: 3})
        self.assertEqual(TokenUse.objects.get(user=self.student, option=self.option).num_used, 3)
        self.assertEqual(self.option.maximum_number_of_use, 1)

    def test_update_token_use_creates_the_course_registration_row(self):
        # KNOWN-BUG (side effect): get_course_registration writes a row.
        stranger = fx.make_user("stranger")
        before = CanvasCourseRegistration.objects.filter(user=stranger).count()
        self.assertEqual(before, 0)

        with self.assertRaises(TokenUseException):
            update_token_use(stranger, self.course, {self.option.id: 1})

        self.assertEqual(CanvasCourseRegistration.objects.filter(user=stranger).count(), 1)


class TokenUseEndpointTests(APITestCase):
    """POST /api/token-use/use/{course_pk}/ (api/views/token_use.py:13-32)"""

    def setUp(self):
        super().setUp()
        self.category = fx.make_category()
        self.course = fx.make_course()
        self.student = fx.make_user("student")
        self.course_reg = fx.make_registration(self.student, self.course)
        practice = fx.make_question(self.category, title="p1")
        fx.set_uqj(self.student, practice, tokens_received=10.0)
        self.option = fx.make_token_use_option(self.course, tokens_required=3.0)
        self.url = reverse("api:token-use-use-tokens", kwargs={"course_pk": self.course.pk})

    def test_use_tokens_success(self):
        self.client.force_authenticate(user=self.student)
        response = self.client.post(self.url, {str(self.option.id): 2}, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(TokenUse.objects.get(user=self.student, option=self.option).num_used, 2)

    def test_use_tokens_over_budget_is_400(self):
        self.client.force_authenticate(user=self.student)
        response = self.client.post(self.url, {str(self.option.id): 5}, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertFalse(TokenUse.objects.filter(user=self.student).exists())

    def test_use_tokens_empty_body_is_400(self):
        self.client.force_authenticate(user=self.student)
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_use_tokens_requires_authentication(self):
        response = self.client.post(self.url, {str(self.option.id): 1}, format="json")
        self.assertIn(response.status_code, (401, 403))
