from django.db import models
from polymorphic.models import PolymorphicModel

from accounts.models import MyUser
from canvas.models import Event, CanvasCourse
from course.fields import JSONField
from course.models.models import Submission, Question, UserQuestionJunction


class SubmissionAnalytics(PolymorphicModel):
    id = models.AutoField(primary_key=True)
    time_created = models.DateTimeField(auto_now_add=True)
    uqj = models.ForeignKey(UserQuestionJunction, on_delete=models.CASCADE)
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    user_id = models.ForeignKey(MyUser, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=255, default="n/a")
    last_name = models.CharField(max_length=255, default="n/a")
    num_attempts = models.IntegerField(default=0)
    is_correct = models.BooleanField(default=False)
    time_spent = models.IntegerField(default=0)


class QuestionAnalytics(PolymorphicModel):
    id = models.AutoField(primary_key=True)
    time_created = models.DateTimeField(auto_now_add=True)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    course = models.ForeignKey(CanvasCourse, on_delete=models.CASCADE, null=True)

    most_frequent_wrong_ans = JSONField()
    avg_grade = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    grade_std_dev = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    num_respondents = models.IntegerField(default=0)
    avg_attempt = models.DecimalField(max_digits=4, decimal_places=1, default=0)
    attempt_std_dev = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    median_time_spent = models.DecimalField(max_digits=6, decimal_places=2, default=0)
