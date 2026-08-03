"""Baseline tests for the gradebook service and the gradebook API endpoints.

Covers ``canvas/services/gradebook.py`` (``get_student_gradebook`` /
``get_course_gradebook``) and ``/api/course/{pk}/grade-book/``.
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase

from canvas.services.gradebook import get_course_gradebook, get_student_gradebook

from test.baseline import fixtures_reporting as fx


class GradebookFixtureMixin(object):
    """Small course with one ASSIGNMENT, one EXAM and one CHALLENGE event."""

    def build_course(self):
        self.category = fx.make_category("gradebook-cat")
        # Pin the token value so ``total`` / ``grade`` are exact numbers.
        fx.make_token_value(self.category, "EASY", 2.0)

        self.teacher = fx.make_teacher("gb_teacher")
        self.course = fx.make_course("GB Course", instructor=self.teacher)

        self.assignment = fx.make_event(self.course, name="A1", type="ASSIGNMENT")
        self.exam = fx.make_event(self.course, name="E1", type="EXAM")
        self.challenge = fx.make_event(self.course, name="C1", type="CHALLENGE")

        self.alice = fx.make_student("alice", first_name="Alice", last_name="Anderson", nickname="al")
        self.bob = fx.make_student("bob")

        self.alice_reg = fx.register(self.course, self.alice)
        self.bob_reg = fx.register(self.course, self.bob)

        self.q_a1 = fx.make_mcq(self.category, title="A1-Q1", event=self.assignment, author=self.teacher)
        self.q_a2 = fx.make_mcq(self.category, title="A1-Q2", event=self.assignment, author=self.teacher)
        self.q_e1 = fx.make_mcq(self.category, title="E1-Q1", event=self.exam, author=self.teacher)
        self.q_c1 = fx.make_mcq(self.category, title="C1-Q1", event=self.challenge, author=self.teacher)

        # Alice answers A1-Q1 correctly: grade 1.0 x token value 2.0 = 2.0 tokens.
        fx.submit_mcq(self.alice, self.q_a1, "a")


class GetStudentGradebookTest(GradebookFixtureMixin, TestCase):
    def setUp(self):
        super(GetStudentGradebookTest, self).setUp()
        self.build_course()

    def test_only_assignment_and_exam_events_are_reported(self):
        result = get_student_gradebook(self.alice_reg, self.course)

        self.assertEqual(len(result), 2)
        # ``course.events.filter(...)`` has no explicit ``order_by`` so the row
        # order is queryset-default; compare as a set.
        self.assertEqual({row["event_name"] for row in result}, {"A1", "E1"})
        self.assertNotIn("C1", [row["event_name"] for row in result])

    def test_row_shape(self):
        result = get_student_gradebook(self.alice_reg, self.course)

        for row in result:
            self.assertEqual(
                set(row.keys()),
                {"grade", "total", "name", "event_name", "question_details"},
            )
            for detail in row["question_details"]:
                self.assertEqual(
                    set(detail.keys()),
                    {"title", "question_grade", "question_value", "attempts", "max_attempts"},
                )

    def test_totals_and_grades(self):
        rows = {row["event_name"]: row for row in get_student_gradebook(self.alice_reg, self.course)}

        # A1 has 2 EASY questions worth 2.0 each.
        self.assertEqual(rows["A1"]["total"], 4.0)
        self.assertEqual(rows["A1"]["grade"], 2.0)

        # E1 has 1 EASY question, nothing submitted.
        self.assertEqual(rows["E1"]["total"], 2.0)
        self.assertEqual(rows["E1"]["grade"], 0)

    def test_question_details(self):
        rows = {row["event_name"]: row for row in get_student_gradebook(self.alice_reg, self.course)}
        details = rows["A1"]["question_details"]

        self.assertEqual(len(details), 2)
        # UQJ iteration order is not explicitly ordered -> compare as a set.
        self.assertEqual({d["title"] for d in details}, {"A1-Q1", "A1-Q2"})

        by_title = {d["title"]: d for d in details}
        self.assertEqual(by_title["A1-Q1"]["question_grade"], 2.0)
        self.assertEqual(by_title["A1-Q1"]["question_value"], 2.0)
        self.assertEqual(by_title["A1-Q1"]["attempts"], 1)
        self.assertEqual(by_title["A1-Q1"]["max_attempts"], 10)

        self.assertEqual(by_title["A1-Q2"]["question_grade"], 0)
        self.assertEqual(by_title["A1-Q2"]["attempts"], 0)

    def test_name_uses_registration_full_name(self):
        alice_rows = get_student_gradebook(self.alice_reg, self.course)
        bob_rows = get_student_gradebook(self.bob_reg, self.course)

        self.assertEqual({row["name"] for row in alice_rows}, {"Alice Anderson"})
        # Bob has no first name -> CanvasCourseRegistration.full_name fallback.
        self.assertEqual({row["name"] for row in bob_rows}, {"Anonymous Student"})

    def test_event_without_questions_yields_empty_details(self):
        empty_event = fx.make_event(self.course, name="A2", type="ASSIGNMENT")
        rows = {row["event_name"]: row for row in get_student_gradebook(self.alice_reg, self.course)}

        self.assertIn("A2", rows)
        self.assertEqual(rows["A2"]["question_details"], [])
        self.assertEqual(rows["A2"]["grade"], 0)
        self.assertEqual(rows["A2"]["total"], 0)
        self.assertEqual(empty_event.question_set.count(), 0)


class GetCourseGradebookTest(GradebookFixtureMixin, TestCase):
    def setUp(self):
        super(GetCourseGradebookTest, self).setUp()
        self.build_course()

    def test_covers_every_verified_student(self):
        result = get_course_gradebook(self.course)

        # 2 verified students x 2 non-challenge events.
        self.assertEqual(len(result), 4)
        self.assertEqual({row["name"] for row in result}, {"Alice Anderson", "Anonymous Student"})
        self.assertEqual({row["event_name"] for row in result}, {"A1", "E1"})

    def test_excludes_non_verified_and_non_student_registrations(self):
        ta = fx.make_student("ta_user", first_name="Tara", last_name="Assistant")
        fx.register(self.course, ta, status="VERIFIED", registration_type="TA")
        pending = fx.make_student("pending_user", first_name="Penny", last_name="Pending")
        fx.register(self.course, pending, status="PENDING_VERIFICATION")

        result = get_course_gradebook(self.course)

        self.assertEqual(len(result), 4)
        names = {row["name"] for row in result}
        self.assertNotIn("Tara Assistant", names)
        self.assertNotIn("Penny Pending", names)

    def test_challenge_events_are_excluded_for_every_student(self):
        result = get_course_gradebook(self.course)
        self.assertNotIn("C1", {row["event_name"] for row in result})


class GradeBookEndpointTest(GradebookFixtureMixin, APITestCase):
    def setUp(self):
        super(GradeBookEndpointTest, self).setUp()
        self.build_course()
        self.url = reverse("api:course-course-grade-book", kwargs={"pk": self.course.pk})

    def test_requires_authentication(self):
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [401, 403])

    def test_teacher_can_read_the_course_gradebook(self):
        self.client.force_authenticate(user=self.teacher)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 4)
        self.assertEqual({row["event_name"] for row in response.data}, {"A1", "E1"})

    def test_student_is_denied(self):
        self.client.force_authenticate(user=self.alice)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_course_instructor_registration_can_read(self):
        instructor = fx.make_student("gb_instructor", first_name="Ivy", last_name="Instructor")
        fx.register(self.course, instructor, status="VERIFIED", registration_type="INSTRUCTOR")

        self.client.force_authenticate(user=instructor)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
