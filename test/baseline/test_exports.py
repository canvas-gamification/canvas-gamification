"""Baseline tests for the CSV export surface.

Covers:
  * ``/api/course/{pk}/export-grade-book/`` (hand-rolled csv writer,
    ``api/views/course.py:195-280``)
  * the five ``rest_framework_csv`` export endpoints wired through
    ``api/renderers.py::CSVRenderer``.

CSV column ORDER for the ``rest_framework_csv`` endpoints depends on dict
iteration inside ``tablize``/the serializer field map rather than an explicit
ordering, so header assertions below compare SETS. The hand-rolled gradebook
writer emits a literal python list, so that header is asserted exactly.
"""

import csv
import datetime
import io

from django.urls import reverse
from rest_framework.test import APITestCase

from test.baseline import fixtures_reporting as fx

OLD = datetime.datetime(2000, 1, 1, 12, 0, tzinfo=datetime.timezone.utc)
NEW = datetime.datetime(2099, 1, 1, 12, 0, tzinfo=datetime.timezone.utc)
BEFORE_OLD = "1999-01-01 00:00:00"
AFTER_OLD = "2010-01-01 00:00:00"
BEFORE_NEW = "2090-01-01 00:00:00"


def parse_csv(response):
    """Return the CSV body as a list of rows (first row is the header)."""
    body = response.content.decode("utf-8")
    return [row for row in csv.reader(io.StringIO(body)) if row]


class ExportGradeBookTest(APITestCase):
    def setUp(self):
        super(ExportGradeBookTest, self).setUp()
        self.category = fx.make_category("export-cat")
        fx.make_token_value(self.category, "EASY", 2.0)

        self.teacher = fx.make_teacher("xgb_teacher")
        self.course = fx.make_course("GB Course", instructor=self.teacher)

        self.assignment = fx.make_event(self.course, name="A1", type="ASSIGNMENT")
        self.exam = fx.make_event(self.course, name="E1", type="EXAM")

        self.alice = fx.make_student("alice", first_name="Alice", last_name="Anderson")
        self.bob = fx.make_student("bob", first_name="Bob", last_name="Brown")
        self.alice_reg = fx.register(self.course, self.alice)
        self.bob_reg = fx.register(self.course, self.bob)

        self.q_a1 = fx.make_mcq(self.category, title="A1-Q1", event=self.assignment, author=self.teacher)
        self.q_a2 = fx.make_mcq(self.category, title="A1-Q2", event=self.assignment, author=self.teacher)
        self.q_e1 = fx.make_mcq(self.category, title="E1-Q1", event=self.exam, author=self.teacher)

        fx.submit_mcq(self.alice, self.q_a1, "a")

        self.url = reverse("api:course-export-grade-book", kwargs={"pk": self.course.pk})
        self.client.force_authenticate(user=self.teacher)

    # -- access control -----------------------------------------------------

    def test_requires_authentication(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [401, 403])

    def test_student_is_denied(self):
        self.client.force_authenticate(user=self.alice)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    # -- headers ------------------------------------------------------------

    def test_summary_header_has_four_columns(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        rows = parse_csv(response)
        self.assertEqual(rows[0], ["Event Name", "Student Name", "Grade", "Total"])
        # 2 students x 2 events + header
        self.assertEqual(len(rows), 5)
        for row in rows[1:]:
            self.assertEqual(len(row), 4)

    def test_details_header_has_nine_columns(self):
        response = self.client.get(self.url, {"details": "true"})

        self.assertEqual(response.status_code, 200)
        rows = parse_csv(response)
        self.assertEqual(
            rows[0],
            [
                "Event Name",
                "Student Name",
                "Grade",
                "Total",
                "Question Title",
                "Question Grade",
                "Question Value",
                "Attempts",
                "Max Attempts",
            ],
        )
        # header + per student: A1 (2 questions -> 2 rows) + E1 (1 question -> 1 row)
        self.assertEqual(len(rows), 1 + 2 * 3)
        for row in rows[1:]:
            self.assertEqual(len(row), 9)

    def test_details_continuation_rows_blank_the_first_four_columns(self):
        response = self.client.get(self.url, {"details": "true", "event_name": "A1", "student_name": "Alice"})
        rows = parse_csv(response)

        self.assertEqual(len(rows), 3)  # header + 2 question rows
        self.assertEqual(rows[1][0], "A1")
        self.assertEqual(rows[1][1], "Alice Anderson")
        self.assertEqual(rows[2][:4], ["", "", "", ""])

    def test_details_flag_is_an_exact_string_match(self):
        # anything other than the literal "true" falls back to the 4 column form
        for value in ["True", "1", "yes", "false"]:
            response = self.client.get(self.url, {"details": value})
            rows = parse_csv(response)
            self.assertEqual(rows[0], ["Event Name", "Student Name", "Grade", "Total"], value)

    # -- filtering ----------------------------------------------------------

    def test_event_name_filter_is_an_exact_match(self):
        response = self.client.get(self.url, {"event_name": "A1"})
        rows = parse_csv(response)

        self.assertEqual(len(rows), 3)  # header + 1 row per student
        self.assertEqual({row[0] for row in rows[1:]}, {"A1"})

    def test_event_name_filter_does_not_do_substring_matching(self):
        response = self.client.get(self.url, {"event_name": "A"})
        rows = parse_csv(response)
        self.assertEqual(len(rows), 1)  # header only

    def test_student_name_filter_is_a_case_insensitive_substring(self):
        for needle in ["alice", "ALICE", "Alice", "ander", "e And"]:
            response = self.client.get(self.url, {"student_name": needle})
            rows = parse_csv(response)
            self.assertEqual(len(rows), 3, needle)  # header + A1 + E1
            self.assertEqual({row[1] for row in rows[1:]}, {"Alice Anderson"}, needle)

    def test_student_name_filter_can_match_several_students(self):
        response = self.client.get(self.url, {"student_name": "n"})
        rows = parse_csv(response)
        # "Alice Anderson" and "Bob Brown" both contain an "n"
        self.assertEqual({row[1] for row in rows[1:]}, {"Alice Anderson", "Bob Brown"})

    def test_filters_combine(self):
        response = self.client.get(self.url, {"event_name": "E1", "student_name": "bob"})
        rows = parse_csv(response)

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[1][:2], ["E1", "Bob Brown"])

    # -- Content-Disposition ------------------------------------------------

    def test_content_disposition_default(self):
        response = self.client.get(self.url)
        self.assertEqual(
            response["Content-Disposition"],
            'attachment; filename="GB Course course gradebook.csv"',
        )

    def test_content_disposition_with_event_name(self):
        response = self.client.get(self.url, {"event_name": "A1"})
        self.assertEqual(
            response["Content-Disposition"],
            'attachment; filename="GB Course A1 gradebook.csv"',
        )

    def test_content_disposition_with_student_name(self):
        response = self.client.get(self.url, {"student_name": "alice"})
        self.assertEqual(
            response["Content-Disposition"],
            'attachment; filename="GB Course alice students course gradebook.csv"',
        )

    def test_content_disposition_with_details(self):
        response = self.client.get(self.url, {"details": "true"})
        self.assertEqual(
            response["Content-Disposition"],
            'attachment; filename="GB Course course gradebook detailed.csv"',
        )

    def test_content_disposition_with_everything(self):
        response = self.client.get(
            self.url,
            {"details": "true", "event_name": "A1", "student_name": "alice"},
        )
        self.assertEqual(
            response["Content-Disposition"],
            'attachment; filename="GB Course alice students A1 gradebook detailed.csv"',
        )


class ExportGradeBookEmptyEventTest(APITestCase):
    """Isolates the ``question_details[0]`` crash on an event with no questions."""

    def setUp(self):
        super(ExportGradeBookEmptyEventTest, self).setUp()
        self.teacher = fx.make_teacher("empty_teacher")
        self.course = fx.make_course("Empty Course", instructor=self.teacher)
        self.empty_event = fx.make_event(self.course, name="Empty", type="ASSIGNMENT")
        self.student = fx.make_student("empty_student", first_name="Ed", last_name="Empty")
        fx.register(self.course, self.student)

        self.url = reverse("api:course-export-grade-book", kwargs={"pk": self.course.pk})
        self.client.force_authenticate(user=self.teacher)

    def test_summary_export_handles_an_event_without_questions(self):
        response = self.client.get(self.url)
        rows = parse_csv(response)

        self.assertEqual(rows[0], ["Event Name", "Student Name", "Grade", "Total"])
        self.assertEqual(rows[1], ["Empty", "Ed Empty", "0", "0"])

    def test_details_export_crashes_on_an_event_without_questions(self):
        # KNOWN-BUG: api/views/course.py:258 indexes ``question_details[0]``
        # unconditionally, so ``?details=true`` raises IndexError (HTTP 500) for
        # any ASSIGNMENT/EXAM event that has no questions.
        with self.assertRaises(IndexError):
            self.client.get(self.url, {"details": "true"})


class CsvExportEndpointsTest(APITestCase):
    """The five ``CSVRenderer`` backed export viewsets."""

    def setUp(self):
        super(CsvExportEndpointsTest, self).setUp()
        self.teacher = fx.make_teacher("csv_teacher")
        self.old_user = fx.make_student("old_user", first_name="Olive", last_name="Old", date_joined=OLD)
        self.new_user = fx.make_student("new_user", first_name="Nina", last_name="New", date_joined=NEW)

        # actions
        self.old_action = fx.make_action(self.old_user, description="old action", token_change=1.0)
        fx.set_auto_now_field(self.old_action, time_created=OLD, time_modified=OLD)
        self.new_action = fx.make_action(self.new_user, description="new action", token_change=9.0)
        fx.set_auto_now_field(self.new_action, time_created=NEW, time_modified=NEW)

        # page views
        self.old_page_view = fx.make_page_view(self.old_user, url="/old", time_created=OLD)
        self.new_page_view = fx.make_page_view(self.new_user, url="/new", time_created=NEW)

        # surveys
        self.old_survey = fx.make_survey(self.old_user, code="old", response=None, time_created=OLD)
        self.new_survey = fx.make_survey(self.new_user, code="new", response=None, time_created=NEW)

        # consents
        self.old_consent = fx.make_consent(self.old_user, legal_first_name="Olive", student_number="1")
        fx.set_auto_now_field(self.old_consent, created_at=OLD)
        self.new_consent = fx.make_consent(self.new_user, legal_first_name="Nina", student_number="2")
        fx.set_auto_now_field(self.new_consent, created_at=NEW)

        self.client.force_authenticate(user=self.teacher)

    # -- helpers ------------------------------------------------------------

    URLS = {
        "action": "api:export-action-list",
        "page-view": "api:export-page-view-list",
        "consent": "api:export-consent-list",
        "user": "api:export-user-list",
        "survey": "api:export-survey-list",
    }

    FILENAMES = {
        "action": "actions.csv",
        "page-view": "page_views.csv",
        "consent": "consents.csv",
        "user": "users.csv",
        "survey": "surveys.csv",
    }

    def url_for(self, key):
        return reverse(self.URLS[key])

    # -- access control -----------------------------------------------------

    def test_all_exports_require_authentication(self):
        self.client.force_authenticate(user=None)
        for key in self.URLS:
            response = self.client.get(self.url_for(key))
            self.assertIn(response.status_code, [401, 403], key)

    def test_all_exports_are_teacher_only(self):
        self.client.force_authenticate(user=self.old_user)
        for key in self.URLS:
            response = self.client.get(self.url_for(key))
            self.assertEqual(response.status_code, 403, key)

    def test_teacher_gets_csv_with_the_expected_filename(self):
        for key in self.URLS:
            response = self.client.get(self.url_for(key))
            self.assertEqual(response.status_code, 200, key)
            self.assertEqual(
                response["Content-Disposition"],
                'attachment; filename="{}"'.format(self.FILENAMES[key]),
                key,
            )

    # -- payload shape ------------------------------------------------------

    def test_action_export_rows(self):
        rows = parse_csv(self.client.get(self.url_for("action")))
        # header order comes from the serializer field map -> compare as a set
        self.assertEqual(
            set(rows[0]),
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
        self.assertEqual(len(rows), 3)

    def test_page_view_export_rows(self):
        rows = parse_csv(self.client.get(self.url_for("page-view")))
        self.assertEqual(set(rows[0]), {"id", "user", "time_created", "url"})
        self.assertEqual(len(rows), 3)

    def test_user_export_rows(self):
        rows = parse_csv(self.client.get(self.url_for("user")))
        self.assertEqual(
            set(rows[0]),
            {"first_name", "last_name", "username", "email", "role", "date_joined"},
        )
        # teacher + old_user + new_user
        self.assertEqual(len(rows), 4)

    def test_survey_export_rows(self):
        rows = parse_csv(self.client.get(self.url_for("survey")))
        # rest_framework_csv flattens nested dict values into dotted columns, so
        # the jsonfield ``response`` becomes one column per key it contains.
        self.assertEqual(set(rows[0]), {"user", "time_created", "code", "response.q1"})
        self.assertEqual(len(rows), 3)

    def test_consent_export_rows(self):
        rows = parse_csv(self.client.get(self.url_for("consent")))
        self.assertEqual(
            set(rows[0]),
            {
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
            },
        )
        self.assertEqual(len(rows), 3)

    # -- QueryFieldsMixin ---------------------------------------------------

    def test_fields_query_param_narrows_the_columns(self):
        rows = parse_csv(self.client.get(self.url_for("user"), {"fields": "email,role"}))
        self.assertEqual(set(rows[0]), {"email", "role"})
        self.assertEqual(len(rows), 4)

    def test_fields_query_param_on_action_export(self):
        rows = parse_csv(self.client.get(self.url_for("action"), {"fields": "description,token_change"}))
        self.assertEqual(set(rows[0]), {"description", "token_change"})
        self.assertEqual({row[rows[0].index("description")] for row in rows[1:]}, {"old action", "new action"})

    def test_fields_exclusion_query_param(self):
        rows = parse_csv(self.client.get(self.url_for("page-view"), {"fields!": "id"}))
        self.assertEqual(set(rows[0]), {"user", "time_created", "url"})

    # -- filterset_fields lookups -------------------------------------------

    def _urls_column(self, response, column):
        rows = parse_csv(response)
        if not rows:
            # an empty queryset renders an empty body (no header row at all)
            return set()
        index = rows[0].index(column)
        return {row[index] for row in rows[1:]}

    def test_action_time_created_lookups(self):
        url = self.url_for("action")

        self.assertEqual(
            self._urls_column(self.client.get(url, {"time_created__lt": AFTER_OLD}), "description"), {"old action"}
        )
        self.assertEqual(
            self._urls_column(self.client.get(url, {"time_created__gt": BEFORE_NEW}), "description"), {"new action"}
        )
        self.assertEqual(
            self._urls_column(
                self.client.get(url, {"time_created__range": "{},{}".format(BEFORE_OLD, AFTER_OLD)}),
                "description",
            ),
            {"old action"},
        )

    def test_action_token_change_lookups(self):
        url = self.url_for("action")
        self.assertEqual(
            self._urls_column(self.client.get(url, {"token_change__lt": "5"}), "description"), {"old action"}
        )
        self.assertEqual(
            self._urls_column(self.client.get(url, {"token_change__gt": "5"}), "description"), {"new action"}
        )

    def test_action_exact_lookups(self):
        url = self.url_for("action")
        self.assertEqual(
            self._urls_column(self.client.get(url, {"actor": str(self.old_user.pk)}), "description"),
            {"old action"},
        )
        self.assertEqual(
            self._urls_column(self.client.get(url, {"actor__role": "Teacher"}), "description"),
            set(),
        )

    def test_page_view_time_created_lookups(self):
        url = self.url_for("page-view")
        self.assertEqual(self._urls_column(self.client.get(url, {"time_created__lt": AFTER_OLD}), "url"), {"/old"})
        self.assertEqual(self._urls_column(self.client.get(url, {"time_created__gt": BEFORE_NEW}), "url"), {"/new"})
        self.assertEqual(
            self._urls_column(
                self.client.get(url, {"time_created__range": "{},{}".format(BEFORE_OLD, AFTER_OLD)}), "url"
            ),
            {"/old"},
        )

    def test_survey_time_created_lookups(self):
        url = self.url_for("survey")
        self.assertEqual(self._urls_column(self.client.get(url, {"time_created__lt": AFTER_OLD}), "code"), {"old"})
        self.assertEqual(self._urls_column(self.client.get(url, {"time_created__gt": BEFORE_NEW}), "code"), {"new"})
        self.assertEqual(
            self._urls_column(
                self.client.get(url, {"time_created__range": "{},{}".format(BEFORE_OLD, AFTER_OLD)}), "code"
            ),
            {"old"},
        )
        self.assertEqual(self._urls_column(self.client.get(url, {"code": "new"}), "code"), {"new"})

    def test_consent_created_at_lookups(self):
        url = self.url_for("consent")
        self.assertEqual(
            self._urls_column(self.client.get(url, {"created_at__lt": AFTER_OLD}), "legal_first_name"), {"Olive"}
        )
        self.assertEqual(
            self._urls_column(self.client.get(url, {"created_at__gt": BEFORE_NEW}), "legal_first_name"), {"Nina"}
        )
        self.assertEqual(
            self._urls_column(
                self.client.get(url, {"created_at__range": "{},{}".format(BEFORE_OLD, AFTER_OLD)}),
                "legal_first_name",
            ),
            {"Olive"},
        )

    def test_user_date_joined_lookups(self):
        url = self.url_for("user")
        self.assertEqual(
            self._urls_column(self.client.get(url, {"date_joined__lt": AFTER_OLD}), "username"), {"old_user"}
        )
        self.assertEqual(
            self._urls_column(self.client.get(url, {"date_joined__gt": BEFORE_NEW}), "username"), {"new_user"}
        )
        self.assertEqual(
            self._urls_column(
                self.client.get(url, {"date_joined__range": "{},{}".format(BEFORE_OLD, AFTER_OLD)}), "username"
            ),
            {"old_user"},
        )
        self.assertEqual(self._urls_column(self.client.get(url, {"role": "Teacher"}), "username"), {"csv_teacher"})

    # -- renderer behaviour -------------------------------------------------

    def test_empty_queryset_renders_an_empty_body(self):
        url = self.url_for("survey")
        response = self.client.get(url, {"code": "nothing-matches"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(parse_csv(response), [])
