from django.contrib.auth import get_user_model
from django.db import models

# Create your models here.
from djrichtextfield.models import RichTextField


class FAQ(models.Model):
    question = models.CharField(max_length=200)
    answer = RichTextField()


class Action(models.Model):

    COMPLETE = 'Complete'
    PENDING = 'Pending'

    ACTION_STATUS_CHOICES = [
        (COMPLETE, COMPLETE),
        (PENDING, PENDING),
    ]

    user = models.ForeignKey(get_user_model(), related_name='actions', on_delete=models.CASCADE)
    description = models.CharField(max_length=500)
    token_change = models.FloatField(default=0)
    status = models.CharField(max_length=100, choices=ACTION_STATUS_CHOICES)
    time_created = models.DateTimeField(auto_now_add=True)
    time_modified = models.DateTimeField(auto_now=True)

    @classmethod
    def create_action(cls, user, description, token_change, status):
        action = Action(user=user, description=description, token_change=token_change, status=status)
        action.save()
