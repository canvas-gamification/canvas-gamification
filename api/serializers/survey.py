from rest_framework import serializers

from general.models.survey import Survey


class SurveySerializer(serializers.ModelSerializer):
    class Meta:
        model = Survey
        fields = [
            "code",
            "response",
        ]
