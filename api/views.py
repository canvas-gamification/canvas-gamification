# Create your views here.
from rest_framework import viewsets, mixins

from accounts.models import UserConsent, MyUser
from accounts.utils.email_functions import send_activation_email
from api.permissions import TeacherAccessPermission, UserConsentPermission
from api.serializers import QuestionSerializer, MultipleChoiceQuestionSerializer, \
    UserConsentSerializer, ContactUsSerializer, QuestionCategorySerializer, UserStatsSerializer, \
    UserRegistrationSerializer
from course.models.models import Question, MultipleChoiceQuestion, QuestionCategory


class QuestionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    permission_classes = [TeacherAccessPermission, ]


class SampleMultipleChoiceQuestionViewSet(viewsets.ModelViewSet):
    queryset = MultipleChoiceQuestion.objects.filter(is_sample=True).all()
    serializer_class = MultipleChoiceQuestionSerializer


class UserConsentViewSet(viewsets.ModelViewSet):
    serializer_class = UserConsentSerializer
    permission_classes = [UserConsentPermission, ]
    queryset = UserConsent.objects.all()


class UserRegistrationViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = UserRegistrationSerializer

    def create(self, request, *args, **kwargs):
        user = super().create(request, *args, **kwargs)
        send_activation_email(request, user)


class ContactUsViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = ContactUsSerializer


class QuestionCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = QuestionCategory.objects.all()
    serializer_class = QuestionCategorySerializer


class UserStatsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MyUser.objects.all()
    serializer_class = UserStatsSerializer
