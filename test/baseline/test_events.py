"""Baseline tests for canvas Events, EventSets, Goals and course registration.

Covers ``Event.calculate_tokens`` / ``Event.tokens_received`` (best-of-team,
the TOP_TEAMS cutoff, QUOTA passthrough), ``Event.has_solved_event``,
``canvas.services.event.add_question_set`` title numbering, the course
registration endpoint, Event/EventSet/Goal CRUD, serializer field sets, and the
read-endpoints-that-write side effects.
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase

from canvas.models.models import CanvasCourseRegistration, Event, EventSet
from canvas.models.goal import Goal, GoalItem
from canvas.services.event import add_question_set
from course.models.models import Question
from test.baseline import fixtures_canvas as fx


class CalculateTokensTests(TestCase):
    """canvas/models/models.py:219-230"""

    def setUp(self):
        super().setUp()
        self.category = fx.make_category()
        self.course = fx.make_course()
        self.event = fx.make_event(self.course, name="challenge", type="CHALLENGE")
        self.user_a = fx.make_user("alice")
        self.user_b = fx.make_user("bob")
        self.reg_a = fx.make_registration(self.user_a, self.course)
        self.reg_b = fx.make_registration(self.user_b, self.course)

    def test_calculate_tokens_takes_the_best_of_the_team_per_question(self):
        q1 = fx.make_question(self.category, title="q1", event=self.event)
        q2 = fx.make_question(self.category, title="q2", event=self.event)

        fx.set_uqj(self.user_a, q1, tokens_received=3.0)
        fx.set_uqj(self.user_b, q1, tokens_received=5.0)
        fx.set_uqj(self.user_a, q2, tokens_received=2.0)
        fx.set_uqj(self.user_b, q2, tokens_received=0.0)

        team = fx.make_team(self.event, "team", [self.reg_a, self.reg_b])
        self.assertEqual(self.event.calculate_tokens(team), 7.0)

    def test_calculate_tokens_only_counts_questions_of_this_event(self):
        in_event = fx.make_question(self.category, title="in", event=self.event)
        other_event = fx.make_event(self.course, name="other")
        outside = fx.make_question(self.category, title="out", event=other_event)

        fx.set_uqj(self.user_a, in_event, tokens_received=4.0)
        fx.set_uqj(self.user_a, outside, tokens_received=100.0)

        team = fx.make_team(self.event, "team", [self.reg_a])
        self.assertEqual(self.event.calculate_tokens(team), 4.0)

    def test_calculate_tokens_for_event_without_questions_is_zero(self):
        team = fx.make_team(self.event, "team", [self.reg_a])
        self.assertEqual(self.event.calculate_tokens(team), 0)

    def test_calculate_tokens_for_empty_team_is_zero(self):
        question = fx.make_question(self.category, title="q1", event=self.event)
        fx.set_uqj(self.user_a, question, tokens_received=9.0)

        empty_team = fx.make_team(self.event, "nobody", [])
        # aggregate Max over an empty queryset returns None, coerced to 0
        self.assertEqual(self.event.calculate_tokens(empty_team), 0)

    def test_calculate_tokens_ignores_non_members(self):
        question = fx.make_question(self.category, title="q1", event=self.event)
        fx.set_uqj(self.user_a, question, tokens_received=1.0)
        fx.set_uqj(self.user_b, question, tokens_received=8.0)

        team = fx.make_team(self.event, "solo", [self.reg_a])
        self.assertEqual(self.event.calculate_tokens(team), 1.0)


class TokensReceivedTests(TestCase):
    """canvas/models/models.py:232-241"""

    def setUp(self):
        super().setUp()
        self.category = fx.make_category()
        self.course = fx.make_course()
        self.users = []
        self.regs = []
        for name in ("u1", "u2", "u3"):
            user = fx.make_user(name)
            self.users.append(user)
            self.regs.append(fx.make_registration(user, self.course))

    def _event(self, challenge_type=None, challenge_type_value=None):
        return fx.make_event(
            self.course,
            name="challenge-{}-{}".format(challenge_type, challenge_type_value),
            type="CHALLENGE",
            challenge_type=challenge_type,
            challenge_type_value=challenge_type_value,
        )

    def _three_teams(self, event, scores):
        """One team per user, each scoring ``scores[i]`` on a shared question."""
        question = fx.make_question(self.category, title="q1", event=event)
        teams = []
        for index, (user, reg) in enumerate(zip(self.users, self.regs)):
            fx.set_uqj(user, question, tokens_received=scores[index])
            teams.append(fx.make_team(event, "team{}".format(index), [reg]))
        return teams

    def test_no_challenge_type_is_passthrough(self):
        event = self._event()
        teams = self._three_teams(event, [10.0, 8.0, 6.0])
        self.assertEqual([event.tokens_received(t) for t in teams], [10.0, 8.0, 6.0])

    def test_quota_is_passthrough(self):
        event = self._event(challenge_type="QUOTA", challenge_type_value=1)
        teams = self._three_teams(event, [10.0, 8.0, 6.0])
        # QUOTA ignores challenge_type_value entirely
        self.assertEqual([event.tokens_received(t) for t in teams], [10.0, 8.0, 6.0])

    def test_top_teams_cutoff_is_at_exactly_challenge_type_value(self):
        event = self._event(challenge_type="TOP_TEAMS", challenge_type_value=2)
        teams = self._three_teams(event, [10.0, 8.0, 6.0])

        # ranks 0 and 1 are inside the cutoff; the third team has 2 teams
        # strictly above it, and 2 >= 2, so it gets nothing.
        self.assertEqual(event.tokens_received(teams[0]), 10.0)
        self.assertEqual(event.tokens_received(teams[1]), 8.0)
        self.assertEqual(event.tokens_received(teams[2]), 0)

    def test_top_teams_value_one_keeps_only_the_leader(self):
        event = self._event(challenge_type="TOP_TEAMS", challenge_type_value=1)
        teams = self._three_teams(event, [10.0, 8.0, 6.0])

        self.assertEqual(event.tokens_received(teams[0]), 10.0)
        self.assertEqual(event.tokens_received(teams[1]), 0)
        self.assertEqual(event.tokens_received(teams[2]), 0)

    def test_top_teams_ties_are_not_counted_as_beating(self):
        # the comparison is strictly greater-than, so tied teams both survive
        event = self._event(challenge_type="TOP_TEAMS", challenge_type_value=1)
        teams = self._three_teams(event, [5.0, 5.0, 9.0])

        self.assertEqual(event.tokens_received(teams[2]), 9.0)
        self.assertEqual(event.tokens_received(teams[0]), 0)
        self.assertEqual(event.tokens_received(teams[1]), 0)

    def test_top_teams_with_a_single_team_always_pays_out(self):
        event = self._event(challenge_type="TOP_TEAMS", challenge_type_value=1)
        question = fx.make_question(self.category, title="q1", event=event)
        fx.set_uqj(self.users[0], question, tokens_received=4.0)
        team = fx.make_team(event, "solo", [self.regs[0]])

        self.assertEqual(event.tokens_received(team), 4.0)


class EventTokenTotalsTests(TestCase):
    """canvas/utils/utils.py:6-38"""

    def setUp(self):
        super().setUp()
        self.category = fx.make_category()
        self.course = fx.make_course()
        self.event = fx.make_event(self.course, name="event")
        self.user = fx.make_user("student")

    def test_total_tokens_of_an_empty_event_is_zero(self):
        self.assertEqual(self.event.total_tokens, 0)

    def test_total_tokens_raises_when_the_token_value_row_is_missing(self):
        # KNOWN-BUG: get_total_event_tokens passes `values("category")` (a
        # category *id*) into get_token_value -> get_token_value_object, which
        # then does TokenValue(category=<int>) and raises
        # ValueError: Cannot assign "1": "TokenValue.category" must be a
        # "QuestionCategory" instance.  Any event whose (category, difficulty)
        # TokenValue row does not exist yet 500s on serialization.
        fx.make_question(self.category, title="q1", event=self.event, ensure_token_value=False)

        with self.assertRaises(ValueError):
            self.event.total_tokens

    def test_total_tokens_sums_the_default_token_values(self):
        fx.make_question(self.category, title="q1", event=self.event, difficulty="EASY")
        fx.make_question(self.category, title="q2", event=self.event, difficulty="EASY")
        fx.make_question(self.category, title="q3", event=self.event, difficulty="HARD")

        # TokenValue defaults: EASY=1, MEDIUM=2, HARD=3
        self.assertEqual(self.event.total_tokens, 1 + 1 + 3)

    def test_total_event_grade_is_a_percentage_that_can_exceed_one_hundred(self):
        from canvas.utils.utils import get_total_event_grade

        question = fx.make_question(self.category, title="q1", event=self.event, difficulty="EASY")
        fx.set_uqj(self.user, question, tokens_received=0.5)
        self.assertEqual(get_total_event_grade(self.event, self.user), 50.0)

        fx.set_uqj(self.user, question, tokens_received=2.5)
        self.assertEqual(get_total_event_grade(self.event, self.user), 250.0)

    def test_total_event_grade_of_an_empty_event_is_zero(self):
        from canvas.utils.utils import get_total_event_grade

        self.assertEqual(get_total_event_grade(self.event, self.user), 0)

    def test_get_course_registration_creates_then_reuses_the_row(self):
        # KNOWN-BUG (side effect): this "getter" writes to the database.
        from canvas.utils.utils import get_course_registration

        self.assertEqual(CanvasCourseRegistration.objects.count(), 0)

        first = get_course_registration(self.user, self.course)
        self.assertEqual(CanvasCourseRegistration.objects.count(), 1)
        self.assertEqual(first.status, "UNREGISTERED")
        self.assertEqual(first.registration_type, "STUDENT")

        second = get_course_registration(self.user, self.course)
        self.assertEqual(second.pk, first.pk)
        self.assertEqual(CanvasCourseRegistration.objects.count(), 1)


class HasSolvedEventTests(TestCase):
    """canvas/models/models.py:274-283"""

    def setUp(self):
        super().setUp()
        self.category = fx.make_category()
        self.course = fx.make_course()
        self.event = fx.make_event(self.course, name="event")
        self.user = fx.make_user("student")

    def test_empty_event_is_vacuously_solved(self):
        # KNOWN-BUG: 0 solved == 0 questions, so an event with no questions
        # reports has_solved_event() == True for everybody.
        self.assertEqual(self.event.question_set.count(), 0)
        self.assertTrue(self.event.has_solved_event(self.user))

    def test_all_questions_solved(self):
        q1 = fx.make_question(self.category, title="q1", event=self.event)
        q2 = fx.make_question(self.category, title="q2", event=self.event)
        fx.set_uqj(self.user, q1, is_solved=True)
        fx.set_uqj(self.user, q2, is_solved=True)

        self.assertTrue(self.event.has_solved_event(self.user))

    def test_partially_solved_is_false(self):
        q1 = fx.make_question(self.category, title="q1", event=self.event)
        fx.make_question(self.category, title="q2", event=self.event)
        fx.set_uqj(self.user, q1, is_solved=True)

        self.assertFalse(self.event.has_solved_event(self.user))

    def test_another_users_solves_do_not_count(self):
        question = fx.make_question(self.category, title="q1", event=self.event)
        other = fx.make_user("other")
        fx.set_uqj(other, question, is_solved=True)

        self.assertFalse(self.event.has_solved_event(self.user))
        self.assertTrue(self.event.has_solved_event(other))

    def test_soft_deleting_a_question_makes_the_event_solved_again(self):
        q1 = fx.make_question(self.category, title="q1", event=self.event)
        q2 = fx.make_question(self.category, title="q2", event=self.event)
        fx.set_uqj(self.user, q1, is_solved=True)
        self.assertFalse(self.event.has_solved_event(self.user))

        # soft_delete() detaches the question from the event
        q2.soft_delete()
        self.assertTrue(self.event.has_solved_event(self.user))


class AddQuestionSetTests(TestCase):
    """canvas/services/event.py:111-131 — title numbering"""

    def setUp(self):
        super().setUp()
        self.category = fx.make_category()
        self.teacher = fx.make_teacher("teacher")
        self.course = fx.make_course(instructor=self.teacher)
        self.event = fx.make_event(self.course, name="event")

    def _make_practice_questions(self, count):
        return [fx.make_question(self.category, title="practice {}".format(i)) for i in range(count)]

    def test_titles_start_at_one_for_an_empty_event(self):
        self._make_practice_questions(2)
        add_question_set(self.event, self.category.id, "EASY", 2)

        titles = sorted(self.event.question_set.values_list("title", flat=True))
        self.assertEqual(titles, ["1", "2"])

    def test_used_numbers_extracted_from_existing_titles_are_skipped(self):
        fx.make_question(self.category, title="Question 2", event=self.event)
        fx.make_question(self.category, title="3 things", event=self.event)
        self._make_practice_questions(2)

        add_question_set(self.event, self.category.id, "EASY", 2)

        titles = sorted(self.event.question_set.values_list("title", flat=True))
        self.assertEqual(titles, ["1", "3 things", "4", "Question 2"])

    def test_titles_without_digits_never_collide(self):
        fx.make_question(self.category, title="no digits here", event=self.event)
        self._make_practice_questions(1)

        add_question_set(self.event, self.category.id, "EASY", 1)

        titles = sorted(self.event.question_set.values_list("title", flat=True))
        self.assertEqual(titles, ["1", "no digits here"])

    def test_only_the_first_number_of_a_title_is_considered(self):
        fx.make_question(self.category, title="1 of 5", event=self.event)
        self._make_practice_questions(1)

        add_question_set(self.event, self.category.id, "EASY", 1)

        titles = sorted(self.event.question_set.values_list("title", flat=True))
        self.assertEqual(titles, ["1 of 5", "2"])

    def test_copies_are_attached_to_the_event_and_course(self):
        self._make_practice_questions(1)
        add_question_set(self.event, self.category.id, "EASY", 1)

        copy = self.event.question_set.get(title="1")
        self.assertEqual(copy.course, self.course)
        self.assertEqual(copy.event, self.event)
        self.assertEqual(copy.author, self.teacher)
        # the source question is untouched and still a practice question
        self.assertEqual(Question.objects.filter(event=None, course=None).count(), 1)

    def test_only_matching_category_and_difficulty_are_copied(self):
        other_category = fx.make_category("other")
        fx.make_question(other_category, title="other-cat")
        fx.make_question(self.category, title="hard-one", difficulty="HARD")
        fx.make_question(self.category, title="easy-one", difficulty="EASY")

        add_question_set(self.event, self.category.id, "EASY", 5)

        self.assertEqual(list(self.event.question_set.values_list("title", flat=True)), ["1"])

    def test_unverified_practice_questions_are_not_copied(self):
        fx.make_question(self.category, title="unverified", is_verified=False)
        add_question_set(self.event, self.category.id, "EASY", 5)
        self.assertEqual(self.event.question_set.count(), 0)


class CourseRegistrationEndpointTests(APITestCase):
    """POST /api/course/{pk}/register/ (api/views/course.py:93-103)"""

    def setUp(self):
        super().setUp()
        self.student = fx.make_user("student")

    def _url(self, course):
        return reverse("api:course-register", kwargs={"pk": course.pk})

    def test_open_course_registers_without_a_code(self):
        course = fx.make_course(registration_mode="OPEN")
        self.client.force_authenticate(user=self.student)

        response = self.client.post(self._url(course), {}, format="json")

        self.assertEqual(response.status_code, 200)
        course_reg = CanvasCourseRegistration.objects.get(user=self.student, course=course)
        self.assertEqual(course_reg.status, "VERIFIED")
        self.assertTrue(response.data["is_registered"])

    def test_code_course_registers_with_the_correct_code(self):
        course = fx.make_course(registration_mode="CODE", registration_code="secret")
        self.client.force_authenticate(user=self.student)

        response = self.client.post(self._url(course), {"code": "secret"}, format="json")

        self.assertEqual(response.status_code, 200)
        course_reg = CanvasCourseRegistration.objects.get(user=self.student, course=course)
        self.assertEqual(course_reg.status, "VERIFIED")

    def test_code_course_rejects_a_wrong_code(self):
        course = fx.make_course(registration_mode="CODE", registration_code="secret")
        self.client.force_authenticate(user=self.student)

        response = self.client.post(self._url(course), {"code": "nope"}, format="json")

        self.assertEqual(response.status_code, 400)
        # the row is still created (get_course_registration side effect) but not verified
        course_reg = CanvasCourseRegistration.objects.get(user=self.student, course=course)
        self.assertEqual(course_reg.status, "UNREGISTERED")

    def test_code_course_rejects_a_missing_code(self):
        course = fx.make_course(registration_mode="CODE", registration_code="secret")
        self.client.force_authenticate(user=self.student)

        response = self.client.post(self._url(course), {}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_registration_requires_authentication(self):
        course = fx.make_course(registration_mode="OPEN")
        response = self.client.post(self._url(course), {}, format="json")
        self.assertIn(response.status_code, (401, 403))
        self.assertEqual(CanvasCourseRegistration.objects.count(), 0)


class SerializerFieldSetTests(APITestCase):
    """Field-name drift is the most common silent DRF-upgrade regression."""

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

    COURSE_FIELDS = {
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
        "secret_registration_code",
    }

    def setUp(self):
        super().setUp()
        self.category = fx.make_category()
        self.teacher = fx.make_teacher("teacher")
        self.course = fx.make_course(instructor=self.teacher)
        self.event = fx.make_event(self.course, name="event", author=self.teacher)
        self.client.force_authenticate(user=self.teacher)

    def test_event_serializer_field_names(self):
        response = self.client.get(reverse("api:event-detail", kwargs={"pk": self.event.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.data.keys()), self.EVENT_FIELDS)

    def test_course_serializer_field_names(self):
        response = self.client.get(reverse("api:course-detail", kwargs={"pk": self.course.pk}))
        self.assertEqual(response.status_code, 200)
        # registration_code is write_only, so it never appears in the output
        self.assertEqual(set(response.data.keys()), self.COURSE_FIELDS)
        self.assertNotIn("registration_code", response.data)

    def test_course_serializer_nests_the_event_serializer(self):
        response = self.client.get(reverse("api:course-detail", kwargs={"pk": self.course.pk}))
        self.assertEqual(len(response.data["events"]), 1)
        self.assertEqual(set(response.data["events"][0].keys()), self.EVENT_FIELDS)

    def test_event_set_serializer_field_names(self):
        event_set = fx.make_event_set(self.course, name="set", tokens=5.0, events=[self.event])
        response = self.client.get(reverse("api:event-set-view-detail", kwargs={"pk": event_set.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            set(response.data.keys()),
            {"id", "name", "course", "events", "tokens", "has_earn_tokens"},
        )


class EventCrudTests(APITestCase):
    """EventViewSet (api/views/event.py:25-151)"""

    def setUp(self):
        super().setUp()
        self.category = fx.make_category()
        self.teacher = fx.make_teacher("teacher")
        self.course = fx.make_course(instructor=self.teacher)
        self.client.force_authenticate(user=self.teacher)

    def _payload(self, **overrides):
        payload = {
            "name": "new event",
            "type": "ASSIGNMENT",
            "course": self.course.pk,
            "count_for_tokens": True,
            "start_date": fx.days(-1).isoformat(),
            "end_date": fx.days(5).isoformat(),
        }
        payload.update(overrides)
        return payload

    def test_create_event_sets_the_author_from_the_request(self):
        response = self.client.post(reverse("api:event-list"), self._payload(), format="json")

        self.assertEqual(response.status_code, 201)
        event = Event.objects.get(pk=response.data["id"])
        self.assertEqual(event.author, self.teacher)
        self.assertEqual(event.name, "new event")

    def test_create_event_requires_a_unique_name_per_course(self):
        fx.make_event(self.course, name="new event")
        response = self.client.post(reverse("api:event-list"), self._payload(), format="json")
        self.assertEqual(response.status_code, 400)

    def test_list_events_filtered_by_course(self):
        fx.make_event(self.course, name="a")
        other_course = fx.make_course(name="Other")
        fx.make_event(other_course, name="b")

        response = self.client.get(reverse("api:event-list"), {"course": self.course.pk})

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["name"] for item in response.data], ["a"])

    def test_patch_and_delete_event(self):
        event = fx.make_event(self.course, name="a", author=self.teacher)
        url = reverse("api:event-detail", kwargs={"pk": event.pk})

        response = self.client.patch(url, {"name": "renamed"}, format="json")
        self.assertEqual(response.status_code, 200)
        event.refresh_from_db()
        self.assertEqual(event.name, "renamed")

        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Event.objects.filter(pk=event.pk).exists())

    def test_get_event_types_and_challenge_types(self):
        types = self.client.get(reverse("api:event-get-event-types"))
        challenge_types = self.client.get(reverse("api:event-get-challenge-types"))

        self.assertEqual(types.status_code, 200)
        self.assertEqual([pair[0] for pair in types.data], ["ASSIGNMENT", "EXAM", "CHALLENGE"])
        self.assertEqual([pair[0] for pair in challenge_types.data], ["QUOTA", "TOP_TEAMS"])

    def test_add_question_set_endpoint(self):
        event = fx.make_event(self.course, name="a", author=self.teacher)
        fx.make_question(self.category, title="practice")

        response = self.client.post(
            reverse("api:event-add-question-set", kwargs={"pk": event.pk}),
            {"category": self.category.id, "difficulty": "EASY", "number_of_questions": 1},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(event.question_set.values_list("title", flat=True)), ["1"])

    def test_set_and_clear_featured(self):
        event_a = fx.make_event(self.course, name="a", author=self.teacher, featured=True)
        event_b = fx.make_event(self.course, name="b", author=self.teacher)

        response = self.client.post(reverse("api:event-set-featured", kwargs={"pk": event_b.pk}))
        self.assertEqual(response.status_code, 200)
        event_a.refresh_from_db()
        event_b.refresh_from_db()
        self.assertFalse(event_a.featured)
        self.assertTrue(event_b.featured)

        response = self.client.post(reverse("api:event-clear-featured", kwargs={"pk": event_b.pk}))
        self.assertEqual(response.status_code, 200)
        event_b.refresh_from_db()
        self.assertFalse(event_b.featured)

    def test_event_leader_board_only_lists_verified_student_teams(self):
        event = fx.make_event(self.course, name="a", author=self.teacher, type="CHALLENGE")
        question = fx.make_question(self.category, title="q1", event=event)

        student = fx.make_user("student", first_name="Stu")
        student_reg = fx.make_registration(student, self.course)
        fx.set_uqj(student, question, tokens_received=6.0)
        fx.make_team(event, "students", [student_reg])

        pending = fx.make_user("pending")
        pending_reg = fx.make_registration(pending, self.course, status="PENDING_VERIFICATION")
        fx.make_team(event, "pending", [pending_reg])

        response = self.client.get(reverse("api:event-leader-board", kwargs={"pk": event.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual([row["name"] for row in response.data], ["students"])
        self.assertEqual(response.data[0]["token"], 6.0)
        self.assertEqual(response.data[0]["member_names"], ["student"])


class EventSetCrudTests(APITestCase):
    """EventSetViewSet (api/views/eventSet.py:10-19)"""

    def setUp(self):
        super().setUp()
        self.teacher = fx.make_teacher("teacher")
        self.course = fx.make_course(instructor=self.teacher)
        self.event = fx.make_event(self.course, name="event", author=self.teacher)
        self.client.force_authenticate(user=self.teacher)

    def test_list_and_retrieve_event_sets(self):
        event_set = fx.make_event_set(self.course, name="set", tokens=5.0, events=[self.event])

        listing = self.client.get(reverse("api:event-set-view-list"))
        self.assertEqual(listing.status_code, 200)
        self.assertEqual([item["name"] for item in listing.data], ["set"])

        detail = self.client.get(reverse("api:event-set-view-detail", kwargs={"pk": event_set.pk}))
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.data["tokens"], 5.0)
        self.assertEqual([nested["id"] for nested in detail.data["events"]], [self.event.pk])

    def test_filter_event_sets_by_event(self):
        wanted = fx.make_event_set(self.course, name="wanted", tokens=1.0, events=[self.event])
        fx.make_event_set(self.course, name="unwanted", tokens=1.0, events=[])

        response = self.client.get(reverse("api:event-set-view-list"), {"events": self.event.pk})

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["id"] for item in response.data], [wanted.pk])

    def test_has_earn_tokens_reflects_solving_every_event(self):
        category = fx.make_category()
        question = fx.make_question(category, title="q1", event=self.event)
        event_set = fx.make_event_set(self.course, name="set", tokens=5.0, events=[self.event])

        detail_url = reverse("api:event-set-view-detail", kwargs={"pk": event_set.pk})
        self.assertFalse(self.client.get(detail_url).data["has_earn_tokens"])

        fx.set_uqj(self.teacher, question, is_solved=True)
        self.assertTrue(self.client.get(detail_url).data["has_earn_tokens"])

    def test_delete_event_set(self):
        event_set = fx.make_event_set(self.course, name="set", tokens=5.0, events=[])
        response = self.client.delete(reverse("api:event-set-view-detail", kwargs={"pk": event_set.pk}))

        self.assertEqual(response.status_code, 204)
        self.assertFalse(EventSet.objects.filter(pk=event_set.pk).exists())

    def test_create_event_set_is_rejected_by_the_writable_nested_serializer(self):
        # KNOWN-BUG: EventSetSerializer declares `events = EventSerializer(many=True)`
        # without read_only, so the nested payload is validated as full Event
        # objects and creation through the API is effectively impossible.
        response = self.client.post(
            reverse("api:event-set-view-list"),
            {"name": "set", "course": self.course.pk, "tokens": 5.0, "events": [self.event.pk]},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("events", response.data)
        self.assertEqual(EventSet.objects.count(), 0)


class GoalCrudTests(APITestCase):
    """GoalViewSet / GoalItemViewSet (api/views/goal.py:21-119)"""

    def setUp(self):
        super().setUp()
        self.category = fx.make_category()
        self.course = fx.make_course()
        self.student = fx.make_user("student")
        self.course_reg = fx.make_registration(self.student, self.course)
        self.client.force_authenticate(user=self.student)

    def _create_goal(self):
        return self.client.post(
            reverse("api:goal-list"),
            {"course_id": str(self.course.pk), "end_date": fx.days(7).isoformat()},
            format="json",
        )

    def test_create_goal_defaults_start_date_and_links_the_registration(self):
        response = self._create_goal()

        self.assertEqual(response.status_code, 201)
        goal = Goal.objects.get(pk=response.data["id"])
        self.assertEqual(goal.course_reg, self.course_reg)
        self.assertIsNotNone(goal.start_date)
        self.assertEqual(response.data["goal_items"], [])
        self.assertFalse(response.data["claimed"])

    def test_goal_list_is_scoped_to_the_requesting_user(self):
        self._create_goal()
        other = fx.make_user("other")
        other_reg = fx.make_registration(other, self.course)
        Goal.objects.create(course_reg=other_reg, start_date=fx.days(-1), end_date=fx.days(1))

        response = self.client.get(reverse("api:goal-list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_goal_item_creation_forces_initial_solved_to_zero(self):
        goal_id = self._create_goal().data["id"]

        response = self.client.post(
            reverse("api:goal-item-list"),
            {
                "goal": goal_id,
                "category": self.category.id,
                "difficulty": "EASY",
                "number_of_questions": 2,
                "initial_solved": 99,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        goal_item = GoalItem.objects.get(pk=response.data["id"])
        # KNOWN-BUG: GoalItem.save() always resets initial_solved to 0, so the
        # field is dead and any client-supplied value is silently dropped.
        self.assertEqual(goal_item.initial_solved, 0)
        self.assertEqual(goal_item.progress, 0)

    def test_claim_rejects_an_unfinished_goal_with_our_message(self):
        goal_id = self._create_goal().data["id"]
        self.client.post(
            reverse("api:goal-item-list"),
            {"goal": goal_id, "category": self.category.id, "difficulty": "EASY", "number_of_questions": 2},
            format="json",
        )

        response = self.client.post(reverse("api:goal-claim", kwargs={"pk": goal_id}))

        self.assertEqual(response.status_code, 400)
        self.assertIn("Goal has not been completed.", str(response.data))
        self.assertFalse(Goal.objects.get(pk=goal_id).claimed)

    def test_claim_succeeds_once_the_goal_is_complete(self):
        goal_id = self._create_goal().data["id"]
        question = fx.make_question(self.category, title="p1")
        fx.set_uqj(self.student, question, is_solved=True)
        self.client.post(
            reverse("api:goal-item-list"),
            {"goal": goal_id, "category": self.category.id, "difficulty": "EASY", "number_of_questions": 1},
            format="json",
        )

        response = self.client.post(reverse("api:goal-claim", kwargs={"pk": goal_id}))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Goal.objects.get(pk=goal_id).claimed)

    def test_goal_stats_endpoint(self):
        goal_id = self._create_goal().data["id"]
        item_id = self.client.post(
            reverse("api:goal-item-list"),
            {"goal": goal_id, "category": self.category.id, "difficulty": "EASY", "number_of_questions": 1},
            format="json",
        ).data["id"]

        response = self.client.get(reverse("api:goal-stats", kwargs={"pk": goal_id}))

        # KNOWN-BUG: canvas/services/goal.py:59 passes a MyUser instance into
        # get_solved_questions_ratio's `user_id` parameter (used as
        # `filter(user_id=...)`).  Django coerces the instance to its pk, so the
        # endpoint happens to work — pinned here so the upgrade notices if it
        # stops working.
        self.assertEqual(response.status_code, 200)
        stats = response.data[str(item_id)] if str(item_id) in response.data else response.data[item_id]
        self.assertEqual(set(stats.keys()), {"mcq", "java", "parsons", "all", "conclusion"})
        self.assertIn(stats["conclusion"]["status"], ("NO_DATA", "NEED_PRACTICE", "MASTER"))

    def test_delete_goal(self):
        goal_id = self._create_goal().data["id"]
        response = self.client.delete(reverse("api:goal-detail", kwargs={"pk": goal_id}))

        self.assertEqual(response.status_code, 204)
        self.assertFalse(Goal.objects.filter(pk=goal_id).exists())


class ReadEndpointsThatWriteTests(APITestCase):
    """Side-effect pins: GETs that mutate the database."""

    def setUp(self):
        super().setUp()
        self.category = fx.make_category()
        self.student = fx.make_user("student")
        self.course_a = fx.make_course(name="A")
        self.course_b = fx.make_course(name="B")

    def test_listing_courses_creates_registration_rows(self):
        # KNOWN-BUG: CourseListSerializer.get_is_registered -> CanvasCourse.is_registered
        # -> get_course_registration, which get-or-*creates*.  A plain GET
        # therefore writes one CanvasCourseRegistration row per visible course.
        self.assertEqual(CanvasCourseRegistration.objects.count(), 0)
        self.client.force_authenticate(user=self.student)

        response = self.client.get(reverse("api:course-list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(CanvasCourseRegistration.objects.count(), 2)
        self.assertEqual(
            set(CanvasCourseRegistration.objects.values_list("status", flat=True)),
            {"UNREGISTERED"},
        )

    def test_retrieving_a_course_creates_a_registration_row(self):
        # KNOWN-BUG: same side effect on the detail endpoint.
        self.client.force_authenticate(user=self.student)

        response = self.client.get(reverse("api:course-detail", kwargs={"pk": self.course_a.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(CanvasCourseRegistration.objects.filter(course=self.course_a).count(), 1)

    def test_listing_courses_clears_featured_on_closed_events(self):
        # KNOWN-BUG: CourseViewSet.get_queryset loops every Event in the
        # database calling update_featured(), which saves.  A read endpoint
        # writes.
        closed = fx.make_event(self.course_a, name="closed", start_offset=-10, end_offset=-1, featured=True)
        still_open = fx.make_event(self.course_a, name="open", start_offset=-1, end_offset=10, featured=True)
        self.client.force_authenticate(user=self.student)

        response = self.client.get(reverse("api:course-list"))

        self.assertEqual(response.status_code, 200)
        closed.refresh_from_db()
        still_open.refresh_from_db()
        self.assertFalse(closed.featured)
        self.assertTrue(still_open.featured)

    def test_course_event_sets_endpoint_is_broken(self):
        # KNOWN-BUG: api/views/course.py:179 uses `course.eventSets`; the
        # related_name is `event_sets`, so this raises AttributeError.
        self.client.force_authenticate(user=self.student)
        url = reverse("api:course-course-event-sets", kwargs={"pk": self.course_a.pk})

        with self.assertRaises(AttributeError):
            self.client.get(url)
