# Create your views here.
from django.utils import timezone
from django.db.models import Q
from rest_framework import viewsets, mixins

from accounts.models import UserConsent, MyUser
from api.permissions import TeacherAccessPermission, UserConsentPermission
from api.serializers import QuestionSerializer, MultipleChoiceQuestionSerializer, \
    UserConsentSerializer, ContactUsSerializer, QuestionCategorySerializer, UserStatsSerializer, CourseSerializer
from canvas.models import CanvasCourse
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


class CourseViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CourseSerializer

    def get_queryset(self):
        user = self.request.user
        # active = active courses, inactive = inactive courses, all = all courses
        status = self.request.query_params.get('status', 'all')
        # true = filter by if user is registered, false = no filtering on registration status
        registered = self.request.query_params.get('registered', False)

        if not user.is_authenticated:
            return CanvasCourse.objects.filter(visible_to_students=True).all()
        else:
            queryset = CanvasCourse.objects
            # if request comes from a teacher, return all the courses they instruct
            if user.is_teacher:
                queryset = queryset.filter(instructor=user)
            elif user.is_student:
                if status == 'active':
                    queryset = queryset.filter(allow_registration=False).filter(start_date__lte = timezone.now()).filter(end_date__gte=timezone.now())
                elif status == 'inactive':
                    # TODO: what is the inactive case?
                    # Q(allow_registration=True) |
                    queryset = queryset.filter(Q(start_date__gt=timezone.now()) | Q(
                        end_date__lt=timezone.now()))
                # if registered or status=='active':
                #     queryset = queryset.filter(is_registered=True)

            return queryset.all()