from django.contrib.auth.models import AbstractUser


# Create your models here.
from django.db import models

STUDENT = 'Student'
TEACHER = 'Teacher'

USER_ROLE_CHOICES = [
    (TEACHER, TEACHER),
    (STUDENT, STUDENT),
]


class MyUser(AbstractUser):
    role = models.CharField(max_length=100, choices=USER_ROLE_CHOICES, default=STUDENT)

    def is_teacher(self):
        return self.role == TEACHER

    def is_student(self):
        return self.role == STUDENT

    @property
    def has_name(self):
        return self.first_name is not None and self.first_name != ""

    @property
    def has_complete_profile(self):
        return self.has_name
