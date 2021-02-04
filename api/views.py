# Create your views here.
from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticated

from accounts.models import UserConsent, MyUser
from api.permissions import TeacherAccessPermission, UserConsentPermission
from api.serializers import QuestionSerializer, MultipleChoiceQuestionSerializer, \
    UserConsentSerializer, ContactUsSerializer, QuestionCategorySerializer, UserStatsSerializer, \
    UserRegistrationSerializer, UpdateProfileSerializer, ResetPasswordSerializer
from course.models.models import Question, MultipleChoiceQuestion, QuestionCategory


class QuestionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    permission_classes = [TeacherAccessPermission, ]


class SampleMultipleChoiceQuestionViewSet(viewsets.ModelViewSet):
    queryset = MultipleChoiceQuestion.objects.filter(is_sample=True).all()
    serializer_class = MultipleChoiceQuestionSerializer


class ResetPasswordViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated, ]
    serializer_class = ResetPasswordSerializer


class UserConsentViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return UserConsent.objects.filter(user=self.request.user.id)

    serializer_class = UserConsentSerializer
    permission_classes = [IsAuthenticated, ]

    def perform_create(self, serializer):
        request = serializer.context['request']
        serializer.save(user=request.user)


class UserRegistrationViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = UserRegistrationSerializer
    queryset = MyUser.objects.all()

    def create(self, request, *args, **kwargs):
        user = super().create(request, *args, **kwargs)
        # send_activation_email(request, user)
        return user


class UpdateProfileViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return MyUser.objects.filter(id=self.request.user.id)

    serializer_class = UpdateProfileSerializer
    permission_classes = [IsAuthenticated, ]


class ContactUsViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = ContactUsSerializer


class QuestionCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = QuestionCategory.objects.all()
    serializer_class = QuestionCategorySerializer


class UserStatsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MyUser.objects.all()
    serializer_class = UserStatsSerializer
