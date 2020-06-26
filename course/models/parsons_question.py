from course.grader import ParsonsGrader
from course.models.models import VariableQuestion, CodeSubmission
from course.fields import JSONField
from django.db import models
import base64

class ParsonsQuestion(VariableQuestion):
    lines = JSONField(default='[]')
    junit_template = models.TextField()

    def get_lines(self):
        return self.lines

    def get_grader(self, user):
        return ParsonsGrader(self, user)


class ParsonsSubmission(CodeSubmission):

    def get_decoded_stdout(self):
        return base64.b64decode(self.results[0]['stdout']).decode('utf-8')
