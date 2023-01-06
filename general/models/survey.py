import jsonfield
from django.db import models

from accounts.models import MyUser


class Survey(models.Model):
    time_created = models.DateTimeField(auto_now_add=True)
    time_modified = models.DateTimeField(auto_now=True)

    user = models.ForeignKey(MyUser, related_name="surveys", on_delete=models.CASCADE)
    code = models.CharField(max_length=100)
    response = jsonfield.JSONField(null=True)
