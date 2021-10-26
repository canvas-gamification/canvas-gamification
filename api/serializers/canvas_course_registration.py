from rest_framework import serializers

from accounts.models import MyAnonymousUser
from api.serializers import TokenUseSerializer
from canvas.models import CanvasCourseRegistration


class CanvasCourseRegistrationSerializer(serializers.ModelSerializer):
    token_uses = serializers.SerializerMethodField('get_token_uses')

    def get_token_uses(self, course_reg):
        token_uses = course_reg.get_token_uses()
        token_uses = [TokenUseSerializer(token_use).data for token_use in token_uses]

        return token_uses

    def get_is_registered(self, course):
        user = MyAnonymousUser()
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user

        # if user is not logged in or the request has no user attached
        if not user.is_authenticated:
            return False

        return course.is_registered(user)

    class Meta:
        model = CanvasCourseRegistration
        fields = ['id', 'canvas_user_id', 'status', 'is_verified', 'is_blocked', 'token_uses', 'total_tokens_received',
                  'available_tokens', 'username', 'name']
