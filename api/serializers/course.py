from rest_framework import serializers

from accounts.models import MyAnonymousUser
from api.serializers import QuestionSerializer, UQJSerializer, CanvasCourseRegistrationSerializer, EventSerializer, \
    TokenUseOptionSerializer
from canvas.models import CanvasCourse
from canvas.utils.utils import get_course_registration
from course.models.models import UserQuestionJunction


class CourseSerializer(serializers.ModelSerializer):
    is_registered = serializers.SerializerMethodField('get_is_registered')
    events = EventSerializer(many=True, read_only=True)
    token_use_options = TokenUseOptionSerializer(many=True, read_only=True)
    question_set = QuestionSerializer(many=True, read_only=True)
    uqjs = serializers.SerializerMethodField('get_uqjs')
    course_reg = serializers.SerializerMethodField('get_course_reg')
    has_create_event_permission = serializers.SerializerMethodField('get_create_event_permission')

    def get_user(self):
        user = MyAnonymousUser()
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user
        return user

    def get_uqjs(self, course):
        user = self.get_user()

        if not user.is_authenticated:
            return []

        is_instructor = course.has_edit_permission(user)
        if is_instructor:
            uqjs = UserQuestionJunction.objects.filter(user=user, question__course=course).all()
        else:
            uqjs = UserQuestionJunction.objects.none()

        serialized_uqjs = [UQJSerializer(uqj).data for uqj in uqjs]

        return serialized_uqjs

    def get_is_registered(self, course):
        user = self.get_user()
        # if user is not logged in or the request has no user attached
        if not user.is_authenticated:
            return False

        return course.is_registered(user)

    def get_course_reg(self, course):
        user = self.get_user()
        # if user is not logged in or the request has no user attached
        if not user.is_authenticated:
            return None

        course_reg = get_course_registration(user, course)
        return CanvasCourseRegistrationSerializer(course_reg).data

    def get_create_event_permission(self, course):
        user = self.get_user()

        # if user is not logged in or the request has no user attached
        if not user.is_authenticated:
            return False

        return course.has_create_event_permission(user)

    class Meta:
        model = CanvasCourse
        fields = ['id', 'mock', 'name', 'url', 'course_id', 'token', 'allow_registration', 'visible_to_students',
                  'start_date', 'end_date', 'instructor', 'status', 'is_registered', 'token_use_options', 'events',
                  'uqjs', 'question_set', 'course_reg', 'leader_board', 'has_create_event_permission']


class CourseSerializerList(serializers.ModelSerializer):
    is_registered = serializers.SerializerMethodField('get_is_registered')
    events = EventSerializer(many=True, read_only=True)

    def get_user(self):
        user = MyAnonymousUser()
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user
        return user

    def get_is_registered(self, course):
        user = self.get_user()
        # if user is not logged in or the request has no user attached
        if not user.is_authenticated:
            return False

        return course.is_registered(user)

    class Meta:
        model = CanvasCourse
        fields = ['id', 'mock', 'name', 'url', 'course_id', 'allow_registration', 'visible_to_students', 'start_date',
                  'end_date', 'instructor', 'status', 'is_registered', 'events', ]
