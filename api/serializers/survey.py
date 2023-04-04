from drf_queryfields import QueryFieldsMixin
from rest_framework import serializers

from general.models.survey import Survey


class SurveySerializer(QueryFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = Survey
        fields = [
            "user",
            "time_created",
            "code",
            "response",
        ]
        read_only_fields = [
            "user",
            "time_created",
        ]
