from analytics.models.models import SubmissionAnalytics, QuestionAnalytics
from django.db import models
from course.fields import JSONField


class JavaSubmissionAnalytics(SubmissionAnalytics):
    lines = models.IntegerField(default=0)
    blank_lines = models.IntegerField(default=0)
    comment_lines = models.IntegerField(default=0)
    import_lines = models.IntegerField(default=0)
    cyclomatic_complexity = models.IntegerField(default=0)
    method = models.IntegerField(default=0)
    # all fields below are part of Halstead metrics for analyzing code complexity
    operator = models.IntegerField(default=0)
    operand = models.IntegerField(default=0)
    unique_operator = models.IntegerField(default=0)
    unique_operand = models.IntegerField(default=0)
    vocab = models.IntegerField(default=0)
    size = models.IntegerField(default=0)
    vol = models.DecimalField(max_digits=8, decimal_places=4, default=0)
    difficulty = models.DecimalField(max_digits=8, decimal_places=4, default=0)
    effort = models.DecimalField(max_digits=8, decimal_places=4, default=0)
    error = models.DecimalField(max_digits=8, decimal_places=4, default=0)
    test_time = models.DecimalField(max_digits=8, decimal_places=4, default=0)
    ans_file = JSONField()


class JavaQuestionAnalytics(QuestionAnalytics):
    lines = models.IntegerField(default=0)
    blank_lines = models.IntegerField(default=0)
    comment_lines = models.IntegerField(default=0)
    import_lines = models.IntegerField(default=0)
    cc = models.IntegerField(default=0)
    method = models.IntegerField(default=0)
    operator = models.IntegerField(default=0)
    operand = models.IntegerField(default=0)
    unique_operator = models.IntegerField(default=0)
    unique_operand = models.IntegerField(default=0)
    vocab = models.IntegerField(default=0)
    size = models.IntegerField(default=0)
    vol = models.DecimalField(max_digits=8, decimal_places=4, default=0)
    difficulty = models.DecimalField(max_digits=8, decimal_places=4, default=0)
    effort = models.DecimalField(max_digits=8, decimal_places=4, default=0)
    error = models.DecimalField(max_digits=8, decimal_places=4, default=0)
    test_time = models.DecimalField(max_digits=8, decimal_places=4, default=0)

