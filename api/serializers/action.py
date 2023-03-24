from drf_queryfields import QueryFieldsMixin
from rest_framework import serializers

from general.models.action import Action


class ActionsSerializer(QueryFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = Action
        exclude = []
        read_only_fields = ["actor"]
