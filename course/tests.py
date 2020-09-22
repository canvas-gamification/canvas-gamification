from django.test import TestCase, Client
from accounts.models import MyUser
from course.models.models import QuestionCategory, Question
from course.utils.utils import create_multiple_choice_question, create_java_question


class ProblemTestCase(TestCase):

    def setUp(self):
        self.client = Client()

        MyUser.objects.create_user("test_user", "test@s202.ok.ubc.ca", "aaaaaaaa")
        self.user = MyUser.objects.get()

        self.category = QuestionCategory(name="category", description="category")
        self.category.save()

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
                choices={'a':'a', 'b':'b'},
                visible_distractor_count=3
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
                additional_file_name='a.java'
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