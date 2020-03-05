import random

import jsonfield
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db import models
from djrichtextfield.models import RichTextField
from polymorphic.models import PolymorphicModel

from course.grader import MultipleChoiceGrader


class QuestionCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.name


DIFFICULTY_CHOICES = [
    ("VERY EASY", "VERY EASY"),
    ("EASY", "EASY"),
    ("NORMAL", "NORMAL"),
    ("HARD", "HARD"),
    ("VERY HARD", "VERY HARD"),
]


def render_text(text, variables):
    text = str(text)
    for variable, value in variables.items():
        text = text.replace("{{"+variable+"}}", str(value))
    return text


class Question(PolymorphicModel):
    title = models.CharField(max_length=300, null=True, blank=True)
    text = RichTextField(null=True, blank=True)
    answer = models.TextField(null=True, blank=True)
    tutorial = RichTextField(null=True, blank=True)
    time_created = models.DateTimeField(auto_now_add=True)
    time_modified = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True)
    category = models.ForeignKey(QuestionCategory, on_delete=models.SET_NULL, null=True, blank=True)
    token_value = models.FloatField()
    difficulty = models.CharField(max_length=100, choices=DIFFICULTY_CHOICES)

    is_verified = models.BooleanField(default=False)


class VariableQuestion(Question):
    variables = jsonfield.JSONField()

    def get_variables(self, user):
        random.seed(user.pk or 0)

        size = len(self.variables)
        p = random.randrange(0, size)
        return self.variables[p]

    def get_rendered_text(self, user):
        return render_text(self.text, self.get_variables(user))


class MultipleChoiceQuestion(VariableQuestion):
    choices = jsonfield.JSONField()

    def get_rendered_choices(self, user):
        res = {}
        for key, val in self.choices.items():
            res[key] = render_text(val, self.get_variables(user))
        return res

    def get_grader(self, user):
        return MultipleChoiceGrader(self, user)


class Submission(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='submissions')
    grade = models.FloatField(default=0)
    is_correct = models.BooleanField(default=False)
    answer = models.TextField(null=True, blank=True)
    submission_time = models.DateTimeField(auto_now_add=True)

    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='submissions')

    @property
    def answer_display(self):
        return self.question.get_rendered_choices(self.user).get(self.answer, 'Unknown')

    @property
    def status(self):
        if self.is_correct:
            return "Correct"
        return "Wrong"

    def calculate_grade(self):
        return self.question.get_grader(self.user).grade(self)

    def save(self, *args, **kwargs):
        self.is_correct, self.grade = self.calculate_grade()
        super().save(*args, **kwargs)
