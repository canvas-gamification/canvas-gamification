from django.contrib.auth import get_user_model

from rest_framework import serializers

from accounts.models import UserConsent, MyUser
from course.models.models import Question, MultipleChoiceQuestion, QuestionCategory
from general.models import ContactUs
from utils.recaptcha import validate_recaptcha

User = get_user_model()


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


class UserRegistrationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password1 = serializers.CharField()
    password2 = serializers.CharField()
    recaptcha_key = serializers.CharField(write_only=True)

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        
        user = User.objects.create_user(
            validated_data.get('email'),
            validated_data.get('password'))
        user.is_active = False
        user.email = validated_data.get('email')
        user.save()
        return user

    def validate_recaptcha_key(self, value):
        if not validate_recaptcha(value):
            raise serializers.ValidationError('reCaptcha should be validate')
        return value

    def validate_password(self, value, value2):
        if value != value2:
            raise serializers.ValidationError('Password should match')
        return value


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
    nextCategories = serializers.SerializerMethodField('next_categories_ids')

    def count_questions(self, category):
        return category.question_count

    def get_avg_success(self, category):
        return category.average_success

    def next_categories_ids(self, category):
        return category.next_category_ids

    class Meta:
        model = QuestionCategory
        fields = ['pk', 'name', 'description', 'parent', 'numQuestions', 'avgSuccess', 'nextCategories']


class UserStatsSerializer(serializers.ModelSerializer):
    successRateByCategory = serializers.SerializerMethodField('success_rate_by_category')

    def success_rate_by_category(self, user):
        return user.success_rate_by_category

    class Meta:
        model = MyUser
        fields = ['pk', 'successRateByCategory']
