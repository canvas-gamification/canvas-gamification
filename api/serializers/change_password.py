from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

import api.error_messages as ERROR_MESSAGES
from accounts.models import MyUser


class ChangePasswordSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        error_messages=ERROR_MESSAGES.PASSWORD.ERROR_MESSAGES,
    )
    password2 = serializers.CharField(
        write_only=True,
        required=True,
        error_messages=ERROR_MESSAGES.PASSWORD.ERROR_MESSAGES,
    )
    old_password = serializers.CharField(
        write_only=True,
        required=True,
        error_messages=ERROR_MESSAGES.PASSWORD.ERROR_MESSAGES,
    )

    class Meta:
        model = MyUser
        fields = ['old_password', 'password', 'password2']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError({"old_password": "Old password is not correct"})
        return value

    def create(self, validated_data):
        user = self.context['request'].user
        user.set_password(validated_data['password'])
        user.save()
        return user
