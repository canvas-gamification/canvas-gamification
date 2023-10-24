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
        validators=[
            UniqueValidator(
                queryset=MyUser.objects.all(),
                message=ERROR_MESSAGES.EMAIL.UNIQUE,
            )
        ],
    )
    first_name = serializers.CharField(
        required=True,
        error_messages=ERROR_MESSAGES.FIRSTNAME.ERROR_MESSAGES,
    )
    last_name = serializers.CharField(
        required=True,
        error_messages=ERROR_MESSAGES.LASTNAME.ERROR_MESSAGES,
    )
    nickname = serializers.CharField(
        required=True,
        error_messages=ERROR_MESSAGES.NICKNAME.ERROR_MESSAGES,
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        error_messages=ERROR_MESSAGES.PASSWORD.ERROR_MESSAGES,
        validators=[validate_password],
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
        fields = ("email", "first_name", "last_name", "nickname", "password", "password2", "recaptcha_key")

    def create(self, validated_data):
        user = MyUser.objects.create_user(
            username=validated_data["email"],
            email=validated_data["email"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            nickname=validated_data["nickname"],
        )
        user.set_password(validated_data["password"])

        user.is_active = False
        user.save()
        return user

    def validate_recaptcha_key(self, value):
        if not validate_recaptcha(value):
            raise serializers.ValidationError(ERROR_MESSAGES.RECAPTCHA.INVALID)
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError(ERROR_MESSAGES.PASSWORD.MATCH)
        return attrs
