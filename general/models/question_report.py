from django.db import models


class QuestionReport(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # These fields will be changed in the future when we discuss with Bowen
    # For now, they will be used to test if the backend works.

    unclear_description = models.BooleanField(default=False, db_index=True)
    test_case_incorrect_answer = models.BooleanField(default=False, db_index=True)
    test_case_violate_constraints = models.BooleanField(default=False, db_index=True)
    poor_test_coverage = models.BooleanField(default=False, db_index=True)
    language_specific_issue = models.BooleanField(default=False, db_index=True)
    other = models.BooleanField(default=False, db_index=True)
    report_text = models.TextField(default=False, db_index=True)
