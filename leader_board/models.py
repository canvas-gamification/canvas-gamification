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


class Leader_Board(models.Model):
    name = models.TextField()
    is_visible = models.BooleanField(default=False)
    assigned_course = models.ForeignKey(CanvasCourse, on_delete=models.DO_NOTHING)
    created_by = models.ForeignKey(MyUser, on_delete=models.DO_NOTHING)

    def __str__(self):
        return self.name
class LeaderBoardAssignedStudents(models.Model):
    student = models.ForeignKey(MyUser, on_delete=models.DO_NOTHING)
    leader_board = models.ForeignKey(Leader_Board, on_delete=models.DO_NOTHING)
    MyUser.tokens =models.ForeignKey(MyUser, on_delete = models.DO_NOTHING)
    
    def __str__(self):
        return self.leader_board.assigned_course.name
