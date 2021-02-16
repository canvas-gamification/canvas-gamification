# Create your views here.
from django.utils import timezone
from django.db.models import Q
from rest_framework import viewsets, mixins, filters
from rest_framework.permissions import IsAuthenticated

from accounts.models import UserConsent, MyUser
from api.pagination import BasePagination
from api.permissions import TeacherAccessPermission, UserConsentPermission
from canvas.models import CanvasCourse
from api.serializers import QuestionSerializer, MultipleChoiceQuestionSerializer, \
    UserConsentSerializer, ContactUsSerializer, QuestionCategorySerializer, UserStatsSerializer, \
    UQJSerializer, ActionsSerializer, FAQSerializer, CourseSerializer

from course.models.models import Question, MultipleChoiceQuestion, QuestionCategory
from general.models import FAQ


class QuestionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    permission_classes = [TeacherAccessPermission, ]


class SampleMultipleChoiceQuestionViewSet(viewsets.ModelViewSet):
    queryset = MultipleChoiceQuestion.objects.filter(is_sample=True).all()
    serializer_class = MultipleChoiceQuestionSerializer


class UserConsentViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = UserConsentSerializer
    permission_classes = [UserConsentPermission, ]
    queryset = UserConsent.objects.all()


class ContactUsViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = ContactUsSerializer


class QuestionCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = QuestionCategory.objects.all()
    serializer_class = QuestionCategorySerializer


class UserStatsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MyUser.objects.all()
    serializer_class = UserStatsSerializer


class ActionsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Query Parameters
    + Standard ordering is applied
    """
    serializer_class = ActionsSerializer
    permission_classes = [IsAuthenticated, ]
    pagination_class = BasePagination
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['time_modified', ]

    def get_queryset(self):
        user = self.request.user
        return user.actions.all()


class UQJViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Query Parameters
    + Standard ordering is applied
    """
    serializer_class = UQJSerializer
    permission_classes = [IsAuthenticated, ]
    pagination_class = BasePagination
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['last_viewed', ]

    def get_queryset(self):
        user = self.request.user
        return user.question_junctions.all()


class FAQViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = FAQ.objects.all()
    serializer_class = FAQSerializer


class CourseViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Optional Parameters
    ?registered: boolean => if true, filter retrieved courses by if user is currently registered in them
    """
    serializer_class = CourseSerializer

    def get_queryset(self):
        user = self.request.user
        registered = self.request.query_params.get('registered', None)
        if registered:
            registered = registered.lower() == 'true'

        queryset = CanvasCourse.objects.all()

        if not user.is_authenticated or user.is_student:
            queryset = queryset.filter(visible_to_students=True).all()

        if registered:
            registered_ids = user.canvascourseregistration_set.filter(is_verified=True, is_blocked=False)\
                .values_list('course_id', flat=True)
            queryset = queryset.filter(pk__in=registered_ids)

        return queryset.all()
