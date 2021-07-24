from rest_framework.validators import UniqueValidator

from accounts.models import MyUser
from rest_framework import serializers
import api.error_messages as ERROR_MESSAGES


class UpdateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = MyUser
        fields = ['id', 'first_name', 'last_name', 'email']

    email = serializers.EmailField(
        read_only=True,
        error_messages=ERROR_MESSAGES.EMAIL.ERROR_MESSAGES,
        validators=[UniqueValidator(
            queryset=MyUser.objects.all(),
            message=ERROR_MESSAGES.EMAIL.UNIQUE,
        )]
    )

    first_name = serializers.CharField(
        required=True,
        error_messages=ERROR_MESSAGES.FIRSTNAME.ERROR_MESSAGES,
    )

    last_name = serializers.CharField(
        required=True,
        error_messages=ERROR_MESSAGES.LASTNAME.ERROR_MESSAGES,
    )

    def create(self, validated_data):
        user = self.context['request'].user

        user.first_name = validated_data['first_name']
        user.last_name = validated_data['last_name']
        user.email = validated_data['email']

        user.save()
        return user
