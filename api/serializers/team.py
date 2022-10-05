from rest_framework import serializers

from canvas.models.team import Team


class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ['id', 'name', 'event', 'course_registrations', 'score']
