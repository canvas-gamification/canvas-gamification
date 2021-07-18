from django.db import models

from course.fields import JSONField
from course.grader.grader import JunitGrader
from course.models.models import VariableQuestion, CodeSubmission


class JavaQuestion(VariableQuestion):
    junit_template = models.TextField()
    input_file_names = JSONField()

    grader = JunitGrader()

    def get_input_file_names(self):
        return " ".join(self.get_input_file_names_array())

    def get_input_file_names_array(self):
        return [x['name'] for x in self.input_file_names]

    def get_input_files(self):
        return self.input_file_names


class JavaSubmission(CodeSubmission):
    answer_files = JSONField()

    def get_answer_files(self):
        return self.answer_files

    def get_embed_files(self):
        return {}
