from rest_framework import serializers

from accounts.models import UserConsent
from course.models.models import Question, MultipleChoiceQuestion, QuestionCategory
from general.models import ContactUs
from utils.recaptcha import validate_recaptcha
from api.utils.category_api import count_category_questions, get_avg_question_success, get_user_success_rate


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['title', 'text', 'max_submission_allowed', 'time_created', 'time_modified', 'author', 'category',
                  'difficulty', 'is_verified']


class MultipleChoiceQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MultipleChoiceQuestion
        fields = ['id', 'title', 'text', 'answer', 'max_submission_allowed', 'time_created', 'time_modified', 'author',
                  'category',
                  'difficulty', 'is_verified', 'variables', 'choices', 'visible_distractor_count']


class UserConsentSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserConsent
        fields = ['user', 'consent', 'legal_first_name', 'legal_last_name', 'student_number', 'date']


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


class QuestionCategorySerializer(serializers.ModelSerializer):
    numQuestions = serializers.SerializerMethodField('count_questions')
    avgSuccess = serializers.SerializerMethodField('get_avg_success')

    def count_questions(self, category):
        return count_category_questions(category.pk)

    def get_avg_success(self, category):
        return get_avg_question_success(category.pk)

    class Meta:
        model = QuestionCategory
        fields = ['pk', 'name', 'description', 'parent', 'numQuestions', 'avgSuccess']

class UserQuestionCategorySerializer(serializers.Serializer):
    avgUserSuccess = serializers.SerializerMethodField('user_success')
    avgCategorySuccess = serializers.SerializerMethodField('category_success')

    def user_success(self, category):
        user_id = self.context['request'].query_params.get('user', None)
        return get_user_success_rate(user_id, category)

    def category_success(self, category):
        return get_avg_question_success(category)
