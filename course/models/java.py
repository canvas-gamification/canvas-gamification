from django.db import models

import jsonfield
from course.grader.grader import JunitGrader
from course.models.models import VariableQuestion, CodeSubmission


class JavaQuestion(VariableQuestion):
    input_files = jsonfield.JSONField()
    """
        [{
            "name": string
            "compile": boolean // whether to compile this input as a separate file or not
            "template": string
            "hidden": boolean // whether this file should not be displayed to the user and added to the submission later

        }...]
    """
    junit_template = models.TextField()

    grader = JunitGrader()

    def get_input_files(self):
        return self.input_files


class JavaSubmission(CodeSubmission):
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
