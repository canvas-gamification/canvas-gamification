from rest_framework import serializers

from accounts.models import UserConsent, MyUser
from course.models.models import Question, MultipleChoiceQuestion, QuestionCategory, UserQuestionJunction
from general.models import ContactUs, Action, FAQ
from canvas.models import CanvasCourse
from utils.recaptcha import validate_recaptcha


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


class ActionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Action
        exclude = ['user']


class UQJSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserQuestionJunction
        exclude = ['user']
        depth = 1


class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = ['question', 'answer']


class CourseSerializer(serializers.ModelSerializer):
    is_registered = serializers.SerializerMethodField('get_is_registered')

    def get_is_registered(self, course):
        user = None
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user

        # if user is not logged in or the request has no user attached
        if user is None or not user.is_authenticated:
            return False

        return course.is_registered(user)

    class Meta:
        model = CanvasCourse
        fields = ['id', 'mock', 'name', 'url', 'course_id', 'token', 'allow_registration', 'visible_to_students',
                  'start_date', 'end_date', 'instructor', 'status', 'is_registered']
