from django.db import models

from canvas.models import Event
from course.models.models import Submission, Question, UserQuestionJunction
from course.fields import JSONField


class SubmissionAnalytics(models.Model):
    id = models.AutoField(primary_key=True)
    submission_type = models.CharField(max_length=255, default="n/a")
    uqj = models.ForeignKey(UserQuestionJunction, on_delete=models.CASCADE)
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, null=True)
    user_id = models.IntegerField(default=0)
    first_name = models.CharField(max_length=255, default="n/a")
    last_name = models.CharField(max_length=255, default="n/a")
    ans_file = JSONField()
    ans = models.CharField(max_length=5, default="n/a")
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


class QuestionAnalytics(models.Model):
    id = models.AutoField(primary_key=True)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, null=True)
    number_submission = models.IntegerField(default=0)
    avg_grade = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    correct_rate = models.DecimalField(max_digits=8, decimal_places=4, default=0)

    frequently_wrong_ans = models.CharField(max_length=5, default="n/a")
    frequently_wrong_reason = models.CharField(max_length=255, default="n/a")

    lines = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    blank_lines = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    comment_lines = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    import_lines = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    cc = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    method = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    operator = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    operand = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    unique_operator = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    unique_operand = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    vocab = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    size = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    vol = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    difficulty = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    effort = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    error = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    test_time = models.DecimalField(max_digits=8, decimal_places=2, default=0)


# class EventAnalytics(models.Model):
#     id = models.AutoField(primary_key=True)
#     event = models.ForeignKey(Event, on_delete=models.CASCADE, null=True)
#     avg_grade = models.DecimalField(max_digits=8, decimal_places=2, default=0)
#     frequently_wrong_questions = JSONField()
#     """
#         [{
#             question_number = string
#             title = string
#             text = string
#             answer = string
#             wrong_answer = string
#             reason_wrong = string (for java & parson, n/a for mcq)
#             category = string
#             // sub_category = string
#             num_wrong = number
#             num_submission = number
#         }...]
#     """
