from django.contrib.auth.models import AbstractUser, AnonymousUser
import jwt

# Create your models here.
from django.db import models
from django.db.models import Count, Q
from django.conf import settings

from course.utils.utils import ensure_uqj, success_rate

STUDENT = "Student"
TEACHER = "Teacher"

USER_ROLE_CHOICES = [
    (TEACHER, TEACHER),
    (STUDENT, STUDENT),
]


class MyAnonymousUser(AnonymousUser):
    @property
    def is_teacher(self):
        return False


class MyUser(AbstractUser):
    role = models.CharField(max_length=100, choices=USER_ROLE_CHOICES, default=STUDENT)
    email = models.EmailField("email address", blank=True, unique=True)
    nickname = models.CharField(max_length=100, null=False, blank=False)

    @property
    def tokens(self):
        return self.actions.all().aggregate(models.Sum("token_change"))["token_change__sum"]

    @property
    def is_teacher(self):
        return self.role == TEACHER

    @property
    def is_student(self):
        return self.role == STUDENT

    @property
    def has_name(self):
        return self.first_name is not None and self.first_name != ""

    @property
    def has_complete_profile(self):
        return self.has_name

    @property
    def success_rate_by_category(self):
        data = list(
            self.question_junctions.values("question__category").annotate(
                total=Count("*"), solved=Count("pk", filter=Q(is_solved=True))
            )
        )
        data = [
            {
                "category": category["question__category"],
                "avgSuccess": success_rate(category["solved"], category["total"]),
            }
            for category in data
        ]
        return data

    @property
    def success_rate_by_difficulty(self):
        data = list(
            self.question_junctions.values("question__difficulty", "question__category").annotate(
                total=Count("*"), solved=Count("pk", filter=Q(is_solved=True))
            )
        )
        data = [
            {
                "category": difficulty["question__category"],
                "difficulty": difficulty["question__difficulty"],
                "avgSuccess": success_rate(difficulty["solved"], difficulty["total"]),
            }
            for difficulty in data
        ]
        return data

    @property
    def has_consent(self):
        return self.consents.exists()

    @property
    def community_jwt(self):
        private_key = settings.COMMUNITY_JWT_PRIVATE_KEY
        user_data = {
            "sub": self.id,
            "email": self.email or self.username,
            "name": self.get_full_name() or self.email,
        }
        return jwt.encode(user_data, private_key, algorithm="HS256")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        ensure_uqj(self, None)


GENDER_CHOICES = [
    ("MALE", "Male"),
    ("FEMALE", "Female"),
    ("NB", "Non-binary"),
    ("OTHER", "Other"),
    ("N/A", "Prefer not to answer"),
]


class UserConsent(models.Model):
    user = models.ForeignKey(
        MyUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=False,
        related_name="consents",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    consent = models.BooleanField(default=False)
    access_submitted_course_work = models.BooleanField(default=False)
    access_course_grades = models.BooleanField(default=False)

    legal_first_name = models.CharField(max_length=100, null=True, blank=True)
    legal_last_name = models.CharField(max_length=100, null=True, blank=True)
    gender = models.CharField(max_length=100, choices=GENDER_CHOICES, null=True, blank=True)
    race = models.CharField(max_length=500, null=True, blank=True)

    student_number = models.CharField(max_length=100, null=True, blank=True)
    date = models.CharField(max_length=100, null=True, blank=True)

    @property
    def is_student(self):
        return self.user.is_student
