import copy

import canvasapi
from django.db import models
from django.db.models import Sum, F, FloatField
from django.shortcuts import get_object_or_404
from django.utils import timezone
from fuzzywuzzy import process

from accounts.models import MyUser
from canvas import canvasapi_mock
from canvas.utils.token_use import get_token_use
from canvas.utils.utils import get_course_registration


class CanvasCourse(models.Model):
    mock = models.BooleanField(default=False)
    name = models.CharField(max_length=500)
    url = models.URLField()
    course_id = models.IntegerField()
    token = models.CharField(max_length=500)
    instructor = models.ForeignKey(MyUser, on_delete=models.SET_NULL, null=True, blank=True)

    allow_registration = models.BooleanField(default=False)
    visible_to_students = models.BooleanField(default=False)
    start_date = models.DateTimeField(null=True)
    end_date = models.DateTimeField(null=True)

    verification_assignment_group_name = models.CharField(max_length=100)
    verification_assignment_group_id = models.IntegerField(null=True, blank=True)
    verification_assignment_name = models.CharField(max_length=100)
    verification_assignment_id = models.IntegerField(null=True, blank=True)

    bonus_assignment_group_name = models.CharField(max_length=100)
    bonus_assignment_group_id = models.IntegerField(null=True, blank=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._canvas = None
        self._course = None
        self._verification_assignment = None

    @property
    def canvas(self):
        if self.mock:
            return canvasapi_mock.Canvas(self.url, self.token)
        if not self._canvas:
            self._canvas = canvasapi.Canvas(self.url, self.token)
        return self._canvas

    @property
    def course(self):
        if not self._course:
            self._course = self.canvas.get_course(self.course_id)
        return self._course

    @property
    def canvas_course_name(self):
        return self.course.attributes.get('name', 'Unknown')

    @property
    def status(self):
        if not self.allow_registration:
            return "Blocked"
        if timezone.now() < self.start_date:
            return "Pending"
        if self.end_date < timezone.now():
            return "Finished"
        return "In Session"

    @property
    def verification_assignment(self):
        if not self._verification_assignment:
            self._verification_assignment = self.course.get_assignment(self.verification_assignment_id)
        return self._verification_assignment

    @property
    def leader_board(self):
        return [
            {
                "name": course_reg.user.get_full_name(),
                "token": course_reg.total_tokens_received,
            } for course_reg in self.canvascourseregistration_set.all()
        ]

    def create_verification_assignment_group(self):
        if self.verification_assignment_group_id:
            return
        ag = self.course.create_assignment_group(name=self.verification_assignment_group_name)
        self.verification_assignment_group_id = ag.id

    def create_bonus_assignment_group(self):
        if self.bonus_assignment_group_id:
            return
        ag = self.course.create_assignment_group(name=self.bonus_assignment_group_name)
        self.bonus_assignment_group_id = ag.id

    def create_verification_assignment(self):
        if self.verification_assignment_id:
            return

        a = self.course.create_assignment({
            'points_possible': 100,
            'name': self.verification_assignment_name,
            'assignment_group_id': self.verification_assignment_group_id,
            'published': True
        })
        self.verification_assignment_id = a.id

    def get_user(self, name=None, id=None, student_id=None):
        for user in self.course.get_users():
            if user.id == id or user.name == name or user.sis_user_id == student_id:
                return user
        return None

    def guess_user(self, name):
        choices = [x.name for x in self.course.get_users()]
        student_names = process.extractBests(name, choices, score_cutoff=95)
        return [x[0] for x in student_names]

    def is_registered(self, user):
        if user.is_anonymous:
            return False
        return self.canvascourseregistration_set.filter(user=user, status='VERIFIED').exists()

    def is_instructor(self, user):
        return self.instructor == user

    def has_view_permission(self, user):
        return user.is_teacher or self.is_instructor(user) or self.is_registered(user)

    def has_edit_permission(self, user):
        course_reg = get_course_registration(user, self)
        return course_reg.registration_type == INSTRUCTOR

    def has_create_event_permission(self, user):
        course_reg = get_course_registration(user, self)
        return course_reg.registration_type == TA or course_reg.registration_type == INSTRUCTOR

    def save(self, *args, **kwargs):
        self.create_verification_assignment_group()
        self.create_verification_assignment()
        self.create_bonus_assignment_group()
        super().save(*args, **kwargs)


def random_verification_code():
    import random
    return random.randint(1, 100)


STATUS = [
    ("UNREGISTERED", "UNREGISTERED"),
    ("PENDING_VERIFICATION", "PENDING_VERIFICATION"),
    ("VERIFIED", "VERIFIED"),
    ("BLOCKED", "BLOCKED")
]

STUDENT = "STUDENT"
TA = "TA"
INSTRUCTOR = "INSTRUCTOR"

REGISTRATION_TYPE = [
    (STUDENT, STUDENT),
    (TA, TA),
    (INSTRUCTOR, INSTRUCTOR)
]


class CanvasCourseRegistration(models.Model):
    course = models.ForeignKey(CanvasCourse, on_delete=models.CASCADE, db_index=True)
    user = models.ForeignKey(MyUser, on_delete=models.CASCADE, db_index=True)
    canvas_user_id = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=100, choices=STATUS, default="UNREGISTERED")
    verification_code = models.IntegerField(default=random_verification_code)
    verification_attempts = models.IntegerField(default=3)

    registration_type = models.CharField(max_length=10, choices=REGISTRATION_TYPE, null=True, default=STUDENT)

    class Meta:
        unique_together = ('course', 'user')

    def get_token_uses(self):
        return [get_token_use(self.user, tup['id']) for tup in self.course.token_use_options.values('id')]

    @property
    def is_verified(self):
        return self.status == 'VERIFIED'

    @property
    def is_blocked(self):
        return self.status == 'BLOCKED'

    def verify(self):
        self.status = 'VERIFIED'
        self.save()

    def block(self):
        self.status = 'BLOCKED'
        self.save()

    def unregister(self):
        self.status = 'UNREGISTERED'
        self.save()

    def unverify(self):
        self.status = 'PENDING_VERIFICATION'
        self.save()

    @property
    def canvas_user(self):
        if self.canvas_user_id is None:
            return None
        if not self._canvas_user:
            self._canvas_user = self.course.course.get_user(self.canvas_user_id)
        return self._canvas_user

    def send_verification_code(self):
        self.course.verification_assignment.submissions_bulk_update(grade_data={
            self.canvas_user_id: {
                'posted_grade': self.verification_code,
            }
        })

    def set_canvas_user(self, canvas_user):
        self.canvas_user_id = canvas_user.id
        self.save()

    def check_verification_code(self, code):
        if self.is_blocked:
            return False
        if str(self.verification_code) == str(code):
            self.verify()
            return True
        self.verification_attempts -= 1
        if self.verification_attempts <= 0:
            self.block()

        return False

    @property
    def total_tokens_received(self):
        event_ids = [x['id'] for x in self.course.events.filter(count_for_tokens=True).values('id')]
        return self.user.question_junctions.filter(question__event_id__in=event_ids) \
                   .aggregate(Sum('tokens_received'))['tokens_received__sum'] or 0

    @property
    def available_tokens(self):
        tokens_used = self.user.token_uses.filter(option__course=self.course). \
            aggregate(available_tokens=Sum(F('option__tokens_required') * F('num_used'), output_field=FloatField()))[
            'available_tokens']

        if not tokens_used:
            tokens_used = 0

        return self.total_tokens_received - tokens_used

    @property
    def username(self):
        return self.user.username

    @property
    def name(self):
        return self.user.get_full_name()


EVENT_TYPE_CHOICES = [
    ("ASSIGNMENT", "ASSIGNMENT"),
    ("EXAM", "EXAM")
]


class Event(models.Model):
    name = models.CharField(max_length=500)
    type = models.CharField(max_length=500, choices=EVENT_TYPE_CHOICES)
    course = models.ForeignKey(CanvasCourse, related_name='events', on_delete=models.CASCADE)
    count_for_tokens = models.BooleanField()

    start_date = models.DateTimeField(null=True)
    end_date = models.DateTimeField(null=True)

    def __str__(self):
        return self.name

    @property
    def is_open(self):
        return self.start_date <= timezone.now() <= self.end_date

    def is_closed(self):
        return self.end_date < timezone.now()

    def is_not_available_yet(self):
        return self.start_date > timezone.now()

    @property
    def is_exam(self):
        return self.type == "EXAM"

    @property
    def status(self):
        if self.is_not_available_yet():
            return "Not available yet"
        if self.is_closed():
            return "Closed"
        return "Open"

    def has_view_permission(self, user):
        if self.course.is_instructor(user) or user.is_teacher:
            return True
        return self.is_open and self.course.is_registered(user)

    def has_edit_permission(self, user):
        course_reg = get_object_or_404(CanvasCourseRegistration, user=user, course=self.course)
        return course_reg.registration_type == TA or course_reg.registration_type == INSTRUCTOR

    def has_create_permission(self, user):
        course_reg = get_object_or_404(CanvasCourseRegistration, user=user, course=self.course)
        return course_reg.registration_type == TA or course_reg.registration_type == INSTRUCTOR

    def is_allowed_to_open(self, user):
        return self.course.is_registered(user) and self.is_open

    def can_view_results(self, user):
        return self.is_closed() and self.course.is_registered(user)

    def cannot_access_event_yet(self, user):
        return self.is_not_available_yet() and self.course.is_registered(user)

    def is_exam_and_open(self):
        return self.is_exam and self.is_open

    def copy_to_course(self, course):
        cloned_event = copy.deepcopy(self)
        cloned_event.id = None
        cloned_event.name += ' (Copy)'
        cloned_event.course = course
        cloned_event.save()

        for question in self.question_set.all():
            question.copy_to_event(cloned_event)

        return cloned_event


class TokenUseOption(models.Model):
    course = models.ForeignKey(CanvasCourse, related_name='token_use_options', on_delete=models.CASCADE)
    tokens_required = models.FloatField()
    points_given = models.IntegerField()
    maximum_number_of_use = models.IntegerField(default=1)

    assignment_name = models.CharField(max_length=100)
    assignment_id = models.IntegerField(null=True, blank=True)

    def create_assignment(self):
        if self.assignment_id:
            return

        a = self.course.course.create_assignment({
            'points_possible': 100,
            'name': self.assignment_name,
            'assignment_group_id': self.course.bonus_assignment_group_id,
            'published': True
        })
        self.assignment_id = a.id

    def save(self, *args, **kwargs):
        self.create_assignment()
        super().save(*args, **kwargs)


class TokenUse(models.Model):
    option = models.ForeignKey(TokenUseOption, on_delete=models.CASCADE, related_name='token_uses')
    user = models.ForeignKey(MyUser, on_delete=models.CASCADE, related_name='token_uses')
    num_used = models.IntegerField(default=0)

    def apply(self):
        course_reg = CanvasCourseRegistration.objects.get(user=self.user, course=self.option.course)
        self.option.course.course.submissions_bulk_update(grade_data={
            course_reg.canvas_user_id: {
                'posted_grade': self.option.points_given * self.num_used,
            }
        })

    def revert(self):
        course_reg = CanvasCourseRegistration.objects.get(user=self.user, course=self.option.course)
        self.option.course.course.submissions_bulk_update(grade_data={
            course_reg.canvas_user_id: {
                'posted_grade': 0,
            }
        })
