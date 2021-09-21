from django.db import models
from djrichtextfield.models import RichTextField


class FAQ(models.Model):
    question = models.CharField(max_length=200)
    answer = RichTextField()
