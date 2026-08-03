"""Baseline tests for the analytics / stats surface.

Covers ``canvas/services/event.py`` (``get_question_stats`` /
``get_event_stats``), the two leader-board endpoints, and
``api/services/stats.py`` together with ``/api/user-stats/``.
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase

from canvas.services.event import get_event_stats
from canvas.services.event import get_question_stats as get_event_question_stats
from api.services.stats import (
    get_category_stats,
    get_challenge_stats,
    get_goal_stats,
    get_question_stats,
    get_token_stats,
)

from test.baseline import fixtures_reporting as fx

QUESTION_STATS_KEYS = {
    "question",
    "has_variables",
    "answers",
    "error_messages",
    "submissions",
    "submission_details",
    "status_messages",
    "total_submissions",
    "num_students_attempted",
}


class EventQuestionStatsTest(TestCase):
    def setUp(self):
        super(EventQuestionStatsTest, self).setUp()
        self.category = fx.make_category("stats-cat")
        fx.make_token_value(self.category, "EASY", 2.0)

        self.teacher = fx.make_teacher("stats_teacher")
        self.course = fx.make_course("Stats Course", instructor=self.teacher)
        self.event = fx.make_event(self.course, name="Ev", type="ASSIGNMENT")

        self.solver = fx.make_student("solver", first_name="Sol", nickname="sol")
        self.wrong = fx.make_student("wrong_student", first_name="Wan", nickname="wan")
        self.partial = fx.make_student("partial_student", first_name="Pat", nickname="pat")
        self.idle = fx.make_student("idle_student", first_name="Ida", nickname="ida")

        self.question = fx.make_mcq(
            self.category,
            title="Q1",
            answer="a",
            choices={"a": "A", "b": "B", "c": "C"},
            visible_distractor_count=1,
            event=self.event,
            author=self.teacher,
        )

        fx.submit_mcq(self.solver, self.question, "a")
        fx.submit_mcq(self.wrong, self.question, "b")
        fx.submit_mcq(self.partial, self.question, "b")
        fx.force_partially_solved(fx.uqj_for(self.partial, self.question))

    def test_shape(self):
        stats = get_event_question_stats(self.question)

        self.assertEqual(set(stats.keys()), QUESTION_STATS_KEYS)
        self.assertEqual(stats["question"], {"title": "Q1", "text": "question text"})
        self.assertEqual(
            set(stats["submissions"].keys()),
            {"Correct", "Partially Correct", "Incorrect"},
        )

    def test_correct_partial_and_incorrect_counts(self):
        stats = get_event_question_stats(self.question)

        self.assertEqual(stats["submissions"]["Correct"], 1)
        self.assertEqual(stats["submissions"]["Partially Correct"], 1)
        self.assertEqual(stats["submissions"]["Incorrect"], 1)

    def test_totals_ignore_users_without_submissions(self):
        stats = get_event_question_stats(self.question)

        self.assertEqual(stats["total_submissions"], 3)
        # ``idle`` and the teacher have a UQJ but no submission.
        self.assertEqual(stats["num_students_attempted"], 3)

    def test_answer_histogram_uses_the_raw_choice_values(self):
        stats = get_event_question_stats(self.question)
        self.assertEqual(stats["answers"], {"A": 1, "B": 2})

    def test_mcq_submissions_produce_no_status_or_error_messages(self):
        stats = get_event_question_stats(self.question)

        self.assertEqual(stats["status_messages"], {})
        self.assertEqual(stats["error_messages"], {})

    def test_has_variables_is_false_for_an_empty_variable_list(self):
        self.assertFalse(get_event_question_stats(self.question)["has_variables"])

    def test_has_variables_is_true_when_variables_are_defined(self):
        question = fx.make_mcq(
            self.category,
            title="Q-vars",
            event=self.event,
            author=self.teacher,
            variables=[{"name": "x", "type": "int", "min": "1", "max": "2"}],
        )
        stats = get_event_question_stats(question)

        self.assertTrue(stats["has_variables"])
        self.assertEqual(stats["answers"], {})
        self.assertEqual(stats["total_submissions"], 0)
        self.assertEqual(stats["num_students_attempted"], 0)

    def test_submission_details_is_none_for_a_multiple_choice_question(self):
        self.assertIsNone(get_event_question_stats(self.question)["submission_details"])

    def test_submission_details_is_none_for_a_non_featured_event(self):
        java_question = fx.make_java_question(self.category, title="J1", event=self.event, author=self.teacher)
        self.assertFalse(self.event.featured)
        self.assertIsNone(get_event_question_stats(java_question)["submission_details"])

    def test_submission_details_is_a_list_for_a_featured_non_mcq_question(self):
        featured_event = fx.make_event(self.course, name="Featured", type="ASSIGNMENT", featured=True)
        java_question = fx.make_java_question(self.category, title="J2", event=featured_event, author=self.teacher)
        # still None for the MCQ living in the same featured event
        mcq = fx.make_mcq(self.category, title="M2", event=featured_event, author=self.teacher)

        self.assertEqual(get_event_question_stats(java_question)["submission_details"], [])
        self.assertIsNone(get_event_question_stats(mcq)["submission_details"])


class EventQuestionStatsMultiAnswerTest(TestCase):
    def setUp(self):
        super(EventQuestionStatsMultiAnswerTest, self).setUp()
        self.category = fx.make_category("multi-cat")
        self.teacher = fx.make_teacher("multi_teacher")
        self.course = fx.make_course("Multi Course", instructor=self.teacher)
        self.event = fx.make_event(self.course, name="Multi", type="ASSIGNMENT")
        self.student = fx.make_student("multi_student", first_name="Mia")

        self.question = fx.make_mcq(
            self.category,
            title="Checkbox",
            answer="a,b",
            choices={"a": "A", "b": "B", "c": "C", "d": "D"},
            visible_distractor_count=2,
            event=self.event,
            author=self.teacher,
        )

    def test_multi_answer_submission_breaks_the_answer_histogram(self):
        fx.submit_mcq(self.student, self.question, "a,b")

        # KNOWN-BUG: canvas/services/event.py:65 does ``choices[submission.answer]``
        # so any checkbox (comma separated) answer raises KeyError, taking down
        # /api/event/{pk}/stats/ with a 500.
        with self.assertRaises(KeyError):
            get_event_question_stats(self.question)

    def test_empty_answer_submission_breaks_the_answer_histogram(self):
        fx.submit_mcq(self.student, self.question, "")

        # KNOWN-BUG: same line - an empty answer string is not a choice key either.
        with self.assertRaises(KeyError):
            get_event_question_stats(self.question)


class EventStatsOrderingTest(TestCase):
    def setUp(self):
        super(EventStatsOrderingTest, self).setUp()
        self.category = fx.make_category("order-cat")
        self.teacher = fx.make_teacher("order_teacher")
        self.course = fx.make_course("Order Course", instructor=self.teacher)
        self.event = fx.make_event(self.course, name="Ordered", type="ASSIGNMENT")

        # created out of alphabetical order on purpose
        fx.make_mcq(self.category, title="Zed", event=self.event, author=self.teacher)
        fx.make_mcq(self.category, title="Alpha", event=self.event, author=self.teacher)
        fx.make_mcq(self.category, title="Mike", event=self.event, author=self.teacher)

    def test_event_stats_is_ordered_by_title(self):
        stats = get_event_stats(self.event)

        # explicit ``order_by("title")`` in the service -> assert exact order
        self.assertEqual([row["question"]["title"] for row in stats], ["Alpha", "Mike", "Zed"])
        for row in stats:
            self.assertEqual(set(row.keys()), QUESTION_STATS_KEYS)

    def test_event_stats_is_empty_for_an_event_without_questions(self):
        empty = fx.make_event(self.course, name="Nothing", type="ASSIGNMENT")
        self.assertEqual(get_event_stats(empty), [])


class EventStatsEndpointTest(APITestCase):
    def setUp(self):
        super(EventStatsEndpointTest, self).setUp()
        self.category = fx.make_category("ep-cat")
        self.teacher = fx.make_teacher("ep_teacher")
        self.course = fx.make_course("Ep Course", instructor=self.teacher)
        self.event = fx.make_event(self.course, name="Ep", type="ASSIGNMENT")
        self.student = fx.make_student("ep_student", first_name="Eve")
        fx.register(self.course, self.student)
        self.question = fx.make_mcq(self.category, title="EQ", event=self.event, author=self.teacher)
        fx.submit_mcq(self.student, self.question, "a")

        self.url = reverse("api:event-stats", kwargs={"pk": self.event.pk})

    def test_requires_authentication(self):
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [401, 403])

    def test_teacher_gets_the_stats(self):
        self.client.force_authenticate(user=self.teacher)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(set(response.data[0].keys()), QUESTION_STATS_KEYS)
        self.assertEqual(response.data[0]["submissions"]["Correct"], 1)

    def test_any_authenticated_user_can_read_event_stats(self):
        # the EventViewSet permissions only gate writes, so a student sees them too
        self.client.force_authenticate(user=self.student)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_unknown_event_is_404(self):
        self.client.force_authenticate(user=self.teacher)
        response = self.client.get(reverse("api:event-stats", kwargs={"pk": 999999}))
        self.assertEqual(response.status_code, 404)


class CourseLeaderBoardTest(APITestCase):
    def setUp(self):
        super(CourseLeaderBoardTest, self).setUp()
        self.category = fx.make_category("lb-cat")
        fx.make_token_value(self.category, "EASY", 2.0)

        self.teacher = fx.make_teacher("lb_teacher")
        self.course = fx.make_course("LB Course", instructor=self.teacher)
        self.counted_event = fx.make_event(self.course, name="Counted", type="ASSIGNMENT", count_for_tokens=True)

        self.alice = fx.make_student("lb_alice", first_name="Alice", last_name="Anderson", nickname="al")
        self.bob = fx.make_student("lb_bob", first_name="Bob", last_name="Brown", nickname="bo")
        self.ta = fx.make_student("lb_ta", first_name="Tara", last_name="Assistant")
        self.pending = fx.make_student("lb_pending", first_name="Penny", last_name="Pending")

        self.alice_reg = fx.register(self.course, self.alice)
        self.bob_reg = fx.register(self.course, self.bob)
        fx.register(self.course, self.ta, registration_type="TA")
        fx.register(self.course, self.pending, status="PENDING_VERIFICATION")

        # a practice question (no course, no event) is what feeds token totals
        self.practice = fx.make_mcq(self.category, title="Practice", author=self.teacher)
        fx.set_uqj_tokens(fx.uqj_for(self.alice, self.practice), 3.0, is_solved=True)

        self.url = reverse("api:course-leader-board", kwargs={"pk": self.course.pk})

    def test_requires_authentication(self):
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [401, 403])

    def test_shape_and_membership(self):
        self.client.force_authenticate(user=self.teacher)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.data.keys()), {"board", "excluded_values"})

        board = response.data["board"]
        self.assertEqual(len(board), 2)
        for row in board:
            self.assertEqual(set(row.keys()), {"name", "token", "course_reg_id"})

        # the queryset has no explicit ordering -> compare as a set
        self.assertEqual({row["name"] for row in board}, {"Alice Anderson", "Bob Brown"})

    def test_only_verified_students_are_listed(self):
        self.client.force_authenticate(user=self.teacher)
        names = {row["name"] for row in self.client.get(self.url).data["board"]}

        self.assertNotIn("Tara Assistant", names)
        self.assertNotIn("Penny Pending", names)

    def test_tokens_come_from_total_tokens_received(self):
        self.client.force_authenticate(user=self.teacher)
        board = {row["name"]: row for row in self.client.get(self.url).data["board"]}

        self.assertEqual(board["Alice Anderson"]["token"], 3.0)
        self.assertEqual(board["Bob Brown"]["token"], 0)
        self.assertEqual(board["Alice Anderson"]["course_reg_id"], self.alice_reg.id)

    def test_excluded_values_flag(self):
        self.client.force_authenticate(user=self.teacher)
        self.assertFalse(self.client.get(self.url).data["excluded_values"])

        fx.make_event(self.course, name="Uncounted", type="ASSIGNMENT", count_for_tokens=False)
        self.assertTrue(self.client.get(self.url).data["excluded_values"])

    def test_students_can_read_the_leader_board(self):
        self.client.force_authenticate(user=self.alice)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_unknown_course_is_404(self):
        self.client.force_authenticate(user=self.teacher)
        response = self.client.get(reverse("api:course-leader-board", kwargs={"pk": 999999}))
        self.assertEqual(response.status_code, 404)


class EventLeaderBoardTest(APITestCase):
    def setUp(self):
        super(EventLeaderBoardTest, self).setUp()
        self.category = fx.make_category("elb-cat")
        fx.make_token_value(self.category, "EASY", 2.0)

        self.teacher = fx.make_teacher("elb_teacher")
        self.course = fx.make_course("ELB Course", instructor=self.teacher)
        self.event = fx.make_event(self.course, name="Challenge", type="CHALLENGE", count_for_tokens=True)

        self.alice = fx.make_student("elb_alice", first_name="Alice", nickname="al")
        self.anon = fx.make_student("elb_anon", nickname="anon-nick")  # no first name
        self.ta = fx.make_student("elb_ta", first_name="Tara")

        self.alice_reg = fx.register(self.course, self.alice)
        self.anon_reg = fx.register(self.course, self.anon)
        self.ta_reg = fx.register(self.course, self.ta, registration_type="TA")

        self.question = fx.make_mcq(self.category, title="CQ", event=self.event, author=self.teacher)
        fx.set_uqj_tokens(fx.uqj_for(self.alice, self.question), 2.0, is_solved=True)

        self.student_team = fx.make_team(
            self.event, name="Students", course_registrations=[self.alice_reg, self.anon_reg]
        )
        self.ta_team = fx.make_team(self.event, name="TAs", course_registrations=[self.ta_reg])
        self.empty_team = fx.make_team(self.event, name="Nobody")

        self.url = reverse("api:event-leader-board", kwargs={"pk": self.event.pk})

    def test_requires_authentication(self):
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [401, 403])

    def test_only_teams_with_a_verified_student_are_listed(self):
        self.client.force_authenticate(user=self.teacher)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Students")
        self.assertEqual(set(response.data[0].keys()), {"name", "token", "member_names", "team_id"})
        self.assertEqual(response.data[0]["team_id"], self.student_team.id)

    def test_token_is_the_best_of_team_score(self):
        self.client.force_authenticate(user=self.teacher)
        response = self.client.get(self.url)
        self.assertEqual(response.data[0]["token"], 2.0)

    def test_member_names_fall_back_to_anonymous(self):
        self.client.force_authenticate(user=self.teacher)
        member_names = self.client.get(self.url).data[0]["member_names"]

        # M2M iteration order is not explicit -> compare as a set
        self.assertEqual(set(member_names), {"al", "Anonymous User"})

    def test_event_without_teams_returns_an_empty_list(self):
        other = fx.make_event(self.course, name="Lonely", type="CHALLENGE")
        self.client.force_authenticate(user=self.teacher)
        response = self.client.get(reverse("api:event-leader-board", kwargs={"pk": other.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])


class UserStatsServiceTest(TestCase):
    def setUp(self):
        super(UserStatsServiceTest, self).setUp()
        self.cat_a = fx.make_category("cat-a")
        self.cat_b = fx.make_category("cat-b")
        fx.make_token_value(self.cat_a, "EASY", 2.0)
        fx.make_token_value(self.cat_a, "MEDIUM", 3.0)

        self.teacher = fx.make_teacher("us_teacher")
        self.student = fx.make_student("us_student", first_name="Sam", last_name="Student")

        # practice questions only (no event) - that is all the stats layer counts
        self.q_easy = fx.make_mcq(self.cat_a, title="PE", difficulty="EASY", author=self.teacher)
        self.q_medium = fx.make_mcq(self.cat_a, title="PM", difficulty="MEDIUM", author=self.teacher)
        self.q_java = fx.make_java_question(self.cat_a, title="PJ", author=self.teacher)

        fx.submit_mcq(self.student, self.q_easy, "a")  # correct
        fx.submit_mcq(self.student, self.q_medium, "b")  # incorrect

        self.course = fx.make_course("US Course", instructor=self.teacher)
        self.other_course = fx.make_course("Other Course", instructor=self.teacher)
        self.ta_course = fx.make_course("TA Course", instructor=self.teacher)
        fx.register(self.course, self.student)
        fx.register(self.other_course, self.student, status="PENDING_VERIFICATION")
        fx.register(self.ta_course, self.student, registration_type="TA")

    # -- get_category_stats -------------------------------------------------

    def test_category_stats_shape(self):
        stats = get_category_stats(self.student)

        # 2 categories x (3 difficulties + ALL)
        self.assertEqual(len(stats), 8)
        for row in stats:
            self.assertEqual(
                set(row.keys()),
                {"category", "difficulty", "questions_attempt", "questions_solved", "avgSuccess"},
            )
        self.assertEqual({row["category"] for row in stats}, {self.cat_a.id, self.cat_b.id})

    def test_category_stats_difficulty_sequence_per_category(self):
        stats = get_category_stats(self.student)
        # DIFFICULTY_CHOICES ordering is explicit in the service, ALL is appended
        self.assertEqual(
            [row["difficulty"] for row in stats[:4]],
            ["EASY", "MEDIUM", "HARD", "ALL"],
        )

    def test_category_stats_values(self):
        stats = {(row["category"], row["difficulty"]): row for row in get_category_stats(self.student)}

        easy = stats[(self.cat_a.id, "EASY")]
        self.assertEqual(easy["questions_solved"], 1)
        self.assertEqual(easy["questions_attempt"], 1)
        self.assertEqual(easy["avgSuccess"], 1.0)

        medium = stats[(self.cat_a.id, "MEDIUM")]
        self.assertEqual(medium["questions_solved"], 0)
        self.assertEqual(medium["questions_attempt"], 1)
        self.assertEqual(medium["avgSuccess"], 0)

        hard = stats[(self.cat_a.id, "HARD")]
        self.assertEqual((hard["questions_solved"], hard["questions_attempt"], hard["avgSuccess"]), (0, 0, 0))

        all_a = stats[(self.cat_a.id, "ALL")]
        self.assertEqual(all_a["questions_solved"], 1)
        self.assertEqual(all_a["questions_attempt"], 2)
        self.assertEqual(all_a["avgSuccess"], 0.5)

        empty_category = stats[(self.cat_b.id, "ALL")]
        self.assertEqual(empty_category["questions_attempt"], 0)
        self.assertEqual(empty_category["avgSuccess"], 0)

    # -- get_question_stats -------------------------------------------------

    def test_question_stats_shape(self):
        stats = get_question_stats(self.student)

        self.assertEqual(set(stats.keys()), {"mcq", "java", "parsons"})
        for key in stats:
            self.assertEqual(
                set(stats[key].keys()),
                {"questions_attempt", "questions_solved", "avgSuccess"},
            )

    def test_question_stats_values(self):
        stats = get_question_stats(self.student)

        self.assertEqual(stats["mcq"]["questions_attempt"], 2)
        self.assertEqual(stats["mcq"]["questions_solved"], 1)
        self.assertEqual(stats["mcq"]["avgSuccess"], 0.5)

        # the java question exists but was never attempted
        self.assertEqual(stats["java"], {"questions_attempt": 0, "questions_solved": 0, "avgSuccess": 0})
        self.assertEqual(stats["parsons"], {"questions_attempt": 0, "questions_solved": 0, "avgSuccess": 0})

    # -- get_challenge_stats ------------------------------------------------

    def test_challenge_stats_shape_with_no_challenges(self):
        self.assertEqual(get_challenge_stats(self.student), {"challenges_completed": 0})

    def test_challenge_stats_counts_solved_challenges(self):
        unsolved = fx.make_event(self.course, name="C-unsolved", type="CHALLENGE")
        fx.make_mcq(self.cat_a, title="CQ1", event=unsolved, author=self.teacher)
        solved = fx.make_event(self.course, name="C-solved", type="CHALLENGE")
        solved_question = fx.make_mcq(self.cat_a, title="CQ2", event=solved, author=self.teacher)

        self.assertEqual(get_challenge_stats(self.student), {"challenges_completed": 0})

        fx.set_uqj_tokens(fx.uqj_for(self.student, solved_question), 2.0, is_solved=True)
        self.assertEqual(get_challenge_stats(self.student), {"challenges_completed": 1})

    def test_empty_challenge_counts_as_solved(self):
        fx.make_event(self.course, name="C-empty", type="CHALLENGE")

        # KNOWN-BUG: Event.has_solved_event compares solved-UQJ count with the
        # question count, so a CHALLENGE event with zero questions is vacuously
        # "solved" for every user and inflates challenges_completed.
        self.assertEqual(get_challenge_stats(self.student), {"challenges_completed": 1})

    # -- get_token_stats / get_goal_stats -----------------------------------

    def test_token_stats_only_covers_verified_student_registrations(self):
        stats = get_token_stats(self.student)

        self.assertEqual(len(stats), 1)
        self.assertEqual(set(stats[0].keys()), {"course_name", "tokens"})
        self.assertEqual(stats[0]["course_name"], "US Course")

    def test_token_stats_value(self):
        uqj = fx.uqj_for(self.student, self.q_easy)
        fx.set_uqj_tokens(uqj, 7.0, is_solved=True)

        stats = get_token_stats(self.student)
        self.assertEqual(stats[0]["tokens"], 7.0)

    def test_goal_stats_is_hardcoded(self):
        self.assertEqual(get_goal_stats(self.student), {"goals_completed": 0})


class UserStatsEndpointTest(APITestCase):
    def setUp(self):
        super(UserStatsEndpointTest, self).setUp()
        self.category = fx.make_category("use-cat")
        self.teacher = fx.make_teacher("use_teacher")
        self.student = fx.make_student("use_student", first_name="Uma", last_name="User")
        self.question = fx.make_mcq(self.category, title="UQ", author=self.teacher)
        fx.submit_mcq(self.student, self.question, "a")

        self.url = reverse("api:user-stats-list")

    def test_requires_authentication(self):
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [401, 403])

    def test_payload_shape(self):
        self.client.force_authenticate(user=self.student)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            set(response.data.keys()),
            {"token_stats", "challenge_stats", "goal_stats", "question_stats", "category_stats"},
        )
        self.assertEqual(response.data["goal_stats"], {"goals_completed": 0})
        self.assertEqual(response.data["challenge_stats"], {"challenges_completed": 0})
        self.assertEqual(response.data["token_stats"], [])
        self.assertEqual(response.data["question_stats"]["mcq"]["questions_solved"], 1)
        self.assertEqual(len(response.data["category_stats"]), 4)

    def test_category_difficulty_endpoint(self):
        self.client.force_authenticate(user=self.student)
        url = reverse("api:user-stats-difficulty", kwargs={"category_pk": self.category.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        # explicit ordering in the view: DIFFICULTY_CHOICES then ALL
        self.assertEqual(
            [row["difficulty"] for row in response.data],
            ["EASY", "MEDIUM", "HARD", "ALL"],
        )
        self.assertEqual(response.data[0]["avgSuccess"], 1.0)
