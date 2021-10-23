from django.db import models
from accounts.models import MyUser
from course.models.models import Question


class QuestionReport(models.Model):
    user = models.ForeignKey(MyUser, on_delete=models.CASCADE, db_index=True)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    typo_in_question = models.BooleanField(default=False, db_index=True)
    typo_in_answer = models.BooleanField(default=False, db_index=True)
    correct_solution_marked_wrong = models.BooleanField(default=False, db_index=True)
    incorrect_solution_marked_right = models.BooleanField(default=False, db_index=True)
    other = models.BooleanField(default=False, db_index=True)
    report_details = models.TextField(default=False, db_index=True)

    class Meta:
        unique_together = ('user', 'question')
