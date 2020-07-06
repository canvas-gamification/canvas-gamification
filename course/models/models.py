import json
import random
import math

from django.contrib.auth.models import AnonymousUser
from django.db import models
from django.urls import reverse_lazy
from djrichtextfield.models import RichTextField
from polymorphic.models import PolymorphicModel

from accounts.models import MyUser
from course.fields import JSONField
from course.grader import MultipleChoiceGrader, JavaGrader
from course.utils import get_user_question_junction, get_token_value
from general.models import Action


class QuestionCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        if self.parent is None:
            return self.name
        else:
            return "{} :: {}".format(self.parent, self.name)


DIFFICULTY_CHOICES = [
    ("EASY", "EASY"),
    ("NORMAL", "MEDIUM"),
    ("HARD", "HARD"),
]


def render_text(text, variables):
    text = str(text)
    for variable, value in variables.items():
        text = text.replace("{{" + variable + "}}", str(value))
    return text


class TokenValue(models.Model):
    value = models.FloatField()
    category = models.ForeignKey(QuestionCategory, on_delete=models.CASCADE, related_name='token_values')
    difficulty = models.CharField(max_length=100, choices=DIFFICULTY_CHOICES)

    def save(self, **kwargs):
        if self.value is None:
            if self.difficulty == 'EASY':
                self.value = 1
            if self.difficulty == "NORMAL":
                self.value = 2
            if self.difficulty == 'HARD':
                self.value = 3

        super().save(**kwargs)

    class Meta:
        unique_together = ('category', 'difficulty')


class Question(PolymorphicModel):
    title = models.CharField(max_length=300, null=True, blank=True)
    text = RichTextField(null=True, blank=True)
    answer = models.TextField(null=True, blank=True)
    max_submission_allowed = models.IntegerField(default=5, blank=True)
    tutorial = RichTextField(null=True, blank=True)
    time_created = models.DateTimeField(auto_now_add=True)
    time_modified = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(MyUser, on_delete=models.SET_NULL, null=True, blank=True)
    category = models.ForeignKey(QuestionCategory, on_delete=models.SET_NULL, null=True, blank=True)
    difficulty = models.CharField(max_length=100, choices=DIFFICULTY_CHOICES, default="EASY")

    is_verified = models.BooleanField(default=False)

    user = AnonymousUser()
    grader = None

    @property
    def is_allowed_to_submit(self):
        if not self.user.is_authenticated:
            return False
        return self.user.submissions.filter(question=self).count() < self.max_submission_allowed

    @property
    def is_solved(self):
        if not self.user.is_authenticated:
            return False
        return self.user.submissions.filter(question=self, is_correct=True).exists()

    @property
    def is_partially_correct(self):
        if not self.user.is_authenticated:
            return False
        return self.user.submissions.filter(question=self, is_partially_correct=True).exists() and not self.is_solved

    @property
    def no_submission(self):
        if not self.user.is_authenticated:
            return True
        return not self.user.submissions.filter(question=self).exists()

    @property
    def is_wrong(self):
        return not self.is_solved and not self.is_partially_correct and not self.no_submission

    def get_rendered_text(self):
        return self.text


class VariableQuestion(Question):
    variables = JSONField()

    def get_variables(self):
        random.seed(self.user.pk or 0)
        variables = {}

        if type(self.variables) != list:
            return variables

        for attrs in self.variables:
            vtype = attrs.get('type', None)
            vmin = eval(render_text(attrs.get('min', 0), variables))
            vmax = eval(render_text(attrs.get('max', 1), variables))
            precision = eval(render_text(attrs.get('precision'), variables))
            exp = render_text(attrs.get('expression', ''), variables)
            values = [render_text(x, variables) for x in attrs.get('values', [])]

            if vtype == 'int':
                variables[attrs['name']] = random.randrange(int(vmin), int(vmax) + 1)
            if vtype == 'float':
                value = random.uniform(vmin, vmax + 1)
                precision = 10**precision
                value = math.floor(value*precision)/precision
                variables[attrs['name']] = value
            if vtype == 'enum':
                p = random.randrange(0, len(values))
                variables[attrs['name']] = values[p]
            if vtype == 'expression':
                variables[attrs['name']] = eval(exp)

        return variables

    def get_rendered_text(self):
        return render_text(self.text, self.get_variables())


class MultipleChoiceQuestion(VariableQuestion):
    choices = JSONField()
    visible_distractor_count = models.IntegerField()

    grader = MultipleChoiceGrader()

    def get_rendered_choices(self):
        choices = json.loads(self.choices) if type(self.choices) == str else self.choices

        res = {}
        for key, val in choices.items():
            res[key] = render_text(val, self.get_variables())
        return res


class CheckboxQuestion(MultipleChoiceQuestion):
    pass


class JavaQuestion(Question):
    test_cases = JSONField()

    grader = JavaGrader()

    def is_allowed_to_submit(self):
        if not self.user.is_authenticated:
            return False
        return len(list(filter(lambda s: not s.is_compile_error,
                               list(self.user.submissions.filter(question=self))))) < self.max_submission_allowed


class Submission(PolymorphicModel):
    user = models.ForeignKey(MyUser, on_delete=models.CASCADE, related_name='submissions')
    submission_time = models.DateTimeField(auto_now_add=True)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='submissions')

    code = models.TextField(null=True, blank=True)
    answer = models.TextField(null=True, blank=True)

    grade = models.FloatField(default=0)
    is_correct = models.BooleanField(default=False)
    is_partially_correct = models.BooleanField(default=False)
    finalized = models.BooleanField(default=False)

    show_answer = True
    show_detail = False

    def get_description(self):
        return "{}Solved Question <a href='{}'>{}</a>".format("Partially " if self.is_partially_correct else "",
                                                              reverse_lazy('course:question_view',
                                                                           kwargs={'pk': self.question.pk}),
                                                              self.question.title)

    @property
    def status_color(self):
        dic = {
            "Evaluating": 'info',
            "Wrong": 'danger',
            "Partially Correct": 'warning',
            "Correct": 'success',
        }

        return dic[self.status]

    @property
    def in_progress(self):
        return False

    @property
    def status(self):
        if self.in_progress:
            return "Evaluating"
        if self.is_correct:
            return "Correct"
        if self.is_partially_correct:
            return "Partially Correct"

        return "Wrong"

    def calculate_grade(self, commit=True):
        if self.finalized:
            return

        self.is_correct, self.grade = self.question.grader.grade(self)

        if not self.is_correct and self.grade > 0:
            self.is_partially_correct = True

        if not self.in_progress:
            self.finalized = True

        if commit:
            self.save()

    @property
    def get_grade(self):
        if self.in_progress:
            self.calculate_grade()
        return self.grade

    def save(self, *args, **kwargs):

        if not self.finalized:
            self.calculate_grade(commit=False)

        if not self.in_progress and self.is_correct or self.is_partially_correct:
            user_question_junction = get_user_question_junction(self.user, self.question)
            received_tokens = self.grade * get_token_value(self.question.category, self.question.difficulty)
            token_change = received_tokens - user_question_junction.tokens_received

            if token_change > 0:
                user_question_junction.tokens_received = received_tokens
                user_question_junction.save()

            Action.create_action(self.user, self.get_description(), received_tokens, Action.COMPLETE)

        super().save(*args, **kwargs)


class MultipleChoiceSubmission(Submission):
    @property
    def answer_display(self):
        return self.question.get_rendered_choices().get(self.answer, 'Unknown')


class CodeSubmission(Submission):
    tokens = JSONField()
    results = JSONField()

    show_answer = False
    show_detail = True

    @property
    def is_compile_error(self):
        for result in self.results:
            if result['status']['id'] != 6:
                return False
        return True

    @property
    def status(self):
        if self.in_progress:
            self.calculate_grade()
        return super().status

    @property
    def in_progress(self):
        for result in self.results:
            if result['status']['id'] == 1 or result['status']['id'] == 2:
                return True
        return False

    def submit(self):
        self.question.grader.submit(self)


class JavaSubmission(CodeSubmission):
    pass


class UserQuestionJunction(models.Model):
    user = models.ForeignKey(MyUser, on_delete=models.CASCADE, related_name='question_junctions')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='user_junctions')

    opened_tutorial = models.BooleanField(default=False)
    opened_question = models.BooleanField(default=False)
    tokens_received = models.FloatField(default=0)
