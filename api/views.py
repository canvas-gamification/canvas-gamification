# Create your views here.
from rest_framework import viewsets, mixins

from accounts.models import UserConsent, MyUser
from api.permissions import TeacherAccessPermission, UserConsentPermission
from api.serializers import QuestionSerializer, MultipleChoiceQuestionSerializer, \
    UserConsentSerializer, ContactUsSerializer, QuestionCategorySerializer, UserStatsSerializer, TokenValueSerializer
from course.models.models import Question, MultipleChoiceQuestion, QuestionCategory
from course.utils.utils import get_token_values


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


class TokenValueViewSet(viewsets.GenericViewSet,
                        mixins.UpdateModelMixin,
                        mixins.ListModelMixin,
                        mixins.RetrieveModelMixin):
    serializer_class = TokenValueSerializer
    permission_classes = [TeacherAccessPermission, ]

    def get_queryset(self):
        return get_token_values()


class UserStatsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MyUser.objects.all()
    serializer_class = UserStatsSerializer
