from django.db import models
from polymorphic.models import PolymorphicModel

from accounts.models import MyUser
from analytics.utils import init_analytics


class SubmissionAnalyticsObj:
    def __init__(self, submission_code):
        lines = 0
        blank_lines = 0
        comment_lines = 0
        import_lines = 0
        cc = 0
        method = 0
        operator = 0
        operand = 0
        operator_list = []
        operand_list = []
        halstead = [0, 0, 0, 0, 0, 0, 0, 0, 0]

        for string in submission_code.values():
            lines += init_analytics.num_lines(string)
            blank_lines += init_analytics.num_blank_lines(string)
            comment_lines += init_analytics.num_comments(string)
            import_lines += init_analytics.num_import(string)
            cc += init_analytics.calc_cc(string)
            method += init_analytics.num_method(string)
            op_list = init_analytics.num_op(string)
            operator += op_list[0]
            operand += op_list[1]
            operator_list.append(op_list[2])
            operand_list.append(op_list[3])
            if string is not None:
                halstead = init_analytics.halstead(operator_list, operand_list, operator, operand)

        unique_operator = halstead[0]
        unique_operand = halstead[1]
        vocab = halstead[2]
        size = halstead[3]
        vol = halstead[4]
        difficulty = halstead[5]
        effort = halstead[6]
        error = halstead[7]
        test_time = halstead[8]

        self.lines = lines
        self.blank_lines = blank_lines
        self.comment_lines = comment_lines
        self.imported_lines = import_lines
        self.cc = cc
        self.method = method
        self.operator = operator
        self.operand = operand
        self.unique_operator = unique_operator
        self.unique_operand = unique_operand
        self.vocab = vocab
        self.size = size
        self.vol = vol
        self.difficulty = difficulty
        self.effort = effort
        self.error = error
        self.test_time = test_time


class SubmissionAnalytics(PolymorphicModel):
    id = models.AutoField(primary_key=True)
    uqj = models.IntegerField(default=0)
    submission = models.IntegerField(default=0)
    question = models.IntegerField(default=0)
    event = models.IntegerField(default=0)
    user_id = models.ForeignKey(MyUser, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=255, default="n/a")
    last_name = models.CharField(max_length=255, default="n/a")


class QuestionAnalytics(PolymorphicModel):
    id = models.AutoField(primary_key=True)
    question = models.IntegerField(default=0)
    event = models.IntegerField(default=0)
    number_submission = models.IntegerField(default=0)
    avg_grade = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    correct_rate = models.DecimalField(max_digits=8, decimal_places=4, default=0)

    frequent_wrong_ans = models.CharField(max_length=5, default="n/a")
    frequent_wrong_reason = models.CharField(max_length=255, default="n/a")
