from django.db import models
from accounts.models import MyUser
from course.models.models import Question

REPORT_CHOICES = [
    ("TYPO_TEXT", "There is a typo in the question instructions"),
    ("TYPO_ANSWER", "There is a typo in one of the multiple-choice answers"),
    ("RIGHT_SOLUTION_MARKED_WRONG", "My solution is definitely correct but it did not get full marks"),
    ("WRONG_SOLUTION_MARKED_RIGHT", "My solution is incorrect but it received full marks"),
    ("OTHER", "Other")
]


class QuestionReport(models.Model):
    user = models.ForeignKey(MyUser, on_delete=models.CASCADE, db_index=True)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    report = models.CharField(max_length=100, choices=REPORT_CHOICES)
    report_details = models.TextField(db_index=True, null=True)

    class Meta:
        unique_together = ('user', 'question')
