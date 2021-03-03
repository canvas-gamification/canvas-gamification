from accounts.models import MyUser
from rest_framework import serializers


class UpdateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = MyUser
        fields = ['id', 'first_name', 'last_name', 'email']

    def validate_email(self, value):
        user = self.context['request'].user
        if MyUser.objects.exclude(pk=user.pk).filter(email=value).exists():
            raise serializers.ValidationError({"email": "This email is already in use."})
        return value

    def create(self, validated_data):
        user = self.context['request'].user

        user.first_name = validated_data['first_name']
        user.last_name = validated_data['last_name']
        user.email = validated_data['email']

        user.save()
        return user
