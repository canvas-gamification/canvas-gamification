from rest_framework import serializers

from accounts.models import MyUser


class UserStatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = MyUser
        fields = ["pk"]
