from rest_framework import serializers

from accounts.models import MyUser


class UserStatsSerializer(serializers.ModelSerializer):
    successRateByCategory = serializers.SerializerMethodField('success_rate_by_category')
    successRateByDifficulty = serializers.SerializerMethodField('success_rate_by_difficulty')

    def success_rate_by_category(self, user):
        return user.success_rate_by_category

    def success_rate_by_difficulty(self, user):
        return user.success_rate_by_difficulty

    class Meta:
        model = MyUser
        fields = ['pk', 'successRateByCategory', 'successRateByDifficulty']
