from django.test import TestCase, Client
from django.utils import timezone

from accounts.models import MyUser
from course.models.models import QuestionCategory, Question, Event, CanvasCourse, Submission
from course.utils.utils import create_multiple_choice_question, create_java_question, create_mcq_submission


class ProblemTestCase(TestCase):

    def setUp(self):
        self.client = Client()

        MyUser.objects.create_user("test_user", "test@s202.ok.ubc.ca", "aaaaaaaa")
        self.user = MyUser.objects.get()

        self.category = QuestionCategory(name="category", description="category")
        self.category.save()

        self.course = CanvasCourse(
            mock=True,
            name="Test",
            url="http://canvas.ubc.ca",
            course_id=1,
            token="test token",

            allow_registration=True,
            visible_to_students=True,
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=10),

            verification_assignment_group_name="test",
            verification_assignment_name="test",
            bonus_assignment_group_name="test",
        )
        self.course.save()

        self.event = Event(
            name="test_event",
            type="ASSIGNMENT",
            course=self.course,
            count_for_tokens=False,
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=10)
        )
        self.event.save()

        for i in range(10):
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
                choices={'a': 'a', 'b': 'b'},
                visible_distractor_count=3,
                event=self.event
            )
            create_java_question(
                title='title',
                text='text',
                max_submission_allowed=999,
                tutorial='tutorial',
                author=self.user,
                category=self.category,
                difficulty='EASY',
                is_verified=True,
                junit_template='',
                input_files=[
                    {
                        'name': 'A.java',
                        'compile': False,
                        'template': '',
                    },
                    {
                        'name': 'B.java',
                        'compile': True,
                        'template': '',
                    },
                    {
                        'name': 'C.java',
                        'compile': False,
                        'template': '',
                    }
                ],
                event=self.event
            )

        MyUser.objects.create_user('test_user2', "test2@s202.ok.ubc.ca", "aaaaaaaa")


class EnsureUQJTest(ProblemTestCase):

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


class McqSubmissionTestCase(TestCase):

    def setUp(self):
        self.client = Client()

        MyUser.objects.create_user("test_user3", "test3@s202.ok.ubc.ca", "aaaaaaaa")
        self.user = MyUser.objects.get()

        self.category = QuestionCategory(name="category", description="category")
        self.category.save()

        self.course = CanvasCourse(
            mock=True,
            name="Test",
            url="http://canvas.ubc.ca",
            course_id=1,
            token="test token",

            allow_registration=True,
            visible_to_students=True,
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=10),

            verification_assignment_group_name="test",
            verification_assignment_name="test",
            bonus_assignment_group_name="test",
        )
        self.course.save()

        self.event = Event(
            name="test_event",
            type="ASSIGNMENT",
            course=self.course,
            count_for_tokens=False,
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=10)
        )
        self.event.save()

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

    def test_blank_answer(self):
        create_mcq_submission(self.user.question_junctions.all()[2], '')
        self.assertEquals(getattr(Submission.objects.first(), 'grade'), 0)

    def test_correct_answer(self):
        create_mcq_submission(self.user.question_junctions.all()[2], 'a')
        self.assertEquals(getattr(Submission.objects.first(), 'grade'), 1)

    def test_incorrect_answer(self):
        create_mcq_submission(self.user.question_junctions.all()[2], 'b')
        self.assertEquals(getattr(Submission.objects.first(), 'grade'), 0)


class EnsureCorrectMcqGradingTwoAnswersTest(McqSubmissionTestCase):

    def test_duplicated_correct_choice(self):
        create_mcq_submission(self.user.question_junctions.first(), 'a,a')
        self.assertEquals(getattr(Submission.objects.first(), 'grade'), 0)

    def test_reversed_correct_choice(self):
        create_mcq_submission(self.user.question_junctions.first(), 'b,a')
        self.assertEquals(getattr(Submission.objects.first(), 'grade'), 1)

    def test_incorrect_choices(self):
        create_mcq_submission(self.user.question_junctions.first(), '!@#')
        self.assertEquals(getattr(Submission.objects.first(), 'grade'), 0)

    def test_one_correct_choice(self):
        create_mcq_submission(self.user.question_junctions.first(), 'b')
        self.assertEquals(getattr(Submission.objects.first(), 'grade'), 0.5)

    def test_one_incorrect_one_correct_choice(self):
        create_mcq_submission(self.user.question_junctions.first(), 'a,c')
        self.assertEquals(getattr(Submission.objects.first(), 'grade'), 0)

    def test_empty_string(self):
        create_mcq_submission(self.user.question_junctions.all()[1], '')
        self.assertEquals(getattr(Submission.objects.first(), 'grade'), 0)


class EnsureCorrectMcqGradingThreeAnswersTest(McqSubmissionTestCase):

    def test_one_incorrect_two_correct_choice(self):
        create_mcq_submission(self.user.question_junctions.all()[1], 'a,b,d')
        self.assertEquals(getattr(Submission.objects.first(), 'grade'), 0.33)

    def test_one_correct_two_duplicated_correct_choice(self):
        create_mcq_submission(self.user.question_junctions.all()[1], 'a,b,a')
        self.assertEquals(getattr(Submission.objects.first(), 'grade'), 0.33)

    def test_empty_string(self):
        create_mcq_submission(self.user.question_junctions.all()[1], '')
        self.assertEquals(getattr(Submission.objects.first(), 'grade'), 0)

    def test_one_correct_choice(self):
        create_mcq_submission(self.user.question_junctions.all()[1], 'a')
        self.assertEquals(getattr(Submission.objects.first(), 'grade'), 0.33)

    def test_two_correct_choice(self):
        create_mcq_submission(self.user.question_junctions.all()[1], 'c,a')
        self.assertEquals(getattr(Submission.objects.first(), 'grade'), 0.67)

    def test_two_incorrect_one_correct_choice(self):
        create_mcq_submission(self.user.question_junctions.all()[1], 'efa')
        self.assertEquals(getattr(Submission.objects.first(), 'grade'), 0)
