from rest_framework import serializers

from accounts.models import MyAnonymousUser
from canvas.models import Event
from canvas.utils.utils import get_total_event_grade


class EventSerializer(serializers.ModelSerializer):
    is_allowed_to_open = serializers.SerializerMethodField('get_is_allowed_to_open')
    has_edit_permission = serializers.SerializerMethodField('get_has_edit_permission')
    total_event_grade = serializers.SerializerMethodField('get_total_event_grade')

    def get_user(self):
        user = MyAnonymousUser()
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user
        return user

    def get_total_event_grade(self, event):
        user = self.get_user()
        # if user is not logged in or the request has no user attached
        if not user.is_authenticated:
            return 0

        return get_total_event_grade(event, user)

    def get_is_allowed_to_open(self, event):
        user = self.get_user()
        # if user is not logged in or the request has no user attached
        if not user.is_authenticated:
            return False

        return event.is_allowed_to_open(user)

    def get_has_edit_permission(self, event):
        user = self.get_user()
        # if user is not logged in or the request has no user attached
        if not user.is_authenticated:
            return False

        return event.has_edit_permission(user)

    class Meta:
        model = Event
        fields = ['id', 'name', 'type', 'count_for_tokens', 'start_date', 'end_date', 'course', 'is_allowed_to_open',
                  'has_edit_permission', 'is_open', 'is_exam', 'total_event_grade', ]
