from rest_framework import serializers

from accounts.models import MyUser


class UserStatsSerializer(serializers.ModelSerializer):
    successRateByCategory = serializers.SerializerMethodField('success_rate_by_category')

    def success_rate_by_category(self, user):
        return user.success_rate_by_category

    class Meta:
        model = MyUser
        fields = ['pk', 'successRateByCategory']
