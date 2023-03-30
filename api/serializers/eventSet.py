# from rest_framework import serializers
#
# from accounts.models import MyAnonymousUser
# from canvas.models.models import EventSet
# from canvas.utils.utils import get_has_solved_event
#
#
# class EventSetSerializer(serializers.ModelSerializer):
#     has_earn_tokens = serializers.SerializerMethodField("get_has_earn_tokens")
#
#     def get_user(self):
#         user = MyAnonymousUser()
#         request = self.context.get("request")
#         if request and hasattr(request, "user"):
#             user = request.user
#         return user
#
#     def get_has_earn_tokens(self, event_set):
#         #  when all events in the event_set has been solved
#         user = self.get_user()
#         return all(get_has_solved_event(event, user) for event in event_set.events)
#
#     class Meta:
#         model = EventSet
#         fields = [
#             "id",
#             "name",
#             "course",
#             "events",
#             "tokens_worth",
#             "is_closed",
#             "has_earn_tokens",
#         ]
