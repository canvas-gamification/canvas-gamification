from course.grader import ParsonsGrader
from course.models.models import VariableQuestion, CodeSubmission
from course.fields import JSONField
from django.db import models
import base64
import random


class ParsonsQuestion(VariableQuestion):
    lines = JSONField(default='[]')
    junit_template = models.TextField()
    additional_file_name = models.CharField(max_length=100, null=True, blank=True, default=None)

    grader = ParsonsGrader()


class ParsonsSubmission(CodeSubmission):

    def get_decoded_stdout(self):
        stdout = self.results[0]['stdout']
        if stdout is None:
            stdout = ""
        return base64.b64decode(stdout).decode('utf-8')

    def get_decoded_compile_output(self):
        stdout = self.results[0]['compile_output']
        if stdout is None:
            stdout = ""
        return base64.b64decode(stdout).decode('utf-8')