from rest_framework import serializers

from accounts.models import MyAnonymousUser
from canvas.models import Team

from api.serializers import CanvasCourseRegistrationSerializer
from canvas.utils.utils import get_course_registration


class TeamSerializer(serializers.ModelSerializer):

    def get_user(self):
        user = MyAnonymousUser()
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user
        return user

    class Meta:
        model = Team
        fields = ['id', 'name', 'tokens']
