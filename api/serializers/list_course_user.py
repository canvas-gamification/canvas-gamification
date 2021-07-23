from rest_framework import serializers
from canvas.models import CanvasCourse
from canvas.models import CanvasCourseRegistration
from accounts.models import MyUser


class UsersCourseCountSerializers(serializers.ModelSerializer):
    course_in = serializers.CharField()

    class Meta:
        model = MyUser
        fields = ['id', 'first_name', 'last_name', 'username', 'email', 'role', 'course_in']
