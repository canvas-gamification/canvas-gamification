import canvasapi
from django.db import models
from django.db.models import Sum
from django.utils import timezone
from fuzzywuzzy import process

from accounts.models import MyUser
from canvas import canvasapi_mock


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

    def get_user(self, name=None, id=None):
        for user in self.course.get_users():
            if user.id == id or user.name == name:
                return user
        return None

    def guess_user(self, name):
        choices = [x.name for x in self.course.get_users()]
        return process.extractOne(name, choices, score_cutoff=95)

    def is_registered(self, user):
        return self.canvascourseregistration_set.filter(user=user, is_verified=True, is_blocked=False).exists()

    def is_instructor(self, user):
        return user.is_staff or self.instructor == user

    def save(self, *args, **kwargs):
        self.create_verification_assignment_group()
        self.create_verification_assignment()
        self.create_bonus_assignment_group()
        super().save(*args, **kwargs)


def random_verification_code():
    import random
    return random.randint(1, 100)


class CanvasCourseRegistration(models.Model):
    course = models.ForeignKey(CanvasCourse, on_delete=models.CASCADE, db_index=True)
    user = models.ForeignKey(MyUser, on_delete=models.CASCADE, db_index=True)

    canvas_user_id = models.IntegerField(null=True, blank=True)
    is_verified = models.BooleanField(default=False, db_index=True)
    is_blocked = models.BooleanField(default=False, db_index=True)

    verification_code = models.IntegerField(default=random_verification_code)
    verification_attempts = models.IntegerField(default=3)

    class Meta:
        unique_together = ('course', 'user')

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

    def check_verification_code(self, code):
        if self.is_blocked:
            return False
        if str(self.verification_code) == str(code):
            self.is_verified = True
            self.save()
            return True
        self.verification_attempts -= 1
        if self.verification_attempts <= 0:
            self.is_blocked = True
        self.save()

        return False

    @property
    def available_tokens(self):
        event_ids = [x['id'] for x in self.course.events.filter(count_for_tokens=True).values('id')]
        tokens_gained = self.user.question_junctions.filter(question__event_id__in=event_ids). \
            aggregate(Sum('tokens_received'))['tokens_received__sum']
        tokens_used = self.user.token_uses.filter(option__course=self.course). \
            aggregate(Sum('option__tokens_required'))['option__tokens_required__sum']

        if not tokens_gained:
            tokens_gained = 0
        if not tokens_used:
            tokens_used = 0

        return tokens_gained - tokens_used


class Event(models.Model):
    name = models.CharField(max_length=500)
    course = models.ForeignKey(CanvasCourse, related_name='events', on_delete=models.CASCADE)
    count_for_tokens = models.BooleanField()

    start_date = models.DateTimeField(null=True)
    end_date = models.DateTimeField(null=True)

    def __str__(self):
        return self.name

    def is_allowed_to_open(self, user):
        if self.course.is_instructor(user):
            return True
        return self.start_date <= timezone.now() <= self.end_date and self.course.is_registered(user)


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

    def apply(self):
        course_reg = CanvasCourseRegistration.objects.get(user=self.user, course=self.option.course)
        self.option.course.course.submissions_bulk_update(grade_data={
            course_reg.canvas_user_id: {
                'posted_grade': self.option.points_given,
            }
        })

    def revert(self):
        course_reg = CanvasCourseRegistration.objects.get(user=self.user, course=self.option.course)
        self.option.course.course.submissions_bulk_update(grade_data={
            course_reg.canvas_user_id: {
                'posted_grade': 0,
            }
        })
