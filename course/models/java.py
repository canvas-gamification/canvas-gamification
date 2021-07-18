from django.db import models

from course.fields import JSONField
from course.grader.grader import JunitGrader
from course.models.models import VariableQuestion, CodeSubmission


class JavaQuestion(VariableQuestion):
    input_files = JSONField()
    """
        [{
            "name": string
            "compile": boolean // whether to compile this input as a separate file or not
            "template": string
        }...]
    """
    junit_template = models.TextField()

    grader = JunitGrader()

    def should_compile(self, file_name):
        for input_file in self.input_files:
            if input_file['name'] == file_name:
                return input_file['compile']
        return False

    def get_input_file_names(self):
        input_files = [
            x['name']
            for x in self.input_files
            if x['compile']
        ]
        return " ".join(input_files)

    def get_input_files(self):
        return self.input_files


class JavaSubmission(CodeSubmission):
    answer_files = JSONField()
    """
        {
            file_name: string
            ...
        }
    """

    def get_answer_files(self):
        return {
            file_name: code
            for file_name, code in self.answer_files.items() if self.question.should_compile(file_name)
        }

    def get_embed_files(self):
        return self.answer_files
