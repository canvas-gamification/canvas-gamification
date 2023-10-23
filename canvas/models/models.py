import copy

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Sum, F, FloatField, Max
from django.utils import timezone

from accounts.models import MyUser
from canvas.utils.token_use import get_token_use
from canvas.utils.utils import get_course_registration, get_total_event_tokens

REGISTRATION_MODES = [("OPEN", "OPEN"), ("CODE", "CODE")]


class CanvasCourse(models.Model):
    name = models.CharField(max_length=500)
    url = models.URLField(null=True, blank=True)
    instructor = models.ForeignKey(MyUser, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.CharField(max_length=500, null=True, blank=True)

    registration_mode = models.CharField(max_length=100, choices=REGISTRATION_MODES, default="OPEN")
    registration_code = models.CharField(max_length=100, null=True, blank=True)
    allow_registration = models.BooleanField(default=False)
    visible_to_students = models.BooleanField(default=False)
    start_date = models.DateTimeField(null=True)
    end_date = models.DateTimeField(null=True)

    @property
    def verified_course_registration(self):
        return self.canvascourseregistration_set.filter(status="VERIFIED").all()

    @property
    def status(self):
        if not self.allow_registration:
            return "Blocked"
        if timezone.now() < self.start_date:
            return "Pending"
        if self.end_date < timezone.now():
            return "Finished"
        return "In Session"

    def is_registered(self, user):
        if user.is_anonymous:
            return False
        return get_course_registration(user, self).status == "VERIFIED"

    def is_instructor(self, user):
        return self.instructor == user

    def has_view_permission(self, user):
        return user.is_teacher or self.is_instructor(user) or (self.is_registered(user) and self.status == "In Session")

    def has_edit_permission(self, user):
        course_reg = get_course_registration(user, self)
        return user.is_teacher or course_reg.registration_type == INSTRUCTOR

    def has_create_event_permission(self, user):
        course_reg = get_course_registration(user, self)
        return user.is_teacher or course_reg.registration_type == TA or course_reg.registration_type == INSTRUCTOR

    def has_create_challenge_permission(self, user):
        return user.is_teacher or self.is_instructor(user) or self.is_registered(user)


def random_verification_code():
    import random

    return random.randint(1, 99)


STATUS = [
    ("UNREGISTERED", "UNREGISTERED"),
    ("PENDING_VERIFICATION", "PENDING_VERIFICATION"),
    ("VERIFIED", "VERIFIED"),
    ("BLOCKED", "BLOCKED"),
]

STUDENT = "STUDENT"
TA = "TA"
INSTRUCTOR = "INSTRUCTOR"

REGISTRATION_TYPE = [(STUDENT, STUDENT), (TA, TA), (INSTRUCTOR, INSTRUCTOR)]


class CanvasCourseRegistration(models.Model):
    course = models.ForeignKey(CanvasCourse, on_delete=models.CASCADE, db_index=True)
    user = models.ForeignKey(MyUser, on_delete=models.CASCADE, db_index=True)
    canvas_user_id = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=100, choices=STATUS, default="UNREGISTERED")
    verification_code = models.IntegerField(default=random_verification_code)
    verification_attempts = models.IntegerField(default=3)

    registration_type = models.CharField(max_length=10, choices=REGISTRATION_TYPE, null=True, default=STUDENT)

    class Meta:
        unique_together = ("course", "user")

    def __str__(self):
        return f"{self.user.username} - {self.course.name}"

    def get_token_uses(self):
        return [get_token_use(self.user, tup["id"]) for tup in self.course.token_use_options.values("id")]

    @property
    def is_verified(self):
        return self.status == "VERIFIED"

    @property
    def is_blocked(self):
        return self.status == "BLOCKED"

    def verify(self):
        self.status = "VERIFIED"

    def block(self):
        self.status = "BLOCKED"

    def unregister(self):
        self.status = "UNREGISTERED"

    def unverify(self):
        self.status = "PENDING_VERIFICATION"

    def set_instructor(self):
        self.registration_type = INSTRUCTOR

    @property
    def total_tokens_received(self):
        events = self.course.events.filter(count_for_tokens=True, end_date__lt=timezone.now())
        tokens = 0

        for event in events:
            team = event.team_set.filter(course_registrations=self).first()
            if team is None:
                tokens += 0
            else:
                tokens += event.tokens_received(team)

        from course.models.models import Question

        practiced_uqjs = self.user.question_junctions.filter(
            user=self.user,
            question__course=None,
            question__event=None,
            question__is_verified=True,
            question__question_status=Question.CREATED,
        )
        for uqj in practiced_uqjs:
            tokens += uqj.tokens_received

        event_sets = EventSet.objects.filter(course=self.course).all()
        for event_set in event_sets:
            if all(event.has_solved_event(self.user) for event in event_set.events.all()):
                tokens += event_set.tokens

        return tokens

    @property
    def available_tokens(self):
        tokens_used = self.user.token_uses.filter(option__course=self.course).aggregate(
            available_tokens=Sum(
                F("option__tokens_required") * F("num_used"),
                output_field=FloatField(),
            )
        )["available_tokens"]

        if not tokens_used:
            tokens_used = 0

        return self.total_tokens_received - tokens_used

    @property
    def username(self):
        return self.user.username

    @property
    def name(self):
        return self.user.nickname

    @property
    def full_name(self):
        if self.user.has_name:
            return self.user.get_full_name()
        return "Anonymous Student"


EVENT_TYPE_CHOICES = [
    ("ASSIGNMENT", "ASSIGNMENT"),
    ("EXAM", "EXAM"),
    ("CHALLENGE", "CHALLENGE"),
]

CHALLENGE_TYPE_CHOICES = [
    ("QUOTA", "QUOTA"),  # Receive token for each question solved
    ("TOP_TEAMS", "TOP_TEAMS"),  # Be in the top 'challenge_type_value' team to receive token
]


class Event(models.Model):
    name = models.CharField(max_length=500)
    type = models.CharField(max_length=500, choices=EVENT_TYPE_CHOICES)
    challenge_type = models.CharField(max_length=500, choices=CHALLENGE_TYPE_CHOICES, blank=True, null=True)
    challenge_type_value = models.FloatField(blank=True, null=True)
    course = models.ForeignKey(CanvasCourse, related_name="events", on_delete=models.CASCADE)
    author = models.ForeignKey(MyUser, on_delete=models.SET_NULL, null=True, blank=True)
    count_for_tokens = models.BooleanField()
    featured = models.BooleanField(default=False)
    max_team_size = models.IntegerField(default=3, validators=[MinValueValidator(1)])

    start_date = models.DateTimeField(null=True)
    end_date = models.DateTimeField(null=True)

    class Meta:
        unique_together = ("course", "name")

    def __str__(self):
        return self.name

    def calculate_tokens(self, team):
        from course.models.models import UserQuestionJunction

        user_ids = [course_reg.user.id for course_reg in team.course_registrations.all()]
        question_ids = [question.id for question in self.question_set.all()]
        uqjs = UserQuestionJunction.objects.filter(user_id__in=user_ids)

        score = 0
        for question_id in question_ids:
            score += uqjs.filter(question_id=question_id).aggregate(Max("tokens_received"))["tokens_received__max"]

        return score

    def tokens_received(self, team):
        tokens = self.calculate_tokens(team)
        if self.challenge_type == "TOP_TEAMS":
            count = 0
            for other_team in self.team_set.all():
                if self.calculate_tokens(other_team) > tokens:
                    count += 1
            if count >= self.challenge_type_value:
                return 0
        return tokens

    @property
    def total_tokens(self):
        return get_total_event_tokens(self)

    @property
    def is_open(self):
        return self.start_date <= timezone.now() <= self.end_date

    @property
    def is_closed(self):
        return self.end_date < timezone.now()

    @property
    def is_not_available_yet(self):
        return self.start_date > timezone.now()

    @property
    def is_exam(self):
        return self.type == "EXAM"

    @property
    def status(self):
        if self.is_not_available_yet:
            return "Not available yet"
        if self.is_closed:
            return "Closed"
        return "Open"

    def is_author(self, user):
        return self.author == user

    def has_solved_event(self, user):
        event_questions = self.question_set.all()

        from course.models.models import UserQuestionJunction

        uqjs = UserQuestionJunction.objects.filter(user_id=user.id, is_solved=True, question__in=event_questions)

        if uqjs.count() == event_questions.count():
            return True
        return False

    def has_view_permission(self, user):
        if self.course.is_instructor(user) or user.is_teacher or self.is_author(user):
            return True
        return self.is_open and self.course.is_registered(user)

    def has_edit_permission(self, user):
        course_reg = get_course_registration(user, self.course)
        return (
            user.is_teacher
            or course_reg.registration_type == TA
            or course_reg.registration_type == INSTRUCTOR
            or self.is_author(user)
        )

    def has_create_permission(self, user):
        course_reg = get_course_registration(user, self.course)
        return (
            user.is_teacher
            or course_reg.registration_type == TA
            or course_reg.registration_type == INSTRUCTOR
            or self.is_author(user)
        )

    def is_allowed_to_open(self, user):
        return self.course.is_registered(user) and self.is_open

    def can_view_results(self, user):
        return self.is_closed and self.course.is_registered(user)

    def cannot_access_event_yet(self, user):
        return self.is_not_available_yet and self.course.is_registered(user)

    def is_exam_and_open(self):
        return self.is_exam and self.is_open

    def copy_to_course(self, course):
        cloned_event = copy.deepcopy(self)
        cloned_event.id = None
        cloned_event.name += " (Copy)"
        cloned_event.course = course
        cloned_event.featured = False
        cloned_event.save()

        for question in self.question_set.all():
            question.copy_to_event(cloned_event)

        return cloned_event

    def update_featured(self):
        if self.is_closed:
            self.featured = False
            self.save()


class EventSet(models.Model):
    name = models.CharField(max_length=500)
    course = models.ForeignKey(CanvasCourse, related_name="event_sets", on_delete=models.CASCADE)
    events = models.ManyToManyField(Event, related_name="event_sets", blank=True)
    tokens = models.FloatField()

    def has_edit_permission(self, user):
        course_reg = get_course_registration(user, self.course)
        return course_reg.registration_type == TA or course_reg.registration_type == INSTRUCTOR


class TokenUseOption(models.Model):
    course = models.ForeignKey(
        CanvasCourse,
        related_name="token_use_options",
        on_delete=models.CASCADE,
    )
    tokens_required = models.FloatField()
    points_given = models.IntegerField()
    maximum_number_of_use = models.IntegerField(default=1)

    assignment_name = models.CharField(max_length=100)
    assignment_id = models.IntegerField(null=True, blank=True)


class TokenUse(models.Model):
    option = models.ForeignKey(TokenUseOption, on_delete=models.CASCADE, related_name="token_uses")
    user = models.ForeignKey(MyUser, on_delete=models.CASCADE, related_name="token_uses")
    num_used = models.IntegerField(default=0)

    def apply(self):
        pass

    def revert(self):
        pass
