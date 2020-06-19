import json
import random
import requests
import jsonfield

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.urls import reverse_lazy
from djrichtextfield.models import RichTextField
from polymorphic.models import PolymorphicModel

from course.grader import MultipleChoiceGrader
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
    ("NORMAL", "NORMAL"),
    ("HARD", "HARD"),
]


def render_text(text, variables):
    text = str(text)
    for variable, value in variables.items():
        text = text.replace("{{"+variable+"}}", str(value))
    return text


class TokenValue(models.Model):
    value = models.FloatField(default=0)
    category = models.ForeignKey(QuestionCategory, on_delete=models.CASCADE, related_name='token_values')
    difficulty = models.CharField(max_length=100, choices=DIFFICULTY_CHOICES, default="EASY")

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
    author = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True)
    category = models.ForeignKey(QuestionCategory, on_delete=models.SET_NULL, null=True, blank=True)
    difficulty = models.CharField(max_length=100, choices=DIFFICULTY_CHOICES)

    is_verified = models.BooleanField(default=False)

    def is_allowed_to_submit(self, user):
        if not user.is_authenticated:
            return False
        return user.submissions.filter(question=self).count() < self.max_submission_allowed

    def is_solved_by_user(self, user):
        if not user.is_authenticated:
            return False
        return user.submissions.filter(question=self, is_correct=True).exists()

    def is_partially_correct_by_user(self, user):
        if not user.is_authenticated:
            return False
        return user.submissions.filter(question=self, is_partially_correct=True).exists() and not self.is_solved_by_user(user)

    def has_no_submission_by_user(self, user):
        if not user.is_authenticated:
            return True
        return not user.submissions.filter(question=self).exists()


class VariableQuestion(Question):
    variables = jsonfield.JSONField()

    def get_variables(self, user):
        random.seed(user.pk or 0)
        variables = json.loads(self.variables) if type(self.variables) == str else self.variables
        size = len(variables)
        p = random.randrange(0, size)
        return variables[p]

    def get_rendered_text(self, user):
        return render_text(self.text, self.get_variables(user))


class MultipleChoiceQuestion(VariableQuestion):
    choices = jsonfield.JSONField()
    visible_distractor_count = models.IntegerField()

    def get_rendered_choices(self, user):
        choices = json.loads(self.choices) if type(self.choices) == str else self.choices

        res = {}
        for key, val in choices.items():
            res[key] = render_text(val, self.get_variables(user))
        return res

    def get_grader(self, user):
        return MultipleChoiceGrader(self, user)


class CheckboxQuestion(MultipleChoiceQuestion):
    pass


class JavaQuestion(Question):
    test_cases = jsonfield.JSONField()

    def is_allowed_to_submit(self, user):
        if not user.is_authenticated:
            return False
        return len(list(filter(lambda s : not s.is_compile_error, list(user.submissions.filter(question=self))))) < self.max_submission_allowed


class Submission(PolymorphicModel):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='submissions')
    submission_time = models.DateTimeField(auto_now_add=True)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='submissions')

    code = models.TextField(null=True, blank=True)
    answer = models.TextField(null=True, blank=True)

    grade = models.FloatField(default=0)
    is_correct = models.BooleanField(default=False)
    is_partially_correct = models.BooleanField(default=False)

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
    def status(self):
        raise NotImplementedError()


class MultipleChoiceSubmission(Submission):
    @property
    def answer_display(self):
        if isinstance(self.question, CheckboxQuestion):
            return self.answer
        if isinstance(self.question, MultipleChoiceQuestion):
            return self.question.get_rendered_choices(self.user).get(self.answer, 'Unknown')
        return self.answer

    @property
    def status(self):
        if self.is_correct:
            return "Correct"
        return "Wrong"

    def calculate_grade(self):
        return self.question.get_grader(self.user).grade(self)

    def save(self, *args, **kwargs):
        self.is_correct, self.grade = self.calculate_grade()

        if self.is_correct:
            user_question_junction = get_user_question_junction(self.user, self.question)

            received_tokens = self.grade * get_token_value(self.question.category, self.question.difficulty)
            user_question_junction.tokens_received = received_tokens
            user_question_junction.save()
            self.user.save()

            Action.create_action(self.user, "Solved Question <a href='{}'>{}</a>".format(reverse_lazy('course:question_view', kwargs={'pk':self.question.pk}), self.question.title), received_tokens, Action.COMPLETE)

        super().save(*args, **kwargs)


class JavaSubmission(Submission):
    tokens = jsonfield.JSONField()
    results = jsonfield.JSONField()

    @property
    def is_compile_error(self):
        for result in self.results:
            if result['status']['id'] != 6:
                return False
        return True

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
    def status(self):
        if self.in_progress:
            self.evaluate()
        if self.in_progress:
            return "Evaluating"

        if self.is_correct:
            return "Correct"
        if self.is_partially_correct:
            return "Partially Correct"

        return "Wrong"

    def get_grade(self, evaluate=True):
        if self.in_progress and evaluate:
            self.evaluate()
        if self.in_progress:
            return 0

        total_test_cases = len(self.question.test_cases)
        correct_test_cases = 0

        for i, result in enumerate(self.results):
            if result['status']['id'] == 3:
                correct_test_cases += 1

        return correct_test_cases / total_test_cases

    @property
    def in_progress(self):
        for result in self.results:
            if result['status']['id'] == 1 or result['status']['id'] == 2:
                return True
        return False

    def evaluate(self):
        self.results = []

        for i, test_case in enumerate(self.question.test_cases):
            token = self.tokens[i]
            r = requests.get("https://api.judge0.com/submissions/{}?base64_encoded=false".format(token))
            self.results.append(r.json())

        self.grade = self.get_grade(False)
        if self.grade == 1:
            self.is_correct = True
            self.is_partially_correct = False
        if 0 < self.grade < 1:
            self.is_correct = False
            self.is_partially_correct = True
        self.save()

        if not self.in_progress:
            self.finalize_evaluation()

    def finalize_evaluation(self):
        user_question_junction = get_user_question_junction(self.user, self.question)
        received_tokens = self.grade * get_token_value(self.question.category, self.question.difficulty)
        token_change = received_tokens - user_question_junction.tokens_received
        if token_change > 0:
            user_question_junction.tokens_received = received_tokens
            user_question_junction.save()

            Action.create_action(self.user, self.get_description(), token_change, Action.COMPLETE)

    def get_description(self):
        return "{}Solved Question <a href='{}'>{}</a>".format("Partially " if self.is_partially_correct else "", reverse_lazy('course:question_view', kwargs={'pk':self.question.pk}), self.question.title)

    def submit(self):
        self.tokens = []

        for test_case in self.question.test_cases:

            r = requests.post("https://api.judge0.com/submissions/", data={
                "base64_encoded": False,
                "wait": False,
                "source_code": self.code,
                "language_id": 62,
                "stdin": test_case['input'],
                "expected_output": test_case['output'],
            })
            self.tokens.append(r.json()['token'])
        self.save()
        self.evaluate()


class UserQuestionJunction(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='question_junctions')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='user_junctions')

    opened_tutorial = models.BooleanField(default=False)
    opened_question = models.BooleanField(default=False)
    tokens_received = models.FloatField(default=0)
