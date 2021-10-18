# Create your tests here.
from api.serializers import MultipleChoiceQuestionSerializer
from course.utils.utils import create_mcq_submission
from general.models.action import Action, ActionVerb
from general.services.action import create_login_action, create_logout_action, create_submission_action, \
    give_user_consent_action, remove_user_consent_action, update_user_profile_action, change_password_action, \
    reset_password_email_action, reset_password_action, create_question_action, update_question_action, \
    delete_question_action
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


class GiveUserConsentActionTest(BaseTestCase):
    def test(self):
        give_user_consent_action(self.user, {})
        self.assertTrue(
            Action.objects.filter(
                actor=self.user,
                verb=ActionVerb.COMPLETED
            ).exists()
        )


class RemoveUserConsentActionTest(BaseTestCase):
    def test(self):
        remove_user_consent_action(self.user, {})
        self.assertTrue(
            Action.objects.filter(
                actor=self.user,
                verb=ActionVerb.COMPLETED
            ).exists()
        )


class UpdateUserProfileActionTest(BaseTestCase):
    def test(self):
        update_user_profile_action(self.user, {})
        self.assertTrue(
            Action.objects.filter(
                actor=self.user,
                verb=ActionVerb.UPDATED
            ).exists()
        )


class ChangePasswordActionTest(BaseTestCase):
    def test(self):
        change_password_action(self.user)
        self.assertTrue(
            Action.objects.filter(
                actor=self.user,
                verb=ActionVerb.UPDATED
            ).exists()
        )


class ResetPasswordEmailActionTest(BaseTestCase):
    def test(self):
        reset_password_email_action(self.user)
        self.assertTrue(
            Action.objects.filter(
                actor=self.user,
                verb=ActionVerb.COMPLETED
            ).exists()
        )


class ResetPasswordActionTest(BaseTestCase):
    def test(self):
        reset_password_action(self.user)
        self.assertTrue(
            Action.objects.filter(
                actor=self.user,
                verb=ActionVerb.UPDATED
            ).exists()
        )


class CreateQuestionActionTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.question = self.user.question_junctions.filter(question__answer='a').first().question

    def test(self):
        create_question_action(MultipleChoiceQuestionSerializer(self.question).data, self.user)
        question_action = Action.objects.get(actor=self.user, verb=ActionVerb.CREATED)
        self.assertIsNotNone(question_action)


class UpdateQuestionActionTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.question = self.user.question_junctions.filter(question__answer='a').first().question

    def test(self):
        update_question_action(MultipleChoiceQuestionSerializer(self.question).data, self.user)
        question_action = Action.objects.get(actor=self.user, verb=ActionVerb.UPDATED)
        self.assertIsNotNone(question_action)


class DeleteQuestionActionTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.question = self.user.question_junctions.filter(question__answer='a').first().question

    def test(self):
        delete_question_action(MultipleChoiceQuestionSerializer(self.question).data, self.user)
        question_action = Action.objects.get(actor=self.user, verb=ActionVerb.DELETED)
        self.assertIsNotNone(question_action)


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
