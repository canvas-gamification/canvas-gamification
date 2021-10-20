# Create your tests here.
from course.utils.utils import create_mcq_submission
from general.models.action import Action, ActionVerb
from general.services.action import create_login_action, create_logout_action, create_submission_action
from test.base import BaseTestCase


class LoginActionTest(BaseTestCase):
    def test(self):
        create_login_action(self.user)
        self.assertTrue(
            Action.objects.filter(
                actor=self.user,
                verb=ActionVerb.LOGGED_IN
            ).exists()
        )


class LogoutActionTest(BaseTestCase):
    def test(self):
        create_logout_action(self.user)
        self.assertTrue(
            Action.objects.filter(
                actor=self.user,
                verb=ActionVerb.LOGGED_OUT
            ).exists()
        )


class SubmissionActionTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.uqj = self.user.question_junctions.filter(question__answer='a').first()

    def test_incorrect_submission(self):
        submission = create_mcq_submission(self.uqj, 'b')
        create_submission_action(submission)

        submission_action = Action.objects.get(actor=self.user, verb=ActionVerb.SUBMITTED)
        submission_evaluation_action = Action.objects.get(actor=self.user, verb=ActionVerb.EVALUATED)

        self.assertIsNotNone(submission_action)
        self.assertEqual(submission_action.data['answer'], 'b')

        self.assertIsNotNone(submission_evaluation_action)
        self.assertEqual(submission_evaluation_action.data['grade'], 0)

    def test_correct_submission(self):
        submission = create_mcq_submission(self.uqj, 'a')
        create_submission_action(submission)

        submission_action = Action.objects.get(actor=self.user, verb=ActionVerb.SUBMITTED)
        submission_evaluation_action = Action.objects.get(actor=self.user, verb=ActionVerb.EVALUATED)

        self.assertIsNotNone(submission_action)
        self.assertEqual(submission_action.data['answer'], 'a')

        self.assertIsNotNone(submission_evaluation_action)
        self.assertEqual(submission_evaluation_action.data['grade'], 1)
