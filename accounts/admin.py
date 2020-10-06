from django.contrib import admin

# Register your models here.
from accounts.models import MyUser, UserConsent


class MyUserAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'username', 'email', 'role')


admin.site.register(MyUser, MyUserAdmin)
admin.site.register(UserConsent)
