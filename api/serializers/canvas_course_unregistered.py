from rest_framework import serializers

from accounts.models import MyAnonymousUser
from canvas.models import MyUser
from canvas.models import CanvasCourseRegistration


class CanvasCourseUnRegisteredSerializer(serializers.ModelSerializer):
    token_uses = serializers.SerializerMethodField('get_token_uses')

    def get_not_registered(self, course):
        user = MyAnonymousUser()
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user

        # if user is not logged in or the request has no user attached
        if not user.is_authenticated:
            return False

        if not course.is_registered(user).exists():
            return user

    class Meta:
        model = MyUser
        fields = ['id', 'first_name', 'last_name', 'username', 'email', 'role']
