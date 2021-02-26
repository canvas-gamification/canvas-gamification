from rest_framework import serializers

from canvas.models import TokenUseOption


class TokenUseOptionSerializer(serializers.ModelSerializer):
    def get_user(self):
        user = None
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user

        return user

    class Meta:
        model = TokenUseOption
        fields = '__all__'
