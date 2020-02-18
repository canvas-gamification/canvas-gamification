import jsonfield
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
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


class Question(PolymorphicModel):
    title = models.CharField(max_length=300, null=True, blank=True)
    text = RichTextField(null=True, blank=True)
    answer = models.TextField(null=True, blank=True)
    tutorial = RichTextField(null=True, blank=True)
    time_created = models.DateTimeField(auto_now_add=True)
    time_modified = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True)
    category = models.ForeignKey(QuestionCategory, on_delete=models.SET_NULL, null=True, blank=True)

    def get_grader(self):
        raise NotImplementedError()


class VariableQuestion(Question):
    variables = jsonfield.JSONField()

    @property
    def rendered_text(self):
        return self.text.format(**self.variables)

    def get_grader(self):
        raise NotImplementedError()


class MultipleChoiceQuestion(VariableQuestion):
    choices = jsonfield.JSONField()

    @property
    def rendered_choices(self):
        res = {}
        for key, val in self.choices.items():
            res[key] = val.format(**self.variables)
        return res

    def get_grader(self):
        return MultipleChoiceGrader(self.answer)


class Submission(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='submissions')
    grade = models.FloatField(default=0)
    answer = models.TextField(null=True, blank=True)
    submission_time = models.DateTimeField(auto_now_add=True)

    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='submissions')

    def calculate_grade(self):
        return self.question.get_grader().grade(self.answer)

    def save(self, *args, **kwargs):
        self.grade = self.calculate_grade()
        super().save(*args, **kwargs)
