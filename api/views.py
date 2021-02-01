# Create your views here.
from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticated

from accounts.models import UserConsent, MyUser
from api.permissions import TeacherAccessPermission, UserConsentPermission
from api.serializers import QuestionSerializer, MultipleChoiceQuestionSerializer, \
    UserConsentSerializer, ContactUsSerializer, QuestionCategorySerializer, UserStatsSerializer, \
    UQJSerializer, ActionsSerializer
from course.models.models import Question, MultipleChoiceQuestion, QuestionCategory


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
    ?recent - if true, renders the list in recent first order
    """
    serializer_class = ActionsSerializer
    permission_classes = [IsAuthenticated, ]

    def get_queryset(self):
        user = self.request.user
        is_recent = self.request.query_params.get('recent', False)
        if is_recent:
            return user.actions.all().order_by("-time_modified")
        return user.actions.all()


class UQJViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UQJSerializer
    permission_classes = [IsAuthenticated, ]

    def get_queryset(self):
        user = self.request.user
        is_recent = self.request.query_params.get('recent', False)
        if is_recent:
            return user.question_junctions.all().order_by('-last_viewed')
        return user.question_junctions.all()
