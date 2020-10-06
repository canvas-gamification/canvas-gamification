from django.db import models

from course.fields import JSONField
from course.grader import JunitGrader
from course.models.models import VariableQuestion, CodeSubmission


class ParsonsQuestion(VariableQuestion):
    lines = JSONField(default='[]')
    junit_template = models.TextField()
    additional_file_name = models.CharField(max_length=100, null=True, blank=True, default=None)

    grader = JunitGrader()


class ParsonsSubmission(CodeSubmission):
    pass
