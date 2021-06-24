from django.contrib.auth.password_validation import validate_password
from django.utils.encoding import force_text
from django.utils.http import urlsafe_base64_decode
from rest_framework import serializers

import api.error_messages as ERROR_MESSAGES
from accounts.models import MyUser
from accounts.utils.email_functions import verify_reset


class ResetPasswordSerializer(serializers.ModelSerializer):
    uid = serializers.CharField(write_only=True, required=True)
    token = serializers.CharField(write_only=True, required=True)

    password = serializers.CharField(
        write_only=True,
        required=True,
        error_messages=ERROR_MESSAGES.PASSWORD.ERROR_MESSAGES,
        validators=[validate_password]
    )
    password2 = serializers.CharField(
        write_only=True,
        required=True,
        error_messages=ERROR_MESSAGES.PASSWORD.ERROR_MESSAGES,
    )

    class Meta:
        model = MyUser
        fields = ['uid', 'token', 'password', 'password2']

    def validate(self, attrs):
        user = verify_reset(attrs['uid'], attrs['token'])
        if not user:
            raise serializers.ValidationError(ERROR_MESSAGES.PASSWORD.INVALID_RESET_LINK)
        old_password = user.password
        if old_password == attrs['password']:
            raise serializers.ValidationError(ERROR_MESSAGES.PASSWORD.DUPLICATED)
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError(ERROR_MESSAGES.PASSWORD.MATCH)
        return attrs

    def create(self, validated_data):
        uid = force_text(urlsafe_base64_decode(validated_data['uid']))
        user = MyUser.objects.get(pk=uid)
        user.set_password(validated_data['password'])
        user.save()
        return user
