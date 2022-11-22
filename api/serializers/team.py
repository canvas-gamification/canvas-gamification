from rest_framework import serializers

from canvas.models.team import Team


class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ["id", "time_created", "time_modified", "name", "is_private", "who_can_join", "event",
                  "course_registrations", "score", "member_names", "number_of_member", "member_usernames"]
