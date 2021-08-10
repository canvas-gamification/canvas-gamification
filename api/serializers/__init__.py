"""
NOTE: if serializer A imports serializer B, then A **must** be imported in this file after B
      failing to do this will lead to a cicurlar import error
"""

# Serializers that don't import any other serializers
from .utils import UpdateListSerializer

from .action import ActionsSerializer
from .contact_us import ContactUsSerializer
from .faq import FAQSerializer
from .question_category import QuestionCategorySerializer
from .token_value import TokenValueSerializer
from .user_consent import UserConsentSerializer
from .user_stats import UserStatsSerializer
from .list_user import UsersCountSerializers
from .token_use_option import TokenUseOptionSerializer
from .event import EventSerializer
from .change_password import ChangePasswordSerializer
from .reset_password import ResetPasswordSerializer
from .register import UserRegistrationSerializer
from .update_profile import UpdateProfileSerializer
from .list_course_user import UsersCourseCountSerializers
# Serializers that depend on other serializers
from .token_use import TokenUseSerializer
from .question import QuestionSerializer
from .java_question import JavaQuestionSerializer, JavaSubmissionSerializer
from .multiple_choice_question import MultipleChoiceQuestionSerializer, MultipleChoiceSubmissionSerializer
from .parsons_question import ParsonsQuestionSerializer, ParsonsSubmissionSerializer
from .uqj import UQJSerializer
from .canvas_course_registration import CanvasCourseRegistrationSerializer
from .canvas_course_unregistered import CanvasCourseUnRegisteredSerializer
from .course import CourseSerializer, CourseSerializerList
from .course_names import CourseNamesSerializer
