from rest_framework import serializers

from accounts.models import MyAnonymousUser

from canvas.models import TeamRegistration

class TeamRegistrationSerializer(serializers.ModelSerializer):

    def get_is_registered(self, team):
        user = MyAnonymousUser()
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user

        # if user is not logged in or the request has no user attached
        if not user.is_authenticated:
            return False

        return team.is_registered(user)

    class Meta:
        model = TeamRegistration
        fields = ['id', 'canvas_user_id']