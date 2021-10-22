from django.db import models


class QuestionReport(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    typo_in_question = models.BooleanField(default=False, db_index=True)
    typo_in_answer = models.BooleanField(default=False, db_index=True)
    correct_solution_marked_wrong = models.BooleanField(default=False, db_index=True)
    incorrect_solution_marked_right = models.BooleanField(default=False, db_index=True)
    other = models.BooleanField(default=False, db_index=True)
    report_details = models.TextField(default=False, db_index=True)
