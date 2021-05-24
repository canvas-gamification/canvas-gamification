from django.contrib.auth.password_validation import validate_password
from django.utils.encoding import force_text
from django.utils.http import urlsafe_base64_decode

from rest_framework import serializers

from accounts.models import MyUser


class ResetPasswordSerializer(serializers.ModelSerializer):
    uid = serializers.CharField(write_only=True, required=True)
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = MyUser
        fields = ['uid', 'password', 'password2']

    def validate(self, attrs):
        uid = force_text(urlsafe_base64_decode(attrs['uid']))
        old_password = MyUser.objects.get(pk=uid).password
        if old_password == attrs['password']:
            raise serializers.ValidationError({"password": "New Password is the same as the old password"})
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        uid = force_text(urlsafe_base64_decode(validated_data['uid']))
        user = MyUser.objects.get(pk=uid)
        user.set_password(validated_data['password'])
        user.save()
        return user
