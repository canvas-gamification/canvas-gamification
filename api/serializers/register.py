from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from accounts.models import MyUser
from utils.recaptcha import validate_recaptcha


class UserRegistrationSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True, validators=[UniqueValidator(queryset=MyUser.objects.all())])
    password = serializers.CharField(write_only=True, required=True)
    password2 = serializers.CharField(write_only=True, required=True)
    recaptcha_key = serializers.CharField(write_only=True)

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
            raise serializers.ValidationError('reCaptcha should be validate')
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs
