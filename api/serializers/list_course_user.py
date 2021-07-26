from rest_framework import serializers
from canvas.models import CanvasCourse
from canvas.models import CanvasCourseRegistration
from accounts.models import MyUser


class UsersCourseCountSerializers(serializers.ModelSerializer):

    class Meta:
        model = MyUser
        fields = ['id', 'first_name', 'last_name', 'username', 'email', 'role']
