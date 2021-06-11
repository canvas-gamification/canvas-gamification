from django.db import models

# Create your models here.
import base64
import json
import random
from datetime import datetime

from django.db import models
from django.utils.crypto import get_random_string
from djrichtextfield.models import RichTextField
from polymorphic.models import PolymorphicModel

from accounts.models import MyUser
from canvas.models import Event, CanvasCourse
from course.fields import JSONField
from course.grader.grader import MultipleChoiceGrader, JunitGrader
from course.utils.junit_xml import parse_junit_xml
from course.utils.utils import get_token_value, ensure_uqj, calculate_average_success
from course.utils.variables import render_text, generate_variables
from general.models import Action



class viewleaderBoard():
    isVisable =  models.BooleanField(default=True)
    leaderBoardId = models.AutoField(primary_key=True)
    student = models.ForeignKey(MyUser, on_delete=models.SET_NULL, null=True, blank=True)
    #tokens = models.ForeignKey(, on_delete = models.Set_Null, default = 0, null = False, blank= False)
