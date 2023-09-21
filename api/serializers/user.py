from drf_queryfields import QueryFieldsMixin
from rest_framework import serializers

from accounts.models import MyUser


class UserSerializer(QueryFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = MyUser
        fields = [
            "first_name",
            "last_name",
            "username",
            "email",
            "nickname",
            "role",
            "date_joined",
        ]
