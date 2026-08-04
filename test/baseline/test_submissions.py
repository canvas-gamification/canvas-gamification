"""Baseline tests for the submission API.

Covers:
  * ``POST /api/submission/submit/`` end-to-end for multiple-choice questions --
    status code, exact serializer field set, UQJ side effects, the two ``Action``
    rows, and every rejection path.
  * Exam answer hiding through ``/api/submission/`` and ``/api/uqj/``.
  * Exact field-name snapshots for all six submission serializers.
  * A regression pin for the client-supplied ``token_change`` on ``/api/user-actions/``.

Current behaviour is locked in as-is; anything that looks wrong is pinned with a
``# KNOWN-BUG:`` comment instead of being fixed.

No network: only multiple-choice submissions are created. The Java/Parsons serializers
are inspected via ``serializer.fields`` only, so ``JunitGrader`` (Judge0 over
``requests``) is never invoked.
"""

from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from api.serializers.java_question import JavaSubmissionHiddenDetailsSerializer, JavaSubmissionSerializer
from api.serializers.multiple_choice_question import (
    MultipleChoiceSubmissionHiddenDetailsSerializer,
    MultipleChoiceSubmissionSerializer,
)
from api.serializers.parsons_question import ParsonsSubmissionHiddenDetailsSerializer, ParsonsSubmissionSerializer
from course.models.models import Submission, TokenValue
from course.models.multiple_choice import MultipleChoiceSubmission
from general.models.action import Action, ActionVerb
from test.baseline.fixtures_submissions import (
    CHOICES_4,
    api_client,
    close_event,
    get_uqj,
    make_category,
    make_course,
    make_event,
    make_mcq,
    make_teacher,
    make_user,
    reload_uqj,
)

# --------------------------------------------------------------------------------------
# Exact serializer field sets. DRF upgrades silently drift field names; these snapshots
# are the canary.
# --------------------------------------------------------------------------------------

MCQ_SUBMISSION_FIELDS = {
    "pk",
    "submission_time",
    "answer",
    "grade",
    "is_correct",
    "is_partially_correct",
    "finalized",
    "status",
    "tokens_received",
    "token_value",
    "question",
    "answer_display",
    "show_answer",
    "show_detail",
    "status_color",
    "author",
}

MCQ_SUBMISSION_HIDDEN_FIELDS = {
    "pk",
    "submission_time",
    "answer",
    "answer_display",
    "token_value",
    "question",
    "show_answer",
    "show_detail",
    "author",
}

JAVA_SUBMISSION_FIELDS = {
    "pk",
    "submission_time",
    "answer",
    "grade",
    "is_correct",
    "is_partially_correct",
    "finalized",
    "status",
    "tokens_received",
    "token_value",
    "answer_files",
    "question",
    "get_decoded_stderr",
    "get_decoded_results",
    "get_status_message",
    "get_formatted_test_results",
    "get_passed_test_results",
    "get_failed_test_results",
    "get_num_tests",
    "formatted_tokens_received",
    "show_answer",
    "show_detail",
    "status_color",
    "author",
    "bugs",
}

JAVA_SUBMISSION_HIDDEN_FIELDS = {
    "pk",
    "submission_time",
    "answer",
    "token_value",
    "answer_files",
    "question",
    "show_answer",
    "show_detail",
    "author",
}

PARSONS_SUBMISSION_FIELDS = {
    "pk",
    "submission_time",
    "answer",
    "grade",
    "is_correct",
    "is_partially_correct",
    "finalized",
    "status",
    "tokens_received",
    "token_value",
    "question",
    "get_decoded_stderr",
    "get_decoded_results",
    "get_formatted_test_results",
    "get_passed_test_results",
    "get_failed_test_results",
    "get_num_tests",
    "formatted_tokens_received",
    "answer_files",
    "show_answer",
    "show_detail",
    "status_color",
    "author",
    "bugs",
}

PARSONS_SUBMISSION_HIDDEN_FIELDS = {
    "pk",
    "submission_time",
    "answer",
    "token_value",
    "question",
    "answer_files",
    "show_answer",
    "show_detail",
    "author",
}

SUBMIT_URL = "api:submission-submit"
SUBMISSION_LIST_URL = "api:submission-list"
SUBMISSION_DETAIL_URL = "api:submission-detail"
UQJ_LIST_URL = "api:uqj-list"
USER_ACTIONS_URL = "api:user-actions-list"


class SubmissionApiBaseTestCase(APITestCase):
    """One teacher (question author), one student, one open ASSIGNMENT event."""

    def setUp(self):
        super().setUp()
        self.author = make_teacher()
        self.student = make_user()
        self.category = make_category()
        self.course = make_course(instructor=self.author)
        self.event = make_event(self.course, event_type="ASSIGNMENT")
        self.question = make_mcq(
            self.author,
            self.category,
            event=self.event,
            answer="a",
            choices=CHOICES_4,
            visible_distractor_count=3,
            difficulty="HARD",
            max_submission_allowed=100,
        )
        self.uqj = get_uqj(self.student, self.question)
        self.client = api_client(self.student)

    def db_token_value(self, question=None):
        """The token value as stored in the DB (a float), which is what the API returns.

        ``get_token_value_object`` returns its freshly built in-memory instance the first
        time, whose ``value`` is still a plain ``int``.
        """
        question = question or self.question
        question.token_value  # force the TokenValue row to be created
        return TokenValue.objects.get(category=question.category, difficulty=question.difficulty).value

    def submit(self, solution, question=None, client=None):
        client = client or self.client
        return client.post(
            reverse(SUBMIT_URL),
            {"question": (question or self.question).id, "solution": solution},
            format="json",
        )


class McqSubmitEndToEndTest(SubmissionApiBaseTestCase):
    def test_correct_submission_returns_201_with_exact_field_set(self):
        response = self.submit("a")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(set(response.data.keys()), MCQ_SUBMISSION_FIELDS)
        self.assertEqual(response.data["answer"], "a")
        self.assertEqual(response.data["grade"], 1.0)
        self.assertTrue(response.data["is_correct"])
        self.assertTrue(response.data["finalized"])
        self.assertEqual(response.data["status"], "Correct")
        self.assertEqual(response.data["status_color"], "success")
        self.assertTrue(response.data["show_answer"])
        self.assertFalse(response.data["show_detail"])
        self.assertEqual(response.data["answer_display"], ["a"])
        # The author has no first_name in the fixtures.
        self.assertEqual(response.data["author"], "Anonymous Student")

    def test_correct_submission_persists_one_submission_row(self):
        self.submit("a")

        self.assertEqual(MultipleChoiceSubmission.objects.count(), 1)
        submission = MultipleChoiceSubmission.objects.get()
        self.assertEqual(submission.uqj_id, self.uqj.id)
        self.assertEqual(submission.answer, "a")
        self.assertTrue(submission.finalized)

    def test_correct_submission_updates_the_uqj(self):
        token_value = self.db_token_value()
        self.assertIsNone(reload_uqj(self.uqj).solved_at)

        self.submit("a")

        uqj = reload_uqj(self.uqj)
        self.assertTrue(uqj.is_solved)
        self.assertIsNotNone(uqj.solved_at)
        self.assertFalse(uqj.is_partially_solved)
        self.assertAlmostEqual(uqj.tokens_received, 1.0 * token_value)
        self.assertEqual(uqj.grade, 1.0)

    def test_wrong_submission_does_not_solve_the_uqj(self):
        response = self.submit("b")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        uqj = reload_uqj(self.uqj)
        self.assertFalse(uqj.is_solved)
        self.assertIsNone(uqj.solved_at)
        self.assertEqual(uqj.tokens_received, 0)

    def test_submission_creates_exactly_two_actions(self):
        token_value = self.db_token_value()

        self.submit("a")

        actions = list(Action.objects.filter(actor=self.student).order_by("id"))
        self.assertEqual(len(actions), 2)

        # Written from inside Submission.save() ...
        evaluated = actions[0]
        self.assertEqual(evaluated.verb, ActionVerb.EVALUATED)
        self.assertEqual(evaluated.object_type, "Submission")
        self.assertAlmostEqual(evaluated.token_change, 1.0 * token_value)

        # ... then by SubmissionViewSet.submit().
        submitted = actions[1]
        self.assertEqual(submitted.verb, ActionVerb.SUBMITTED)
        self.assertEqual(submitted.object_type, "Submission")
        self.assertEqual(submitted.token_change, 0)
        self.assertEqual(submitted.data, {"answer": "a"})

        self.assertAlmostEqual(self.student.tokens, 1.0 * token_value)

    def test_missing_question_or_solution_is_400(self):
        self.assertEqual(self.client.post(reverse(SUBMIT_URL), {}, format="json").status_code, 400)
        self.assertEqual(
            self.client.post(reverse(SUBMIT_URL), {"question": self.question.id}, format="json").status_code,
            400,
        )
        self.assertEqual(
            self.client.post(reverse(SUBMIT_URL), {"solution": "a"}, format="json").status_code,
            400,
        )
        self.assertEqual(Submission.objects.count(), 0)

    def test_unknown_question_is_404(self):
        response = self.client.post(
            reverse(SUBMIT_URL),
            {"question": 10**8, "solution": "a"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_anonymous_submit_is_401(self):
        response = api_client().post(
            reverse(SUBMIT_URL),
            {"question": self.question.id, "solution": "a"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Submission.objects.count(), 0)

    def test_empty_solution_string_is_accepted_and_graded_zero(self):
        # SubmissionViewSet.submit() guards with `is None`, so an empty string is a
        # valid payload and is simply graded as a wrong answer.
        response = self.submit("")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["grade"], 0)


class McqSubmitRejectionPathsTest(SubmissionApiBaseTestCase):
    def test_max_submission_allowed_is_enforced(self):
        self.question.max_submission_allowed = 2
        self.question.save()

        self.assertEqual(self.submit("b").status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.submit("c").status_code, status.HTTP_201_CREATED)

        response = self.submit("d")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("You are not allowed to submit", str(response.data))
        self.assertEqual(Submission.objects.count(), 2)

    def test_duplicate_answer_is_rejected_on_non_practice_questions(self):
        self.assertEqual(self.submit("b").status_code, status.HTTP_201_CREATED)

        response = self.submit("b")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("You have already submitted this answer!", str(response.data))
        self.assertEqual(Submission.objects.count(), 1)

    def test_duplicate_answer_is_allowed_on_practice_questions(self):
        practice = make_mcq(
            self.author,
            self.category,
            event=None,
            answer="a",
            choices=CHOICES_4,
            visible_distractor_count=3,
        )

        self.assertEqual(self.submit("b", question=practice).status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.submit("b", question=practice).status_code, status.HTTP_201_CREATED)
        self.assertEqual(Submission.objects.count(), 2)

    def test_duplicate_answer_is_allowed_for_teachers(self):
        teacher_client = api_client(self.author)

        self.assertEqual(self.submit("b", client=teacher_client).status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.submit("b", client=teacher_client).status_code, status.HTTP_201_CREATED)

    def test_not_allowed_after_opening_the_tutorial(self):
        uqj = reload_uqj(self.uqj)
        uqj.opened_tutorial = True
        uqj.save()

        response = self.submit("a")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("You are not allowed to submit", str(response.data))
        self.assertEqual(Submission.objects.count(), 0)

    def test_not_allowed_once_solved(self):
        self.assertEqual(self.submit("a").status_code, status.HTTP_201_CREATED)
        self.assertTrue(reload_uqj(self.uqj).is_solved)

        response = self.submit("b")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("You are not allowed to submit", str(response.data))
        self.assertEqual(Submission.objects.count(), 1)

    def test_not_allowed_once_the_event_is_closed(self):
        close_event(self.event)

        response = self.submit("a")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("You are not allowed to submit", str(response.data))
        self.assertEqual(Submission.objects.count(), 0)

    def test_not_allowed_before_the_event_starts(self):
        now = timezone.now()
        self.event.start_date = now + timedelta(days=1)
        self.event.end_date = now + timedelta(days=2)
        self.event.save()

        response = self.submit("a")

        # A not-yet-open event is also "not open", so submission is refused.
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("You are not allowed to submit", str(response.data))
        self.assertEqual(Submission.objects.count(), 0)

    def test_teacher_may_submit_to_a_closed_event(self):
        close_event(self.event)

        # UQJ.is_allowed_to_submit short-circuits to True for teachers.
        response = self.submit("a", client=api_client(self.author))

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class SubmissionSerializerFieldSnapshotTest(APITestCase):
    """Exact field-name sets for all six submission serializers.

    Uses ``serializer.fields`` rather than ``.data`` so the Java/Parsons serializers can
    be snapshotted without constructing a ``CodeSubmission`` (which would hit Judge0).
    """

    def test_multiple_choice_submission_serializer_fields(self):
        self.assertEqual(set(MultipleChoiceSubmissionSerializer().fields.keys()), MCQ_SUBMISSION_FIELDS)

    def test_multiple_choice_submission_hidden_serializer_fields(self):
        self.assertEqual(
            set(MultipleChoiceSubmissionHiddenDetailsSerializer().fields.keys()),
            MCQ_SUBMISSION_HIDDEN_FIELDS,
        )

    def test_java_submission_serializer_fields(self):
        self.assertEqual(set(JavaSubmissionSerializer().fields.keys()), JAVA_SUBMISSION_FIELDS)

    def test_java_submission_hidden_serializer_fields(self):
        self.assertEqual(
            set(JavaSubmissionHiddenDetailsSerializer().fields.keys()),
            JAVA_SUBMISSION_HIDDEN_FIELDS,
        )

    def test_parsons_submission_serializer_fields(self):
        self.assertEqual(set(ParsonsSubmissionSerializer().fields.keys()), PARSONS_SUBMISSION_FIELDS)

    def test_parsons_submission_hidden_serializer_fields(self):
        self.assertEqual(
            set(ParsonsSubmissionHiddenDetailsSerializer().fields.keys()),
            PARSONS_SUBMISSION_HIDDEN_FIELDS,
        )

    def test_hidden_serializers_expose_no_grade_bearing_field(self):
        grade_bearing = {
            "grade",
            "is_correct",
            "is_partially_correct",
            "finalized",
            "status",
            "status_color",
            "tokens_received",
            "formatted_tokens_received",
        }
        for field_set in (
            MCQ_SUBMISSION_HIDDEN_FIELDS,
            JAVA_SUBMISSION_HIDDEN_FIELDS,
            PARSONS_SUBMISSION_HIDDEN_FIELDS,
        ):
            self.assertEqual(field_set & grade_bearing, set())


class McqSubmissionSerializedDataSnapshotTest(SubmissionApiBaseTestCase):
    """The serialized payload of a real MCQ submission, both variants."""

    def test_full_serializer_data_keys(self):
        self.submit("a")
        submission = MultipleChoiceSubmission.objects.get()

        self.assertEqual(set(MultipleChoiceSubmissionSerializer(submission).data.keys()), MCQ_SUBMISSION_FIELDS)

    def test_hidden_serializer_data_keys(self):
        self.submit("a")
        submission = MultipleChoiceSubmission.objects.get()

        self.assertEqual(
            set(MultipleChoiceSubmissionHiddenDetailsSerializer(submission).data.keys()),
            MCQ_SUBMISSION_HIDDEN_FIELDS,
        )


class ExamAnswerHidingTest(APITestCase):
    """During an *open* exam, grades must not leak through /api/submission/ or /api/uqj/,
    and must reappear once the exam closes."""

    def setUp(self):
        super().setUp()
        self.author = make_teacher()
        self.student = make_user()
        self.category = make_category()
        self.course = make_course(instructor=self.author)
        self.exam = make_event(self.course, event_type="EXAM")
        self.question = make_mcq(
            self.author,
            self.category,
            event=self.exam,
            answer="a",
            choices=CHOICES_4,
            visible_distractor_count=3,
            difficulty="HARD",
            max_submission_allowed=100,
        )
        self.uqj = get_uqj(self.student, self.question)
        self.client = api_client(self.student)

        response = self.client.post(
            reverse(SUBMIT_URL),
            {"question": self.question.id, "solution": "a"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.submission_id = response.data["pk"]

    def token_value(self):
        self.question.token_value  # force the TokenValue row to exist
        return TokenValue.objects.get(category=self.category, difficulty=self.question.difficulty).value

    def submission_list(self):
        response = self.client.get(reverse(SUBMISSION_LIST_URL), {"question": self.question.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response.data

    def uqj_payload(self):
        response = self.client.get(reverse(UQJ_LIST_URL), {"page_size": 1000})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"] if isinstance(response.data, dict) else response.data
        matches = [row for row in results if row["question_id"] == self.question.id]
        self.assertEqual(len(matches), 1)
        return matches[0]

    def test_submit_response_is_already_hidden_during_an_open_exam(self):
        # A second, unsolved question in the same open exam (the setUp question is
        # already solved, so it would be refused).
        other = make_mcq(
            self.author,
            self.category,
            event=self.exam,
            answer="a",
            choices=CHOICES_4,
            visible_distractor_count=3,
            difficulty="HARD",
            max_submission_allowed=100,
        )
        response = self.client.post(
            reverse(SUBMIT_URL),
            {"question": other.id, "solution": "b"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(set(response.data.keys()), MCQ_SUBMISSION_HIDDEN_FIELDS)

    def test_submission_list_hides_the_grade_during_an_open_exam(self):
        results = self.submission_list()

        self.assertEqual(len(results), 1)
        self.assertEqual(set(results[0].keys()), MCQ_SUBMISSION_HIDDEN_FIELDS)
        self.assertNotIn("grade", results[0])

    def test_submission_retrieve_hides_the_grade_during_an_open_exam(self):
        response = self.client.get(reverse(SUBMISSION_DETAIL_URL, args=[self.submission_id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data.keys()), MCQ_SUBMISSION_HIDDEN_FIELDS)

    def test_uqj_hides_earned_tokens_during_an_open_exam(self):
        payload = self.uqj_payload()

        self.assertEqual(payload["formatted_current_tokens_received"], str(self.token_value()))
        # KNOWN-BUG: the raw `tokens_received` field is still serialized by UQJSerializer
        # during an open exam, so the grade leaks anyway -- only the *formatted* string
        # is masked.
        self.assertAlmostEqual(payload["tokens_received"], 1.0 * self.token_value())
        self.assertTrue(payload["is_solved"])

    def test_submission_list_reveals_the_grade_once_the_exam_closes(self):
        close_event(self.exam)

        results = self.submission_list()

        self.assertEqual(len(results), 1)
        self.assertEqual(set(results[0].keys()), MCQ_SUBMISSION_FIELDS)
        self.assertEqual(results[0]["grade"], 1.0)
        self.assertEqual(results[0]["status"], "Correct")

    def test_submission_retrieve_reveals_the_grade_once_the_exam_closes(self):
        close_event(self.exam)

        response = self.client.get(reverse(SUBMISSION_DETAIL_URL, args=[self.submission_id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data.keys()), MCQ_SUBMISSION_FIELDS)
        self.assertEqual(response.data["grade"], 1.0)

    def test_uqj_reveals_earned_tokens_once_the_exam_closes(self):
        close_event(self.exam)

        payload = self.uqj_payload()
        uqj = reload_uqj(self.uqj)

        self.assertEqual(
            payload["formatted_current_tokens_received"],
            "{}/{}".format(uqj.tokens_received, self.token_value()),
        )


class ActionTokenMintingRegressionTest(APITestCase):
    """`ActionsViewSet` exposes the whole `Action` model for creation (`exclude = []`),
    so a client can post an arbitrary `token_change`."""

    def setUp(self):
        super().setUp()
        self.student = make_user()
        self.other = make_user()
        self.client = api_client(self.student)

    def test_client_can_mint_tokens_through_user_actions(self):
        self.assertIsNone(self.student.tokens)

        response = self.client.post(
            reverse(USER_ACTIONS_URL),
            {
                "description": "totally legitimate",
                "status": "Complete",
                "verb": "Clicked",
                "object_type": "Button",
                "token_change": 500,
            },
            format="json",
        )

        # KNOWN-BUG: ActionsSerializer has `exclude = []` and only `actor` is read-only,
        # so `token_change` is client-writable. The created Action is counted by
        # `MyUser.tokens`, which means any authenticated user can mint unlimited tokens
        # with a single POST to /api/user-actions/.
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["token_change"], 500)
        self.assertEqual(self.student.tokens, 500)
        self.assertEqual(Action.objects.get().actor_id, self.student.id)

    def test_actor_is_forced_to_the_requesting_user(self):
        response = self.client.post(
            reverse(USER_ACTIONS_URL),
            {
                "description": "spoof attempt",
                "status": "Complete",
                "verb": "Clicked",
                "actor": self.other.id,
                "token_change": 42,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Action.objects.get().actor_id, self.student.id)
        self.assertIsNone(self.other.tokens)

    def test_negative_token_change_is_also_accepted(self):
        response = self.client.post(
            reverse(USER_ACTIONS_URL),
            {
                "description": "negative",
                "status": "Complete",
                "verb": "Clicked",
                "token_change": -7.5,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.student.tokens, -7.5)

    def test_anonymous_cannot_create_actions(self):
        response = api_client().post(
            reverse(USER_ACTIONS_URL),
            {"description": "x", "status": "Complete", "verb": "Clicked", "token_change": 1},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Action.objects.count(), 0)
