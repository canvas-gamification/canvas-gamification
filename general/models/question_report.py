from django.db import models
from accounts.models import MyUser
from course.models.models import Question


class QuestionReport(models.Model):
    user = models.ForeignKey(MyUser, on_delete=models.CASCADE, db_index=True)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, db_index=True)
    report_timestamp = models.DateTimeField(default=None, null=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    unclear_description = models.BooleanField(default=False, db_index=True)
    test_case_incorrect_answer = models.BooleanField(default=False, db_index=True)
    test_case_violate_constraints = models.BooleanField(default=False, db_index=True)
    poor_test_coverage = models.BooleanField(default=False, db_index=True)
    language_specific_issue = models.BooleanField(default=False, db_index=True)
    other = models.BooleanField(default=False, db_index=True)
    report_text = models.TextField(default=False, db_index=True)

    class Meta:
        unique_together = ('user', 'question')
