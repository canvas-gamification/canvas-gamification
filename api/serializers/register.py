from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from accounts.models import MyUser
import api.error_messages as ERROR_MESSAGES
from utils.recaptcha import validate_recaptcha


class UserRegistrationSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        error_messages=ERROR_MESSAGES.EMAIL.ERROR_MESSAGES,
        validators=[UniqueValidator(
            queryset=MyUser.objects.all(),
            message=ERROR_MESSAGES.EMAIL.UNIQUE,
        )]
    )
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
    recaptcha_key = serializers.CharField(
        write_only=True,
        required=True,
        error_messages=ERROR_MESSAGES.RECAPTCHA.ERROR_MESSAGES,
    )

    class Meta:
        model = MyUser
        fields = ('email', 'password', 'password2', 'recaptcha_key')

    def create(self, validated_data):
        user = MyUser.objects.create_user(
            username=validated_data['email'],
            email=validated_data['email'])
        user.set_password(validated_data['password'])

        user.is_active = False
        user.save()
        return user

    def validate_recaptcha_key(self, value):
        if not validate_recaptcha(value):
            raise serializers.ValidationError(ERROR_MESSAGES.RECAPTCHA.INVALID)
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError(ERROR_MESSAGES.PASSWORD.MATCH)
        return attrs
