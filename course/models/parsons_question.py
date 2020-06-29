from course.grader import ParsonsGrader
from course.models.models import VariableQuestion, CodeSubmission
from course.fields import JSONField
from django.db import models
import base64


class ParsonsQuestion(VariableQuestion):
    lines = JSONField(default='[]')
    junit_template = models.TextField()

    grader = ParsonsGrader()

    def get_lines(self):
        return self.lines


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