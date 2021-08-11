from rest_framework import serializers

import api.error_messages as ERROR_MESSAGES
from accounts.models import UserConsent


class UserConsentSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(default=serializers.CurrentUserDefault(), read_only=True)

    consent = serializers.BooleanField(
        required=True,
        error_messages=ERROR_MESSAGES.CONSENT.ERROR_MESSAGES,
    )

    legal_first_name = serializers.CharField(
        required=True,
        error_messages=ERROR_MESSAGES.FIRSTNAME.ERROR_MESSAGES,
    )

    legal_last_name = serializers.CharField(
        required=True,
        error_messages=ERROR_MESSAGES.LASTNAME.ERROR_MESSAGES,
    )

    student_number = serializers.CharField(
        required=True,
        error_messages=ERROR_MESSAGES.STUDENT_NUMBER.ERROR_MESSAGES,
    )

    date = serializers.CharField(
        required=True,
        error_messages=ERROR_MESSAGES.DATE.ERROR_MESSAGES,
    )

    class Meta:
        model = UserConsent
        fields = ['user', 'consent', 'legal_first_name', 'legal_last_name', 'student_number', 'date',
                  'access_submitted_course_work', 'access_course_grades', 'is_student']
