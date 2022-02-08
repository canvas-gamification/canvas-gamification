import math

from accounts.models import MyUser
from course.models.java import JavaSubmission
from course.models.models import UserQuestionJunction
from course.models.parsons import ParsonsSubmission
from course.utils.utils import create_mcq_submission, create_multiple_choice_question
from test.base import BaseTestCase
from analytics.models import MCQSubmissionAnalytics
from analytics.models.models import SubmissionAnalytics
from analytics.services.submission_analytics import get_all_submission_analytics
from analytics.utils import init_analytics
from . import test_code


class SubmissionAnalyticsTestCase(BaseTestCase):

    def setUp(self):
        super().setUp()
        MyUser.objects.create_user('test_user2', "test2@s202.ok.ubc.ca", "aaaaaaaa")
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

    def test_ensure_db(self):
        self.uqj = self.user.question_junctions.filter(question__answer='a').first()
        mcq_submission = create_mcq_submission(self.uqj, '')
        get_all_submission_analytics()
        self.assertEquals(MCQSubmissionAnalytics.objects.count(), 1)

    def test_create_submission_analytics(self):
        uqj = UserQuestionJunction.objects.first()
        create_mcq_submission(
            uqj=uqj,
            answer=''
        )
        java_submission = JavaSubmission(
            uqj=uqj,
            answer=''
        )
        java_submission.save()
        parsons_submission = ParsonsSubmission(
            uqj=uqj,
            answer=''
        )
        parsons_submission.save()
        get_all_submission_analytics()
        self.assertEquals(SubmissionAnalytics.objects.all().count(), 3)

    def test_num_lines(self, test_code=test_code.TEST_CODE1):
        self.assertEquals(init_analytics.num_lines(""), 0)
        self.assertEquals(init_analytics.num_lines("int x = 1;\nint y = 2;\n"), 3)
        self.assertEquals(init_analytics.num_lines("\n\n\n\n\n"), 6)
        self.assertEquals(init_analytics.num_lines(test_code), 16)

    def test_num_blank_lines(self, test_code=test_code.TEST_CODE1):
        self.assertEquals(init_analytics.num_blank_lines(test_code), 1)
        code = """int x = 1;\n\n\n\nint x = 1;\nint x=1\n"""
        self.assertEquals(init_analytics.num_blank_lines(code), 4)
        self.assertEquals(init_analytics.num_blank_lines(""), 0)

    def test_import_lines(self, test_code=test_code.TEST_CODE1):
        self.assertEquals(init_analytics.num_import(""), 0)
        self.assertEquals(init_analytics.num_import(test_code), 0)
        self.assertEquals(init_analytics.num_import("import java.util.*;\nimport java.time.*;"), 2)

    def test_comment_lines(self, test_code=test_code.TEST_CODE1):
        self.assertEquals(init_analytics.num_comments(""), 0)
        self.assertEquals(init_analytics.num_comments(test_code), 2)
        self.assertEquals(init_analytics.num_comments("///////////////////"), 1)
        self.assertEquals(init_analytics.num_comments("/*this is a comment\nnextline*/"), 1)

    def test_num_method(self, test_code=test_code.TEST_CODE1, test_code2=test_code.TEST_CODE3, test_code3=test_code.TEST_CODE4):
        self.assertEquals(init_analytics.num_method(""), 0)
        self.assertEquals(init_analytics.num_method(test_code), 2)
        self.assertEquals(init_analytics.num_method(test_code2), 3)
        self.assertEquals(init_analytics.num_method(test_code3), 4)

    def test_op(self, test_code=test_code.TEST_CODE2, test_code1=test_code.TEST_CODE1):
        res = init_analytics.num_op(test_code)
        self.assertEquals(res[0], 11)
        self.assertEquals(res[1], 19)

        res1 = init_analytics.num_op(test_code1)
        self.assertEquals(res1[0], 9)
        self.assertEquals(res1[1], 16)

    def test_cc(self, test_code=test_code.TEST_CODE1):
        self.assertEquals(init_analytics.calc_cc(""), 1)
        self.assertEquals(init_analytics.calc_cc(" "), 1)
        self.assertEquals(init_analytics.calc_cc(test_code), 3)

    def test_halstead(self):
        res = init_analytics.calc_halstead(['+'], ['x', 'y'], 1, 2)
        self.assertEquals(res[0], 1)
        self.assertEquals(res[1], 2)
        self.assertEquals(res[2], 3)
        self.assertEquals(res[3], 3)
        self.assertEquals(res[4], 3 * math.log2(3))
        self.assertEquals(res[5], 1.5)
        self.assertEquals(res[6], 1.5 * 3 * math.log2(3))
        self.assertEquals(res[7], 3 * math.log2(3) / 3000)
        self.assertEquals(res[8], 1.5 * 3 * math.log2(3) / 18)
