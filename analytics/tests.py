from accounts.models import MyUser
from course.models.models import Submission
from course.utils.utils import create_mcq_submission, create_multiple_choice_question
from test.base import BaseTestCase
from .models import MCQSubmissionAnalytics
from .utils import init_analytics


class SubmissionAnalyticsTestCase(BaseTestCase):
    TEST_CODE1 = """public class Test
        {
            //test comment
            public static void main(String[] args)
            {	int x = 100;
            for(int i = 0; i < x; i++)
                System.out.println( i ); //prints out
            }
        
            public static double some_calc(int n)
            {	double res = 1;
                for(int i = 2; i <= n; i++)
                    res *= i;
                return res;
            }
    } """

    TEST_CODE2 = """public class StringExample
    {	public static void main(String[] args)
        {	String s1 = "ss";
            int x = 31;
            String s2 = s1 + " " + x;
            
            System.out.println("s1: " + s1);
            System.out.println("s2: " + s2);
            
            //test comment
            
            x = 16;
            int y = 44;
            String s3 = x + y;
        }
    }"""

    TEST_CODE3 = """public class Test
    {
        public static void main(String[] args) {
            printOnce();
            printOnce();
            printTwice();
        }
    
        public static void printOnce() {
            System.out.println("1");
        }
    
        public static void printTwice() {
            printOnce();
            printOnce();
        }
    }"""

    TEST_CODE4 = """public class Deadlock {
    
        public static void main(String[] args) {
            Object a = new Object();
            Object b = new Object();
            Object c = new Object();
            
            System.out.println("hellp!");
            Thread t1 = new Thread() {
                public void run() {
                    synchronized(a) {
                        try {
                            Thread.sleep(1000);
                        }
                        catch(Exception e) {
    
                        }
                        
                        synchronized(b) {
                            System.out.println("Occupying b!");
                        }
                    }}
            };
            t1.start();
    
            Thread t2 = new Thread() {
                public void run() {
                    synchronized(b) {
                    try {
                        Thread.sleep(1000);
                    }
                    catch(Exception e) {
    
                    }
                    synchronized(c) {
                        System.out.println("Occupying c!");
                    }
                }}
            };
            t2.start();
            Thread t3 = new Thread() {
                public void run() {
                    synchronized(c) {
                    try {
                        Thread.sleep(1000);
                    }
                    catch(Exception e) {
    
                    }
                    synchronized(a) {
                        System.out.println("Occupying a!");
                    }
                }}
            };
            t3.start();
        }
    
    }"""

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
        submission = Submission.objects.first()
        try:
            sub_analytics1 = MCQSubmissionAnalytics.objects.filter(submission=submission.pk).first()
        except MCQSubmissionAnalytics.DoesNotExist:
            sub_analytics1 = None
        self.assertEquals(mcq_submission.pk, sub_analytics1.submission)
        self.assertEquals(MCQSubmissionAnalytics.objects.count(), 1)

    def test_num_lines(self, test_code=TEST_CODE1):
        self.assertEquals(init_analytics.num_lines(""), 0)
        self.assertEquals(init_analytics.num_lines("int x = 1;\nint y = 2;\n"), 3)
        self.assertEquals(init_analytics.num_lines("\n\n\n\n\n"), 6)
        self.assertEquals(init_analytics.num_lines(test_code), 16)

    def test_num_blank_lines(self, test_code=TEST_CODE1):
        self.assertEquals(init_analytics.num_blank_lines(test_code), 1)
        code = """int x = 1;\n\n\n\nint x = 1;\nint x=1\n"""
        self.assertEquals(init_analytics.num_blank_lines(code), 4)
        self.assertEquals(init_analytics.num_blank_lines(""), 0)

    def test_import_lines(self, test_code=TEST_CODE1):
        self.assertEquals(init_analytics.num_import(""), 0)
        self.assertEquals(init_analytics.num_import(test_code), 0)
        self.assertEquals(init_analytics.num_import("import java.util.*;\nimport java.time.*;"), 2)

    def test_comment_lines(self, test_code=TEST_CODE1):
        self.assertEquals(init_analytics.num_comments(""), 0)
        self.assertEquals(init_analytics.num_comments(test_code), 2)
        self.assertEquals(init_analytics.num_comments("///////////////////"), 1)
        self.assertEquals(init_analytics.num_comments("/*this is a comment\nnextline*/"), 1)

    def test_num_method(self, test_code=TEST_CODE1, test_code2=TEST_CODE3, test_code3=TEST_CODE4):
        self.assertEquals(init_analytics.num_method(""), 0)
        self.assertEquals(init_analytics.num_method(test_code), 2)
        self.assertEquals(init_analytics.num_method(test_code2), 3)
        self.assertEquals(init_analytics.num_method(test_code3), 4)

    def test_op(self, test_code=TEST_CODE2, test_code1=TEST_CODE1):
        res = init_analytics.num_op(test_code)
        self.assertEquals(res[0], 11)
        self.assertEquals(res[1], 19)

        res1 = init_analytics.num_op(test_code1)
        self.assertEquals(res1[0], 9)
        self.assertEquals(res1[1], 16)

    def test_cc(self, test_code=TEST_CODE1):
        self.assertEquals(init_analytics.calc_cc(""), 1)
        self.assertEquals(init_analytics.calc_cc(" "), 1)
        self.assertEquals(init_analytics.calc_cc(test_code), 3)

