from rest_framework import serializers

from general.models import Action


class ActionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Action
        exclude = ['user']
