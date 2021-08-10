from rest_framework import serializers
from accounts.models import MyUser


class UsersCountSerializers(serializers.ModelSerializer):
    class Meta:
        model = MyUser
        fields = ['id', 'first_name', 'last_name', 'username', 'email', 'role']
