import json
import random
import math

from django.contrib.auth.models import AnonymousUser
from django.db import models
from django.db.models import Count
from django.urls import reverse_lazy
from django.utils.crypto import get_random_string
from djrichtextfield.models import RichTextField
from polymorphic.models import PolymorphicModel

from accounts.models import MyUser
from course.fields import JSONField
from course.grader import MultipleChoiceGrader, JavaGrader
from course.utils.utils import get_user_question_junction, get_token_value
from course.utils.variables import render_text, generate_variables
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

    grader = None

    @property
    def type_name(self):
        return self._meta.verbose_name

    @property
    def token_value(self):
        return get_token_value(self.category, self.difficulty)

    @property
    def success_rate(self):
        total_tried = self.user_junctions.annotate(Count('submissions')).filter(submissions__count__gt=0).count()
        total_solved = self.user_junctions.filter(is_solved=True).count()
        if total_tried == 0:
            return 0
        return total_solved/total_tried


class VariableQuestion(Question):
    variables = JSONField()


class MultipleChoiceQuestion(VariableQuestion):
    choices = JSONField()
    visible_distractor_count = models.IntegerField()

    grader = MultipleChoiceGrader()


class CheckboxQuestion(MultipleChoiceQuestion):
    pass


class JavaQuestion(VariableQuestion):
    test_cases = JSONField()

    grader = JavaGrader()


def random_seed():
    seed = get_random_string(8, '0123456789')
    return int(seed)


class UserQuestionJunction(models.Model):
    user = models.ForeignKey(MyUser, on_delete=models.CASCADE, related_name='question_junctions')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='user_junctions')
    random_seed = models.IntegerField(default=random_seed)

    opened_tutorial = models.BooleanField(default=False)
    opened_question = models.BooleanField(default=False)
    tokens_received = models.FloatField(default=0)

    is_solved = models.BooleanField(default=False)
    is_partially_solved = models.BooleanField(default=False)


    @property
    def is_allowed_to_submit(self):
        if self.user.is_teacher():
            return True
        if self.opened_tutorial:
            return False
        if self.is_solved:
            return False

        return self.submissions.count() < self.question.max_submission_allowed

    def _get_variables(self):
        if not isinstance(self.question, VariableQuestion):
            return {}, []

        variables, errors = generate_variables(self.question.variables, self.random_seed)

        return variables, errors

    def get_variables_errors(self):
        return self._get_variables()[1]

    def get_variables(self):
        return self._get_variables()[0]

    def get_rendered_text(self):
        return render_text(self.question.text, self.get_variables())

    def get_rendered_choices(self):
        if not isinstance(self.question, MultipleChoiceQuestion):
            return {}

        choices = json.loads(self.question.choices) if type(self.question.choices) == str else self.question.choices

        keys = list(choices.keys())
        keys = keys[:self.question.visible_distractor_count+1]

        random.seed(self.random_seed)
        random.shuffle(keys)

        return {key: render_text(choices[key], self.get_variables()) for key in keys}

    def get_lines(self):
        from course.models.parsons_question import ParsonsQuestion

        if not isinstance(self.question, ParsonsQuestion):
            return {}

        random.seed(self.random_seed)
        lines = []
        for line in self.question.lines:
            lines.append(render_text(line, self.get_variables()))
        random.shuffle(lines)
        return lines

    def num_attempts(self):
        return self.submissions.count()

    @property
    def status_class(self):
        if self.is_solved:
            return "table-success"
        if self.is_partially_solved:
            return "table-warning"
        if self.submissions.exists():
            return "table-danger"
        return ""

    @property
    def status(self):
        if self.is_solved:
            return "Solved"
        if self.is_partially_solved:
            return "Partially Solved"
        if self.submissions.exists():
            return "Wrong"
        if self.opened_question:
            return "Unsolved"
        return "New"

    def save(self, **kwargs):
        self.is_solved = self.submissions.filter(is_correct=True).exists()
        self.is_partially_solved = not self.is_solved and self.submissions.filter(is_partially_correct=True).exists()
        super().save(**kwargs)


class Submission(PolymorphicModel):
    uqj = models.ForeignKey(UserQuestionJunction, on_delete=models.CASCADE, related_name='submissions')
    submission_time = models.DateTimeField(auto_now_add=True)

    answer = models.TextField(null=True, blank=True)

    grade = models.FloatField(default=0)
    is_correct = models.BooleanField(default=False)
    is_partially_correct = models.BooleanField(default=False)
    finalized = models.BooleanField(default=False)

    show_answer = True
    show_detail = False

    @property
    def question(self):
        return self.uqj.question

    @property
    def user(self):
        return self.uqj.user

    def get_description(self):
        template = "{}Solved Question <a href='{}'>{}</a>"
        url = reverse_lazy('course:question_view', kwargs={'pk': self.question.pk})
        title = self.uqj.question.title

        return template.format("Partially " if self.is_partially_correct else "", url, title)

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

        self.is_correct, self.grade = self.uqj.question.grader.grade(self)

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
            user_question_junction = self.uqj
            received_tokens = self.grade * get_token_value(self.question.category, self.question.difficulty)
            token_change = received_tokens - user_question_junction.tokens_received

            if token_change > 0:
                user_question_junction.tokens_received = received_tokens
                user_question_junction.save()

            Action.create_action(self.user, self.get_description(), received_tokens, Action.COMPLETE)

        super().save(*args, **kwargs)

    def submit(self):
        pass


class MultipleChoiceSubmission(Submission):
    @property
    def answer_display(self):
        return self.uqj.get_rendered_choices().get(self.answer, 'Unknown')


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

