from django.db import models
from course.models.models import Submission, Question, UserQuestionJunction
from course.fields import JSONField


class SubmissionAnalytics(models.Model):
    id = models.AutoField(primary_key=True)
    submission_type = models.CharField(max_length=255, default="n/a")
    uqj = models.ForeignKey(UserQuestionJunction, on_delete=models.CASCADE)
    submission = models.OneToOneField(Submission, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    user_id = models.IntegerField(default=0)
    first_name = models.CharField(max_length=255, default="n/a")
    last_name = models.CharField(max_length=255, default="n/a")
    ans_file = JSONField()
    ans = models.CharField(max_length=255, default="n/a")
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
