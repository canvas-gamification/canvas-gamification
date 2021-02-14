from rest_framework import serializers

from accounts.models import UserConsent


class UserConsentSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(default=serializers.CurrentUserDefault(), read_only=True)

    class Meta:
        model = UserConsent
        fields = ['user', 'consent', 'legal_first_name', 'legal_last_name', 'student_number', 'date']
