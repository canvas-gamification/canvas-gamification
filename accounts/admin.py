from django.contrib import admin

# Register your models here.
from accounts.models import MyUser

admin.site.register(MyUser)