import jsonfield
from django.db import models

from course.grader.grader import JunitGrader
from course.models.models import VariableQuestion, CodeSubmission


class ParsonsQuestion(VariableQuestion):
    input_files = jsonfield.JSONField(default=[])
    """
    [{
        "name": string
        "compile": boolean // whether to compile this input as a separate file or not
        "lines": [string]
    }...]
    """
    junit_template = models.TextField()

    grader = JunitGrader()

    def get_input_files(self):
        return self.input_files


class ParsonsSubmission(CodeSubmission):
    answer_files = jsonfield.JSONField()
    """
    {
        file_name: string
        ...
    }
    """

    def get_answer_files(self):
        return {file_name: code for file_name, code in self.answer_files.items() if self.uqj.should_compile(file_name)}

    def get_embed_files(self):
        return self.answer_files
