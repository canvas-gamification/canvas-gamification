from django.db import models


class FAQ(models.Model):
    question = models.CharField(max_length=200)
    answer = models.TextField()
