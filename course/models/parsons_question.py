import base64

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
