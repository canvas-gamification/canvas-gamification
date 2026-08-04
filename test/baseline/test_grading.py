"""Baseline tests for the grading subsystem.

Covers:
  * ``course.grader.grader.MultipleChoiceGrader`` -- the attempt-penalty formula,
    decreasing/negative grades, partial credit, and the one-rendered-choice
    ``ZeroDivisionError``.
  * ``course.models.models.Submission.save()`` -- the token write-back rules
    (monotonic for non-exam questions, overwrite-in-both-directions for exams) and
    the ``Action.token_change == grade * token_value`` ledger entry.

These lock in *current* behaviour so a Python 3.14 / Django 6.0 upgrade can be shown
to be behaviour-preserving. Where current behaviour looks wrong it is pinned with a
``# KNOWN-BUG:`` comment rather than fixed.

No network: only multiple-choice questions are used, whose grader
(``MultipleChoiceGrader``) is pure Python. ``JunitGrader`` (Judge0 over ``requests``)
is never reached.
"""

from django.test import TestCase

from course.models.models import UserQuestionJunction
from general.models.action import Action, ActionVerb
from test.baseline.fixtures_submissions import (
    CHOICES_4,
    CHOICES_5,
    CHOICES_6,
    close_event,
    get_uqj,
    grades_for,
    make_category,
    make_course,
    make_event,
    make_mcq,
    make_mcq_submission,
    make_teacher,
    make_user,
    reload_uqj,
)


class GraderBaseTestCase(TestCase):
    """One student, one author, one category. Questions are created per-test so that
    the ``ensure_uqj`` fan-out stays at a handful of rows."""

    def setUp(self):
        super().setUp()
        self.author = make_teacher()
        self.student = make_user()
        self.category = make_category()


class MultipleChoiceGraderAttemptPenaltyTest(GraderBaseTestCase):
    """`MultipleChoiceGrader.grade` subtracts `prior_submissions / (rendered_choices - 1)`.

    `rendered_choices` is `len(uqj.get_rendered_choices())`, i.e.
    `visible_distractor_count + len(answer.split(","))` -- NOT `len(choices)`.
    """

    def test_single_answer_grade_decreases_with_each_attempt(self):
        # 3 distractors + 1 answer => 4 rendered choices => penalty = prior / 3.
        question = make_mcq(self.author, self.category, answer="a", choices=CHOICES_4, visible_distractor_count=3)
        uqj = get_uqj(self.student, question)

        grades = grades_for(uqj, ["a", "a", "a", "a", "a"])

        self.assertEqual(grades, [1.0, 0.67, 0.33, 0.0, -0.33])

    def test_repeated_correct_attempts_go_negative_but_stay_is_correct(self):
        question = make_mcq(self.author, self.category, answer="a", choices=CHOICES_4, visible_distractor_count=3)
        uqj = get_uqj(self.student, question)

        for _ in range(4):
            make_mcq_submission(uqj, "a")
        submission = make_mcq_submission(uqj, "a")

        # KNOWN-BUG: the attempt penalty is unbounded below, so a *correct* answer can
        # be graded negatively while still being flagged as correct. There is no
        # max(0, ...) clamp in MultipleChoiceGrader.grade().
        self.assertEqual(submission.grade, -0.33)
        self.assertTrue(submission.is_correct)
        self.assertFalse(submission.is_partially_correct)

    def test_visible_distractor_count_changes_the_penalty(self):
        # Same choices dict, but only 1 distractor is rendered => 2 rendered choices
        # => penalty = prior / 1, i.e. an entire grade point per prior attempt.
        question = make_mcq(self.author, self.category, answer="a", choices=CHOICES_4, visible_distractor_count=1)
        uqj = get_uqj(self.student, question)

        grades = grades_for(uqj, ["a", "a", "a"])

        self.assertEqual(grades, [1.0, 0.0, -1.0])

    def test_wrong_answer_scores_exactly_zero_regardless_of_prior_attempts(self):
        question = make_mcq(self.author, self.category, answer="a", choices=CHOICES_4, visible_distractor_count=3)
        uqj = get_uqj(self.student, question)

        for _ in range(3):
            make_mcq_submission(uqj, "a")
        submission = make_mcq_submission(uqj, "b")

        # The "else" branch returns a hard (False, 0) -- the attempt penalty is not applied.
        self.assertEqual(submission.grade, 0)
        self.assertFalse(submission.is_correct)
        self.assertFalse(submission.is_partially_correct)


class MultipleChoiceGraderTwoAnswerTest(GraderBaseTestCase):
    """Two-answer questions with 3 visible distractors => 5 rendered choices => penalty = prior / 4."""

    def setUp(self):
        super().setUp()
        self.question = make_mcq(
            self.author,
            self.category,
            answer="a,b",
            choices=CHOICES_5,
            visible_distractor_count=3,
        )
        self.uqj = get_uqj(self.student, self.question)

    def test_partial_credit_reports_is_correct_true(self):
        submission = make_mcq_submission(self.uqj, "a")

        self.assertEqual(submission.grade, 0.5)
        # KNOWN-BUG: the partial-credit branch of MultipleChoiceGrader.grade() returns
        # is_correct=True. Consequently Submission.calculate_grade() never sets
        # is_partially_correct (it is guarded by `not self.is_correct`), and the UQJ is
        # marked fully solved off a half-right answer.
        self.assertTrue(submission.is_correct)
        self.assertFalse(submission.is_partially_correct)

        uqj = reload_uqj(self.uqj)
        uqj.save()  # this is what course.services.submission.submit_mcq_solution does
        uqj = reload_uqj(uqj)
        self.assertTrue(uqj.is_solved)
        self.assertFalse(uqj.is_partially_solved)

    def test_full_credit_after_a_partial_attempt_is_penalised(self):
        make_mcq_submission(self.uqj, "a")
        submission = make_mcq_submission(self.uqj, "a,b")

        # 1 - 1/4
        self.assertEqual(submission.grade, 0.75)
        self.assertTrue(submission.is_correct)

    def test_one_right_one_wrong_cancels_out_to_zero(self):
        submission = make_mcq_submission(self.uqj, "a,z")

        self.assertEqual(submission.grade, 0)
        self.assertFalse(submission.is_correct)

    def test_answer_order_does_not_matter(self):
        submission = make_mcq_submission(self.uqj, "b,a")

        self.assertEqual(submission.grade, 1.0)
        self.assertTrue(submission.is_correct)


class MultipleChoiceGraderThreeAnswerTest(GraderBaseTestCase):
    """Three-answer questions with 3 visible distractors => 6 rendered choices => penalty = prior / 5."""

    def setUp(self):
        super().setUp()
        self.question = make_mcq(
            self.author,
            self.category,
            answer="a,b,c",
            choices=CHOICES_6,
            visible_distractor_count=3,
        )
        self.uqj = get_uqj(self.student, self.question)

    def test_penalty_sequence_across_four_attempts(self):
        grades = grades_for(self.uqj, ["a,b", "a,b,c", "a", "d,e"])

        self.assertEqual(
            grades,
            [
                0.67,  # 2/3 correct, no prior attempts
                0.8,  # full credit minus 1/5
                -0.07,  # 1/3 - 2/5 -> negative partial credit
                0.0,  # correct - incorrect <= 0 -> hard zero
            ],
        )

    def test_negative_partial_credit_is_still_marked_correct(self):
        make_mcq_submission(self.uqj, "a,b")
        make_mcq_submission(self.uqj, "a,b,c")
        submission = make_mcq_submission(self.uqj, "a")

        # KNOWN-BUG: a submission with a negative grade is stored with is_correct=True.
        self.assertEqual(submission.grade, -0.07)
        self.assertTrue(submission.is_correct)

    def test_duplicate_correct_choice_counts_as_incorrect(self):
        submission = make_mcq_submission(self.uqj, "a,a,b")

        # a(+1), a-again(-1), b(+1) => diff 1 => partial 1/3.
        self.assertEqual(submission.grade, 0.33)
        self.assertTrue(submission.is_correct)


class MultipleChoiceGraderZeroDivisionTest(GraderBaseTestCase):
    """`visible_distractor_count=0` on a single-answer question renders exactly one
    choice, so `number_of_choices - 1 == 0`."""

    def setUp(self):
        super().setUp()
        self.question = make_mcq(
            self.author,
            self.category,
            answer="a",
            choices={"a": "a", "b": "b"},
            visible_distractor_count=0,
        )
        self.uqj = get_uqj(self.student, self.question)

    def test_one_rendered_choice_means_one_rendered_key(self):
        self.assertEqual(len(self.uqj.get_rendered_choices()), 1)

    def test_correct_answer_raises_zero_division_error(self):
        # KNOWN-BUG: MultipleChoiceGrader.grade() divides by (number_of_choices - 1)
        # without guarding against a single rendered choice, so submitting the correct
        # answer to such a question raises ZeroDivisionError out of Submission.save()
        # (and therefore out of POST /api/submission/submit/ as a 500).
        with self.assertRaises(ZeroDivisionError):
            make_mcq_submission(self.uqj, "a")

    def test_incorrect_answer_does_not_raise(self):
        # The (False, 0) branch is reached before any division.
        submission = make_mcq_submission(self.uqj, "b")

        self.assertEqual(submission.grade, 0)
        self.assertFalse(submission.is_correct)


class SubmissionTokenWriteBackNonExamTest(GraderBaseTestCase):
    """`Submission.save()` only pushes tokens onto the UQJ when the question is an exam
    or when `token_change > 0` -- i.e. non-exam tokens never decrease."""

    def setUp(self):
        super().setUp()
        self.question = make_mcq(
            self.author,
            self.category,
            answer="a,b,c",
            choices=CHOICES_6,
            visible_distractor_count=3,
            difficulty="HARD",  # TokenValue defaults HARD -> 3.0
        )
        self.uqj = get_uqj(self.student, self.question)

    def test_token_value_is_the_hard_default(self):
        self.assertEqual(self.question.token_value, 3)
        self.assertFalse(self.question.is_exam)

    def test_tokens_are_monotonically_non_decreasing(self):
        make_mcq_submission(self.uqj, "a")  # grade 0.33
        after_first = reload_uqj(self.uqj)
        self.assertAlmostEqual(after_first.tokens_received, 0.33 * 3)
        self.assertEqual(after_first.grade, 0.33)

        make_mcq_submission(self.uqj, "a,b,c")  # grade 0.8 -> higher, written through
        after_second = reload_uqj(self.uqj)
        self.assertAlmostEqual(after_second.tokens_received, 0.8 * 3)
        self.assertEqual(after_second.grade, 0.8)

        third = make_mcq_submission(self.uqj, "a,b,c")  # grade 0.6 -> lower, NOT written
        self.assertEqual(third.grade, 0.6)
        after_third = reload_uqj(self.uqj)
        self.assertAlmostEqual(after_third.tokens_received, 0.8 * 3)
        self.assertEqual(after_third.grade, 0.8)

    def test_wrong_answer_leaves_tokens_untouched(self):
        make_mcq_submission(self.uqj, "a,b,c")
        before = reload_uqj(self.uqj).tokens_received

        wrong = make_mcq_submission(self.uqj, "d,e")
        self.assertEqual(wrong.grade, 0)

        # A non-exam submission that is neither correct nor partially correct never
        # enters the write-back branch at all.
        self.assertAlmostEqual(reload_uqj(self.uqj).tokens_received, before)


class SubmissionTokenWriteBackExamTest(GraderBaseTestCase):
    """For exam questions the latest submission always overwrites the UQJ tokens,
    in both directions."""

    def setUp(self):
        super().setUp()
        self.course = make_course()
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

    def test_question_is_exam(self):
        self.assertTrue(self.question.is_exam)
        self.assertEqual(self.question.token_value, 3)

    def test_exam_tokens_overwrite_upwards_and_downwards(self):
        wrong = make_mcq_submission(self.uqj, "b")  # grade 0
        self.assertEqual(wrong.grade, 0)
        self.assertAlmostEqual(reload_uqj(self.uqj).tokens_received, 0.0)

        better = make_mcq_submission(self.uqj, "a")  # grade 0.67 (1 prior attempt)
        self.assertEqual(better.grade, 0.67)
        self.assertAlmostEqual(reload_uqj(self.uqj).tokens_received, 0.67 * 3)
        self.assertEqual(reload_uqj(self.uqj).grade, 0.67)

        worse = make_mcq_submission(self.uqj, "b")  # grade 0 again
        self.assertEqual(worse.grade, 0)
        # Downward overwrite: the student loses the tokens they had already earned.
        self.assertAlmostEqual(reload_uqj(self.uqj).tokens_received, 0.0)
        self.assertEqual(reload_uqj(self.uqj).grade, 0)

    def test_closed_exam_still_overwrites_at_model_level(self):
        make_mcq_submission(self.uqj, "a")
        self.assertAlmostEqual(reload_uqj(self.uqj).tokens_received, 3.0)

        close_event(self.exam)
        # is_exam does not depend on the event being open, so the write-back branch
        # still fires for a closed exam when a submission is created directly.
        self.question.refresh_from_db()
        make_mcq_submission(UserQuestionJunction.objects.get(pk=self.uqj.pk), "b")
        self.assertAlmostEqual(reload_uqj(self.uqj).tokens_received, 0.0)


class SubmissionEvaluationActionTest(GraderBaseTestCase):
    """`Submission.save()` -> `create_submission_evaluation_action` writes the token
    ledger row. `Action.token_change` is `grade * token_value` -- the absolute value,
    NOT the delta actually applied to the UQJ."""

    def setUp(self):
        super().setUp()
        self.question = make_mcq(
            self.author,
            self.category,
            answer="a,b,c",
            choices=CHOICES_6,
            visible_distractor_count=3,
            difficulty="HARD",
        )
        self.uqj = get_uqj(self.student, self.question)

    def _evaluation_actions(self):
        return list(Action.objects.filter(actor=self.student, verb=ActionVerb.EVALUATED).order_by("id"))

    def test_one_evaluation_action_per_submission_with_grade_times_token_value(self):
        make_mcq_submission(self.uqj, "a")  # 0.33
        make_mcq_submission(self.uqj, "a,b,c")  # 0.8
        make_mcq_submission(self.uqj, "a,b,c")  # 0.6 -- not written back to the UQJ

        actions = self._evaluation_actions()
        self.assertEqual(len(actions), 3)
        self.assertAlmostEqual(actions[0].token_change, 0.33 * 3)
        self.assertAlmostEqual(actions[1].token_change, 0.8 * 3)
        # KNOWN-BUG: the ledger records grade * token_value for every submission, while
        # UserQuestionJunction.tokens_received keeps only the best non-exam result. The
        # Action ledger (which drives MyUser.tokens) therefore double-counts and cannot
        # be reconciled with CanvasCourseRegistration.total_tokens_received.
        self.assertAlmostEqual(actions[2].token_change, 0.6 * 3)
        self.assertAlmostEqual(reload_uqj(self.uqj).tokens_received, 0.8 * 3)

    def test_evaluation_action_payload(self):
        submission = make_mcq_submission(self.uqj, "a,b,c")

        action = self._evaluation_actions()[0]
        self.assertEqual(action.description, "Submission was evaluated")
        self.assertEqual(action.object_type, "Submission")
        self.assertEqual(action.object_id, submission.id)
        self.assertEqual(action.status, "Complete")
        self.assertEqual(
            set(action.data.keys()),
            {"answer", "grade", "is_correct", "is_partially_correct", "status"},
        )
        self.assertEqual(action.data["answer"], "a,b,c")
        self.assertEqual(action.data["grade"], 1.0)
        self.assertEqual(action.data["status"], "Correct")

    def test_zero_grade_submission_still_writes_a_zero_token_action(self):
        make_mcq_submission(self.uqj, "d,e")

        actions = self._evaluation_actions()
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0].token_change, 0)
        self.assertEqual(actions[0].data["status"], "Incorrect")

    def test_user_tokens_sums_the_action_ledger(self):
        # MyUser.tokens is None (not 0) before any action exists.
        self.assertIsNone(self.student.tokens)

        make_mcq_submission(self.uqj, "a")  # 0.33 * 3
        make_mcq_submission(self.uqj, "a,b,c")  # 0.8 * 3

        self.assertAlmostEqual(self.student.tokens, (0.33 + 0.8) * 3)
