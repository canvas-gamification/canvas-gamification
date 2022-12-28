from django.db import models

from accounts.models import MyUser


class PageView(models.Model):
    user = models.ForeignKey(MyUser, related_name="page_views", on_delete=models.CASCADE)
    time_created = models.DateTimeField(auto_now_add=True, db_index=True)
    url = models.CharField(max_length=500, db_index=True)
