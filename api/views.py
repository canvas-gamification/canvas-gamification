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
    """
    Optional Parameters
    ?status: 'active'|'inactive'|'all' => retrieve specific statuses of courses
    ?registered: boolean => if true, filter retrieved courses by if user is currently registered in them
    """
    serializer_class = CourseSerializer

    def get_queryset(self):
        user = self.request.user
        status = self.request.query_params.get('status', 'all')
        registered = self.request.query_params.get('registered', False)

        if not user.is_authenticated:
            return CanvasCourse.objects.filter(visible_to_students=True).all()
        else:
            queryset = CanvasCourse.objects
            if user.is_teacher:
                queryset = queryset.filter(instructor=user)
            elif user.is_student:
                if status == 'active':
                    # TODO: are courses still active if they do not allow registration because the course has begun?
                    queryset = queryset.filter(allow_registration=True).filter(start_date__lte=timezone.now()) \
                        .filter(end_date__gte=timezone.now())
                elif status == 'inactive':
                    # TODO: what is the inactive case?
                    # Q(allow_registration=True) |
                    queryset = queryset.filter(Q(start_date__gt=timezone.now()) | Q(end_date__lt=timezone.now()))
                if registered or status == 'active':
                    registered_ids = [registration.course.id
                                      for registration in user.canvascourseregistration_set.all()]
                    queryset = queryset.filter(pk__in=registered_ids)

            return queryset.all()
