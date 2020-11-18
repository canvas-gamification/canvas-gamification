from django.contrib.auth.models import AbstractUser, AnonymousUser
# Create your models here.
from django.db import models

from course.utils.utils import ensure_uqj

STUDENT = 'Student'
TEACHER = 'Teacher'

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
    email = models.EmailField('email address', blank=True, unique=True)

    @property
    def tokens(self):
        return self.actions.all().aggregate(models.Sum('token_change'))['token_change__sum']

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

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        ensure_uqj(self, None)


class UserConsent(models.Model):
    user = models.ForeignKey(MyUser, on_delete=models.SET_NULL, null=True, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)
    consent = models.BooleanField(default=False)

    legal_first_name = models.CharField(max_length=100, null=True, blank=True)
    legal_last_name = models.CharField(max_length=100, null=True, blank=True)
    student_number = models.CharField(max_length=100, null=True, blank=True)
    date = models.CharField(max_length=100, null=True, blank=True)
