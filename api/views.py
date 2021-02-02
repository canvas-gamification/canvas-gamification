# Create your views here.
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

    """
    if the user is not authenticated
        return all the courses visible to students
        and the is_registered attribute to false (manually set? in serializer?)
    if its authenticated and is teacher
        return all of the courses
    if a student is authenticated
        return all the courses with the correct value for is_registered (in serializer)
    
    also you should be able to filter the courses by is_registered
    and you might also need to filter by is_active
        which means the user should be registered and the course should be "In Session"
    """

    def get_queryset(self):
        COURSE_ACTIVE = 'In Session'
        user = self.request.user
        # true = active courses, false = all courses
        active = self.request.query_params.get('active', False)
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
                if active:
                    queryset = queryset.filter(status=COURSE_ACTIVE)
                if registered or active:
                    queryset = queryset.filter(is_registered=True)

            return queryset.all()
