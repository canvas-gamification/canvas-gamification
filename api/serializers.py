from rest_framework import serializers

from accounts.models import UserConsent, MyUser
from course.models.models import Question, MultipleChoiceQuestion, QuestionCategory, UserQuestionJunction
from general.models import ContactUs
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


class UserActionsSerializer(serializers.ModelSerializer):
    actions = serializers.SerializerMethodField('get_actions')

    def get_actions(self, user):
        is_recent = self.context['request'].query_params.get('recent', False)
        if is_recent:
            return user.actions.order_by("-time_modified").values()
        else:
            return user.actions.values()

    class Meta:
        model = MyUser
        fields = ['pk', 'actions']


class UQJSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserQuestionJunction
        exclude = ['user']
        depth = 1


class UserUQJSerializer(serializers.ModelSerializer):
    question_junctions = serializers.SerializerMethodField()

    def get_question_junctions(self, user):
        is_recent = self.context['request'].query_params.get('recent', False)
        if is_recent:
            uqj_set = user.question_junctions.all().order_by('-last_viewed')
        else:
            uqj_set = user.question_junctions.all()

        return UQJSerializer(uqj_set, many=True).data

    class Meta:
        model = MyUser
        fields = ['pk', 'question_junctions']
        depth = 2
