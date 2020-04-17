from django.contrib import admin

# Register your models here.
from accounts.models import MyUser


class MyUserAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'username', 'email', 'role')


admin.site.register(MyUser, MyUserAdmin)
