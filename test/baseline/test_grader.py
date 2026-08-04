"""Baseline tests for course/grader/grader.py (the Judge0 / JUnit grader).

Every Judge0 HTTP call site is replaced with ``unittest.mock`` (see
``test.baseline.fixtures_grader.mock_judge0``) -- no test here may open a socket.
The tests pin the *current* return values of ``JunitGrader.grade`` so a later
Python 3.14 / Django 6 upgrade can be checked for behaviour preservation.
"""

import os

from django.conf import settings
from django.test import TestCase

from course.grader.grader import JunitGrader, MultipleChoiceGrader
from course.models.java import JavaSubmission
from test.baseline.fixtures_grader import (
    DEFAULT_TOKEN,
    JUDGE0_ACCEPTED,
    JUDGE0_COMPILATION_ERROR,
    JUDGE0_IN_QUEUE,
    JUDGE0_INTERNAL_ERROR,
    JUDGE0_PROCESSING,
    JUNIT_ALL_PASS,
    JUNIT_SOME_FAIL,
    JUNIT_ZERO_TESTS,
    build_java_submission,
    create_category,
    create_java_question,
    create_user,
    get_uqj,
    judge0_result,
    mock_judge0,
)


class JunitGraderGradeTests(TestCase):
    """``JunitGrader.grade`` over canned JUnit XML."""

    @classmethod
    def setUpTestData(cls):
        cls.user = create_user("grader_student")
        cls.category = create_category()
        cls.question = create_java_question(author=cls.user, category=cls.category)

    def setUp(self):
        self.uqj = get_uqj(self.user, self.question)
        self.grader = self.question.grader

    def test_grader_is_junit_grader(self):
        self.assertIsInstance(self.question.grader, JunitGrader)

    def test_all_tests_pass(self):
        submission = build_java_submission(self.uqj, [judge0_result(stdout=JUNIT_ALL_PASS)])
        with mock_judge0() as requests_mock:
            is_correct, grade = self.grader.grade(submission)
        self.assertTrue(is_correct)
        self.assertEqual(grade, 1.0)
        # Judge0 was never contacted: the submission was already finished.
        self.assertFalse(requests_mock.get.called)
        self.assertEqual(submission.get_num_tests(), 2)
        self.assertEqual(submission.get_formatted_test_results(), "2/2")
        self.assertEqual([r["name"] for r in submission.get_failed_test_results()], [])
        self.assertEqual(
            [r["name"] for r in submission.get_passed_test_results()],
            ["Test addition", "Test subtraction of numbers"],
        )

    def test_some_tests_fail(self):
        submission = build_java_submission(self.uqj, [judge0_result(stdout=JUNIT_SOME_FAIL)])
        with mock_judge0():
            is_correct, grade = self.grader.grade(submission)
        self.assertFalse(is_correct)
        self.assertEqual(grade, 0.5)
        self.assertEqual(submission.get_num_tests(), 4)
        self.assertEqual(submission.get_formatted_test_results(), "2/4")
        self.assertEqual(
            [r["name"] for r in submission.get_failed_test_results()],
            ["Test subtraction of numbers", "Test division"],
        )
        # the "==>" suffix of an opentest4j message is stripped by format_message
        self.assertEqual(
            submission.get_failed_test_results()[0]["message"],
            "expected: <5> but was: <4> ",
        )

    def test_zero_tests(self):
        submission = build_java_submission(self.uqj, [judge0_result(stdout=JUNIT_ZERO_TESTS)])
        with mock_judge0():
            is_correct, grade = self.grader.grade(submission)
        self.assertFalse(is_correct)
        self.assertEqual(grade, 0)
        self.assertEqual(submission.get_num_tests(), 0)
        self.assertEqual(submission.get_formatted_test_results(), "0/0")

    def test_empty_stdout_is_zero_tests(self):
        submission = build_java_submission(self.uqj, [judge0_result(stdout="")])
        with mock_judge0():
            self.assertEqual(self.grader.grade(submission), (False, 0))

    def test_compile_error(self):
        submission = build_java_submission(
            self.uqj,
            [
                judge0_result(
                    stdout="",
                    stderr="Main.java:3: error: incompatible types\n",
                    status_id=JUDGE0_COMPILATION_ERROR,
                    description="Compilation Error",
                )
            ],
        )
        with mock_judge0():
            is_correct, grade = self.grader.grade(submission)
        self.assertFalse(is_correct)
        self.assertEqual(grade, 0)
        self.assertTrue(submission.is_compile_error)
        self.assertFalse(submission.in_progress)
        self.assertEqual(submission.get_status_message(), "Compilation Error")

    def test_in_progress_triggers_evaluate_and_regrades(self):
        submission = build_java_submission(self.uqj, [judge0_result(status_id=JUDGE0_IN_QUEUE, description="In Queue")])
        finished = judge0_result(stdout=JUNIT_ALL_PASS)
        with mock_judge0(get_result=finished) as requests_mock:
            is_correct, grade = self.grader.grade(submission)

        self.assertTrue(is_correct)
        self.assertEqual(grade, 1.0)
        self.assertEqual(requests_mock.get.call_count, 1)
        url = requests_mock.get.call_args[0][0]
        self.assertIn("/submissions/{}".format(DEFAULT_TOKEN), url)
        self.assertIn("base64_encoded=true", url)
        self.assertEqual(requests_mock.get.call_args[1]["headers"], JunitGrader.HEADERS)
        # evaluate() replaces results wholesale
        self.assertEqual(len(submission.results), 1)
        self.assertEqual(submission.results[0]["status"]["id"], JUDGE0_ACCEPTED)

    def test_still_in_progress_after_evaluate(self):
        submission = build_java_submission(
            self.uqj, [judge0_result(status_id=JUDGE0_PROCESSING, description="Processing")]
        )
        with mock_judge0(get_result=judge0_result(status_id=JUDGE0_PROCESSING, description="Processing")):
            self.assertEqual(self.grader.grade(submission), (False, 0))
        self.assertTrue(submission.in_progress)

    def test_evaluate_non_200_falls_back_to_internal_error(self):
        submission = build_java_submission(self.uqj, [])
        with mock_judge0(get_status_code=500) as requests_mock:
            self.grader.evaluate(submission)
        self.assertEqual(len(submission.results), 1)
        self.assertEqual(submission.results[0]["status"]["id"], JUDGE0_INTERNAL_ERROR)
        self.assertEqual(submission.get_status_message(), "Internal Error")
        # the canned fallback never consults the response body
        self.assertFalse(requests_mock.get.return_value.json.called)

    def test_clean_up_issues_delete(self):
        submission = build_java_submission(self.uqj, [judge0_result(stdout=JUNIT_ALL_PASS)])
        with mock_judge0() as requests_mock:
            self.grader.clean_up(submission)
        self.assertEqual(requests_mock.delete.call_count, 1)
        self.assertIn("/submissions/{}".format(DEFAULT_TOKEN), requests_mock.delete.call_args[0][0])
        self.assertEqual(requests_mock.delete.call_args[1]["headers"], JunitGrader.HEADERS)


class JunitGraderSubmitTests(TestCase):
    """``JunitGrader.submit`` builds the zip payload and POSTs it to Judge0."""

    @classmethod
    def setUpTestData(cls):
        cls.user = create_user("grader_submitter")
        cls.category = create_category()
        cls.question = create_java_question(author=cls.user, category=cls.category)

    def setUp(self):
        # get_compiler_script()/get_additional_file() open paths relative to cwd.
        self._old_cwd = os.getcwd()
        os.chdir(str(settings.BASE_DIR))
        self.addCleanup(os.chdir, self._old_cwd)
        self.uqj = get_uqj(self.user, self.question)

    def test_compiler_script_substitutes_file_names(self):
        submission = build_java_submission(self.uqj, [])
        script = self.question.grader.get_compiler_script(submission)
        self.assertNotIn("{{user_code_filename}}", script)
        self.assertNotIn("{{user_code_classname}}", script)
        self.assertIn("Main.java", script)
        self.assertIn("Main.class", script)

    def test_submit_posts_and_stores_token(self):
        submission = build_java_submission(self.uqj, [], tokens=[])
        with mock_judge0(post_token="tok-123", get_result=judge0_result(stdout=JUNIT_ALL_PASS)) as requests_mock:
            self.question.grader.submit(submission)

        self.assertEqual(requests_mock.post.call_count, 1)
        self.assertEqual(submission.tokens, ["tok-123"])

        url = requests_mock.post.call_args[0][0]
        self.assertTrue(url.endswith("/submissions"))
        data = requests_mock.post.call_args[1]["data"]
        self.assertEqual(data["language_id"], 46)
        self.assertFalse(data["base64_encoded"])
        self.assertFalse(data["wait"])
        self.assertIn("Main.java", data["source_code"])
        self.assertTrue(len(data["additional_files"]) > 0)
        self.assertEqual(requests_mock.post.call_args[1]["headers"], JunitGrader.HEADERS)

        # submit() immediately polls once
        self.assertEqual(requests_mock.get.call_count, 1)
        self.assertEqual(len(submission.results), 1)


class SubmissionSaveWithMockedJudge0Tests(TestCase):
    """End-to-end: saving a JavaSubmission grades it and cleans up over Judge0."""

    @classmethod
    def setUpTestData(cls):
        cls.user = create_user("grader_saver")
        cls.category = create_category()
        cls.question = create_java_question(author=cls.user, category=cls.category)

    def setUp(self):
        self.uqj = get_uqj(self.user, self.question)

    def test_saving_a_correct_submission_updates_uqj_and_deletes_judge0_submission(self):
        submission = build_java_submission(self.uqj, [judge0_result(stdout=JUNIT_ALL_PASS)])
        with mock_judge0() as requests_mock:
            submission.save()

        stored = JavaSubmission.objects.get(pk=submission.pk)
        self.assertTrue(stored.is_correct)
        self.assertEqual(stored.grade, 1.0)
        self.assertTrue(stored.finalized)

        self.uqj.refresh_from_db()
        self.assertEqual(self.uqj.grade, 1.0)
        # EASY questions default to a token value of 1 (TokenValue.save)
        self.assertEqual(self.uqj.tokens_received, 1.0)

        # KNOWN-BUG: Submission.save (course/models/models.py:530-537) calls
        # uqj.save() *before* super().save(), so UserQuestionJunction.save
        # (:425-430) queries self.submissions before this submission row exists
        # and is_solved stays False.  It only flips on the *next* uqj.save().
        self.assertFalse(self.uqj.is_solved)
        self.uqj.save()
        self.uqj.refresh_from_db()
        self.assertTrue(self.uqj.is_solved)
        self.assertIsNotNone(self.uqj.solved_at)

        self.assertEqual(requests_mock.delete.call_count, 1)
        self.assertEqual(self.user.actions.count(), 1)

    def test_saving_a_partially_correct_submission(self):
        submission = build_java_submission(self.uqj, [judge0_result(stdout=JUNIT_SOME_FAIL)])
        with mock_judge0():
            submission.save()

        stored = JavaSubmission.objects.get(pk=submission.pk)
        self.assertFalse(stored.is_correct)
        self.assertTrue(stored.is_partially_correct)
        self.assertEqual(stored.grade, 0.5)

        self.uqj.refresh_from_db()
        self.assertFalse(self.uqj.is_solved)
        self.assertEqual(self.uqj.tokens_received, 0.5)
        # KNOWN-BUG: same one-save lag as above -- is_partially_solved is
        # computed before the submission row is written.
        self.assertFalse(self.uqj.is_partially_solved)
        self.uqj.save()
        self.uqj.refresh_from_db()
        self.assertTrue(self.uqj.is_partially_solved)

    def test_saving_an_in_progress_submission_does_not_finalize_or_clean_up(self):
        submission = build_java_submission(self.uqj, [judge0_result(status_id=JUDGE0_IN_QUEUE, description="In Queue")])
        with mock_judge0(get_result=judge0_result(status_id=JUDGE0_IN_QUEUE, description="In Queue")) as requests_mock:
            submission.save()

        stored = JavaSubmission.objects.get(pk=submission.pk)
        self.assertFalse(stored.finalized)
        self.assertFalse(stored.is_correct)
        self.assertEqual(stored.grade, 0)
        self.assertEqual(requests_mock.delete.call_count, 0)
        self.assertEqual(self.user.actions.count(), 0)


class MultipleChoiceGraderCleanUpTests(TestCase):
    """The MCQ grader's clean_up is a no-op -- pinned so the contract stays."""

    def test_clean_up_is_a_noop(self):
        self.assertIsNone(MultipleChoiceGrader().clean_up(None))
