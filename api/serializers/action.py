from rest_framework import serializers

from general.models.action import Action


class ActionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Action
        exclude = []
