from rest_framework import serializers

from accounts.models import MyAnonymousUser
from api.serializers import (
    QuestionSerializer,
    UQJSerializer,
    CanvasCourseRegistrationSerializer,
    EventSerializer,
    TokenUseOptionSerializer,
)
from canvas.models.models import CanvasCourse
from canvas.utils.utils import get_course_registration
from course.models.models import UserQuestionJunction


class CourseCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CanvasCourse
        fields = [
            "id",
            "name",
            "description",
            "url",
            "start_date",
            "end_date",
            "registration_mode",
            "registration_code",
        ]
        read_only_fields = ["id"]


class CourseSerializer(serializers.ModelSerializer):
    is_registered = serializers.SerializerMethodField("get_is_registered")
    events = EventSerializer(many=True, read_only=True)
    token_use_options = TokenUseOptionSerializer(many=True, read_only=True)
    course_reg = serializers.SerializerMethodField("get_course_reg")
    has_create_event_permission = serializers.SerializerMethodField("get_create_event_permission")
    has_view_permission = serializers.SerializerMethodField("get_has_view_permission")

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

    def get_has_view_permission(self, course):
        user = self.get_user()

        # if user is not logged in or the request has no user attached
        if not user.is_authenticated:
            return False

        return course.has_view_permission(user)

    class Meta:
        model = CanvasCourse
        fields = [
            "id",
            "name",
            "url",
            "allow_registration",
            "visible_to_students",
            "start_date",
            "end_date",
            "instructor",
            "status",
            "is_registered",
            "token_use_options",
            "events",
            "course_reg",
            "has_create_event_permission",
            "has_view_permission",
            "description",
            "registration_mode",
            "registration_code",
        ]
        extra_kwargs = {"registration_code": {"write_only": True}}


class CourseListSerializer(serializers.ModelSerializer):
    is_registered = serializers.SerializerMethodField("get_is_registered")
    events = EventSerializer(many=True, read_only=True)
    has_view_permission = serializers.SerializerMethodField("get_has_view_permission")

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

    def get_has_view_permission(self, course):
        user = self.get_user()

        # if user is not logged in or the request has no user attached
        if not user.is_authenticated:
            return False

        return course.has_view_permission(user)

    class Meta:
        model = CanvasCourse
        fields = [
            "id",
            "name",
            "url",
            "allow_registration",
            "visible_to_students",
            "start_date",
            "end_date",
            "instructor",
            "status",
            "is_registered",
            "events",
            "description",
            "registration_mode",
            "has_view_permission",
        ]
