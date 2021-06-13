import base64
import json
import random
from datetime import datetime

from django.db import models
from django.utils.crypto import get_random_string
from djrichtextfield.models import RichTextField
from polymorphic.models import PolymorphicModel

from accounts.models import MyUser
from canvas.models import Event, CanvasCourse
from course.fields import JSONField
from course.grader.grader import MultipleChoiceGrader, JunitGrader
from course.utils.junit_xml import parse_junit_xml
from course.utils.utils import get_token_value, ensure_uqj, calculate_average_success
from course.utils.variables import render_text, generate_variables
from general.models import Action

DIFFICULTY_CHOICES = [
    ("EASY", "EASY"),
    ("NORMAL", "MEDIUM"),
    ("HARD", "HARD"),
]


class QuestionCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name="sub_categories")
    next_categories = models.ManyToManyField('self', related_name="prev_categories", symmetrical=False, blank=True)

    def __str__(self):
        if self.parent is None:
            return self.name
        else:
            return "{} :: {}".format(self.parent, self.name)

    @property
    def full_name(self):
        return self.__str__()

    @property
    def average_success_per_difficulty(self):
        res = []
        for difficulty, difficulty_name in DIFFICULTY_CHOICES:
            res.append({
                'difficulty': difficulty_name,
                'success_rate': calculate_average_success(UserQuestionJunction.objects.all(), self, difficulty)
            })
        return res

    @property
    def average_success(self):
        return calculate_average_success(UserQuestionJunction.objects.all(), self)

    @property
    def question_count(self):
        if self.parent is None:
            cnt = 0
            for cat in self.sub_categories.all():
                cnt += cat.question_set.count()
            return cnt
        return self.question_set.count()

    @property
    def next_category_ids(self):
        return self.next_categories.values_list('pk', flat=True)


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


QUESTION_TYPES = {'mc': 'multiple choice question', 'parsons': 'parsons question', 'java': 'java question'}


class Question(PolymorphicModel):
    title = models.CharField(max_length=300, null=True, blank=True)
    text = RichTextField(null=True, blank=True)
    answer = models.TextField(null=True, blank=True)
    max_submission_allowed = models.IntegerField(default=None, blank=True)
    tutorial = RichTextField(null=True, blank=True)
    time_created = models.DateTimeField(auto_now_add=True)
    time_modified = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(MyUser, on_delete=models.SET_NULL, null=True, blank=True)
    category = models.ForeignKey(QuestionCategory, on_delete=models.SET_NULL, null=True, blank=True)
    difficulty = models.CharField(max_length=100, choices=DIFFICULTY_CHOICES, default="EASY")
    is_sample = models.BooleanField(default=False)

    course = models.ForeignKey(CanvasCourse, on_delete=models.SET_NULL, related_name='question_set', null=True,
                               blank=True, db_index=True)
    event = models.ForeignKey(Event, on_delete=models.SET_NULL, related_name='question_set', null=True, blank=True,
                              db_index=True)

    is_verified = models.BooleanField(default=False)

    grader = None

    @property
    def author_name(self):
        return self.author.username if self.author else ""

    @property
    def full_category_name(self):
        return self.category.full_name

    @property
    def category_name(self):
        return self.category.name if self.category else ""

    @property
    def parent_category_name(self):
        return self.category.parent.name if self.category and self.category.parent else ""

    @property
    def course_name(self):
        return self.course.name if self.course else ""

    @property
    def event_name(self):
        return self.event.name if self.event else ""

    @property
    def type_name(self):
        return self._meta.verbose_name

    @property
    def is_multiple_choice(self):
        return self.type_name == QUESTION_TYPES['mc']

    def __str__(self):
        return "{} ({})".format(self.type_name, self.id)

    @property
    def token_value(self):
        return get_token_value(self.category, self.difficulty)

    @property
    def success_rate(self):
        return calculate_average_success(self.user_junctions.all())

    @property
    def is_open(self):
        return self.event is not None and self.event.is_open

    @property
    def is_exam(self):
        return self.event is not None and self.event.is_exam

    @property
    def is_exam_and_open(self):
        return self.event is not None and self.event.is_exam_and_open()

    def save(self, *args, **kwargs):
        if self.max_submission_allowed is None:
            self.max_submission_allowed = 10 if self.event is not None and self.event.type == "EXAM" else 100

        super().save(*args, **kwargs)
        ensure_uqj(None, self)

    def has_view_permission(self, user):
        if user.is_teacher:
            return True
        if not self.event:
            return False
        return self.event.has_view_permission(user)

    def has_edit_permission(self, user):
        return user.is_teacher


class VariableQuestion(Question):
    variables = JSONField()


class MultipleChoiceQuestion(VariableQuestion):
    choices = JSONField()
    visible_distractor_count = models.IntegerField()
    grader = MultipleChoiceGrader()

    @property
    def is_checkbox(self):
        return ',' in self.answer


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


def random_seed():
    seed = get_random_string(8, '0123456789')
    return int(seed)


class UserQuestionJunction(models.Model):
    user = models.ForeignKey(MyUser, on_delete=models.CASCADE, related_name='question_junctions', db_index=True)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='user_junctions', db_index=True)
    random_seed = models.IntegerField(default=random_seed)

    last_viewed = models.DateTimeField(default=None, null=True, db_index=True)
    opened_tutorial = models.BooleanField(default=False)
    tokens_received = models.FloatField(default=0)

    is_solved = models.BooleanField(default=False, db_index=True)
    is_partially_solved = models.BooleanField(default=False, db_index=True)

    class Meta:
        unique_together = ('user', 'question')

    def viewed(self):
        self.last_viewed = datetime.now()
        self.save()

    @property
    def is_allowed_to_submit(self):
        if self.user.is_teacher:
            return True
        if self.opened_tutorial:
            return False
        if self.is_solved:
            return False

        return self.submissions.count() < self.question.max_submission_allowed and self.question.is_open

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
        keys = keys[:self.question.visible_distractor_count + len(self.question.answer.split(','))]
        random.seed(self.random_seed)
        random.shuffle(keys)

        return {key: render_text(choices[key], self.get_variables()) for key in keys}

    def get_lines(self):
        from course.models.parsons_question import ParsonsQuestion

        if not isinstance(self.question, ParsonsQuestion):
            return []

        random.seed(self.random_seed)
        lines = []
        for line in self.question.lines:
            lines.append(render_text(line, self.get_variables()))
        random.shuffle(lines)
        return lines

    def get_input_files(self):
        if not isinstance(self.question, JavaQuestion):
            return {}
        return self.question.get_input_files()

    def is_checkbox(self):
        if not isinstance(self.question, MultipleChoiceQuestion):
            return False
        return self.question.is_checkbox

    def num_attempts(self):
        return self.submissions.count()

    def formatted_num_attempts(self):
        return "Used " + str(self.num_attempts()) + " out of " + str(self.question.max_submission_allowed)

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
        if self.last_viewed:
            return "Unsolved"
        return "New"

    @property
    def formatted_current_tokens_received(self):
        if self.question.is_exam_and_open:
            return str(self.question.token_value)
        return str(self.tokens_received) + "/" + str(self.question.token_value)

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
        # TODO: Fix this when refactoring user actions
        template = "{}Solved Question <a href='{}'>{}</a>"
        # url = reverse_lazy('course:question_view', kwargs={'pk': self.question.pk})
        url = "#"
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

    @property
    def tokens_received(self):
        return self.grade * self.token_value

    @property
    def token_value(self):
        return get_token_value(self.question.category, self.question.difficulty)

    @property
    def formatted_tokens_received(self):
        return str(self.tokens_received) + "/" + str(self.token_value)

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

        if not self.in_progress and (self.is_correct or self.is_partially_correct or self.question.is_exam):
            user_question_junction = self.uqj
            received_tokens = self.grade * self.token_value
            token_change = received_tokens - user_question_junction.tokens_received

            if self.question.is_exam or token_change > 0:
                user_question_junction.tokens_received = received_tokens
                user_question_junction.save()

            Action.create_action(self.user, self.get_description(), received_tokens, Action.COMPLETE)

        super().save(*args, **kwargs)

    def submit(self):
        pass


class MultipleChoiceSubmission(Submission):
    @property
    def answer_display(self):
        values = []
        rendered_choices = self.uqj.get_rendered_choices()
        for answer in self.answer.split(','):
            values.append(rendered_choices.get(answer, 'Unknown'))
        return values


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

    def get_decoded_stderr(self):
        return base64.b64decode(self.results[0]['stderr'] or "").decode('utf-8')

    def get_decoded_results(self):
        stdout = base64.b64decode(self.results[0]['stdout'] or "").decode('utf-8')
        return parse_junit_xml(stdout)

    def get_formatted_test_results(self):
        return str(len(self.get_passed_test_results())) + "/" + str(self.get_num_tests())

    def get_passed_test_results(self):
        all_tests = self.get_decoded_results()
        return list(filter(lambda test: test["status"] == "PASS", all_tests))

    def get_failed_test_results(self):
        all_tests = self.get_decoded_results()
        return list(filter(lambda test: test["status"] == "FAIL", all_tests))

    def get_num_tests(self):
        return len(self.get_decoded_results())

    def get_answer_files(self):
        raise NotImplementedError()

    def no_file_answer(self):
        return False


class JavaSubmission(CodeSubmission):
    answer_files = JSONField()

    def get_answer_files(self):
        return self.answer_files
