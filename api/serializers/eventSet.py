from rest_framework import serializers

from accounts.models import MyAnonymousUser
from api.serializers import EventSerializer
from canvas.models.models import EventSet


class EventSetSerializer(serializers.ModelSerializer):
    has_earn_tokens = serializers.SerializerMethodField("get_has_earn_tokens")
    events = EventSerializer(many=True)

    def get_user(self):
        user = MyAnonymousUser()
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user
        return user

    def get_has_earn_tokens(self, event_set):
        """
        check if all events in the event_set has been solved
        """
        user = self.get_user()

        if not user.is_authenticated:
            return False

        return all(event.has_solved_event(user) for event in event_set.events.all())

    class Meta:
        model = EventSet
        fields = [
            "id",
            "name",
            "course",
            "events",
            "tokens_worth",
            "has_earn_tokens",
        ]
