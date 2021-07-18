from django.db import models

from course.fields import JSONField
from course.grader.grader import MultipleChoiceGrader
from course.models.models import VariableQuestion, Submission


class MultipleChoiceQuestion(VariableQuestion):
    choices = JSONField()
    visible_distractor_count = models.IntegerField()
    grader = MultipleChoiceGrader()

    @property
    def is_checkbox(self):
        return ',' in self.answer


class MultipleChoiceSubmission(Submission):
    @property
    def answer_display(self):
        values = []
        rendered_choices = self.uqj.get_rendered_choices()
        for answer in self.answer.split(','):
            values.append(rendered_choices.get(answer, 'Unknown'))
        return values
