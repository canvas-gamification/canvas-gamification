from django.db import models

# Create your models here.
from djrichtextfield.models import RichTextField


class Problem(models.Model):
    title = models.CharField(max_length=300)
    text = RichTextField()
