from rest_framework import serializers

from api.serializers.token_use import TokenUseSerializer
from api.serializers.token_use_option import TokenUseOptionSerializer
from canvas.models import CanvasCourseRegistration


class CanvasCourseRegistrationSerializer(serializers.ModelSerializer):
    token_uses = serializers.SerializerMethodField('get_token_uses')

    def get_token_uses(self, course_reg):
        token_uses = course_reg.get_token_uses()
        test = [TokenUseSerializer(token_use).data for token_use in token_uses]

        return test

    def get_is_registered(self, course):
        user = None
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user

        # if user is not logged in or the request has no user attached
        if user is None or not user.is_authenticated:
            return False

        return course.is_registered(user)

    class Meta:
        model = CanvasCourseRegistration
        fields = [
                'id',
                'canvas_user_id',
                'is_verified',
                'is_blocked',
                'verification_code',
                'verification_attempts',
                'course',
                'user',
                'canvas_user',
                'token_uses',
                'total_tokens_received',
                'available_tokens']
