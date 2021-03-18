"""
NOTE: if serializer A imports serializer B, then A **must** be imported in this file after B
      failing to do this will lead to a cicurlar import error
"""

# Serializers that don't import any other serializers
from .action import ActionsSerializer
from .contact_us import ContactUsSerializer
from .faq import FAQSerializer
from .java_question import JavaQuestionSerializer
from .multiple_choice_question import MultipleChoiceQuestionSerializer
from .parsons_question import ParsonsQuestionSerializer
from .question_category import QuestionCategorySerializer
from .token_value import TokenValueSerializer
from .user_consent import UserConsentSerializer
from .user_stats import UserStatsSerializer
from .token_use_option import TokenUseOptionSerializer
from .event import EventSerializer

# Serializers that depend on other serializers
from .token_use import TokenUseSerializer
from .question import QuestionSerializer
from .uqj import UQJSerializer
from .canvas_course_registration import CanvasCourseRegistrationSerializer
from .course import CourseSerializer
