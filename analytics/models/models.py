from django.db import models

from accounts.models import MyUser
from canvas.models import Event
from course.models.models import Submission, Question, UserQuestionJunction


class SubmissionAnalytics(models.Model):
    id = models.AutoField(primary_key=True)
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
