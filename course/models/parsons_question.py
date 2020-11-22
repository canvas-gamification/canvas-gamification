from django.db import models

from course.fields import JSONField
from course.grader.grader import JunitGrader
from course.models.models import VariableQuestion, CodeSubmission


class ParsonsQuestion(VariableQuestion):
    lines = JSONField(default='[]')
    junit_template = models.TextField()
    additional_file_name = models.CharField(max_length=100, null=True, blank=True, default=None)

    grader = JunitGrader()

    def get_input_file_names(self):
        return self.additional_file_name


class ParsonsSubmission(CodeSubmission):
    def no_file_answer(self):
        return self.question.additional_file_name is None

    def get_answer_files(self):
        if self.no_file_answer():
            return {}
        return {
            self.question.additional_file_name: self.answer
        }
