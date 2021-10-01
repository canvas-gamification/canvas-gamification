from accounts.models import MyUser
from course.models.models import Question, Submission
from course.utils.utils import create_multiple_choice_question, create_mcq_submission
from test.base import BaseTestCase


class EnsureUQJTest(BaseTestCase):

    def setUp(self):
        super().setUp()
        MyUser.objects.create_user('test_user2', "test2@s202.ok.ubc.ca", "aaaaaaaa")

    def test_ensure_uqj(self):
        self.assertEquals(self.user.question_junctions.count(), Question.objects.all().count())

        user = MyUser.objects.get(username='test_user2')
        self.assertEquals(user.question_junctions.count(), Question.objects.all().count())
        self.assertEqual(Question.objects.first().user_junctions.count(), MyUser.objects.count())

        user.save()
        self.user.save()
        for q in Question.objects.all():
            q.save()

        self.assertEquals(self.user.question_junctions.count(), Question.objects.all().count())
        self.assertEquals(user.question_junctions.count(), Question.objects.all().count())
        self.assertEqual(Question.objects.first().user_junctions.count(), MyUser.objects.count())


class McqSubmissionTestCase(BaseTestCase):

    def setUp(self):
        super().setUp()

        create_multiple_choice_question(
            title="title",
            text='text',
            answer='a,b',
            max_submission_allowed=999,
            tutorial='tt',
            author=self.user,
            category=self.category,
            difficulty="EASY",
            is_verified=True,
            variables='[]',
            choices={'a': 'a', 'b': 'b', 'c': 'c', 'd': 'd'},
            visible_distractor_count=3,
            event=self.event
        )
        create_multiple_choice_question(
            title="title",
            text='text',
            answer='a,b,c',
            max_submission_allowed=999,
            tutorial='tt',
            author=self.user,
            category=self.category,
            difficulty="EASY",
            is_verified=True,
            variables='[]',
            choices={'a': 'a', 'b': 'b', 'c': 'c', 'd': 'd'},
            visible_distractor_count=3,
            event=self.event
        )

        create_multiple_choice_question(
            title="title",
            text='text',
            answer='a',
            max_submission_allowed=999,
            tutorial='tt',
            author=self.user,
            category=self.category,
            difficulty="EASY",
            is_verified=True,
            variables='[]',
            choices={'a': 'a', 'b': 'b', 'c': 'c', 'd': 'd'},
            visible_distractor_count=3,
            event=self.event
        )


class EnsureCorrectMcqGradingOneAnswerTest(McqSubmissionTestCase):

    def setUp(self):
        super().setUp()
        self.uqj = self.user.question_junctions.filter(question__answer='a').first()

    def test_blank_answer(self):
        create_mcq_submission(self.uqj, '')
        self.assertEquals(getattr(Submission.objects.first(), 'grade'), 0)

    def test_correct_answer(self):
        create_mcq_submission(self.uqj, 'a')
        self.assertEquals(getattr(Submission.objects.first(), 'grade'), 1)

    def test_incorrect_answer(self):
        create_mcq_submission(self.uqj, 'b')
        self.assertEquals(getattr(Submission.objects.first(), 'grade'), 0)


class EnsureCorrectMcqGradingTwoAnswersTest(McqSubmissionTestCase):

    def setUp(self):
        super().setUp()
        self.uqj = self.user.question_junctions.filter(question__answer='a,b').first()

    def test_duplicated_correct_choice(self):
        create_mcq_submission(self.uqj, 'a,a')
        self.assertEquals(getattr(Submission.objects.first(), 'grade'), 0)

    def test_reversed_correct_choice(self):
        create_mcq_submission(self.uqj, 'b,a')
        self.assertEquals(getattr(Submission.objects.first(), 'grade'), 1)

    def test_incorrect_choices(self):
        create_mcq_submission(self.uqj, '!@#')
        self.assertEquals(getattr(Submission.objects.first(), 'grade'), 0)

    def test_one_correct_choice(self):
        create_mcq_submission(self.uqj, 'b')
        self.assertEquals(getattr(Submission.objects.first(), 'grade'), 0.5)

    def test_one_incorrect_one_correct_choice(self):
        create_mcq_submission(self.uqj, 'a,c')
        self.assertEquals(getattr(Submission.objects.first(), 'grade'), 0)

    def test_empty_string(self):
        create_mcq_submission(self.uqj, '')
        self.assertEquals(getattr(Submission.objects.first(), 'grade'), 0)


class EnsureCorrectMcqGradingThreeAnswersTest(McqSubmissionTestCase):

    def setUp(self):
        super().setUp()
        self.uqj = self.user.question_junctions.filter(question__answer='a,b,c').first()

    def test_one_incorrect_two_correct_choice(self):
        create_mcq_submission(self.uqj, 'a,b,d')
        self.assertEquals(getattr(Submission.objects.first(), 'grade'), 0.33)

    def test_one_correct_two_duplicated_correct_choice(self):
        create_mcq_submission(self.uqj, 'a,b,a')
        self.assertEquals(getattr(Submission.objects.first(), 'grade'), 0.33)

    def test_empty_string(self):
        create_mcq_submission(self.uqj, '')
        self.assertEquals(getattr(Submission.objects.first(), 'grade'), 0)

    def test_one_correct_choice(self):
        create_mcq_submission(self.uqj, 'a')
        self.assertEquals(getattr(Submission.objects.first(), 'grade'), 0.33)

    def test_two_correct_choice(self):
        create_mcq_submission(self.uqj, 'c,a')
        self.assertEquals(getattr(Submission.objects.first(), 'grade'), 0.67)

    def test_two_incorrect_one_correct_choice(self):
        create_mcq_submission(self.uqj, 'efa')
        self.assertEquals(getattr(Submission.objects.first(), 'grade'), 0)
