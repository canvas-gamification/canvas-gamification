from rest_framework import serializers

from general.models.contact_us import ContactUs
from utils.recaptcha import validate_recaptcha


class ContactUsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactUs
        fields = ['fullname', 'email', 'comment', 'recaptcha_key']

    recaptcha_key = serializers.CharField(write_only=True)

    def validate_recaptcha_key(self, value):
        if not validate_recaptcha(value):
            raise serializers.ValidationError('reCaptcha should be validate')
        return value

    def create(self, validated_data):
        validated_data.pop('recaptcha_key', None)
        return super().create(validated_data)
