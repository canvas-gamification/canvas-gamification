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
    userId = models.ForeignKey(MyUser, on_delete = models.SET_NULL, null= True, blank= False)
    courseId = models.ForeignKey(CanvasCourse,  related_name='%(class)s_requests_created' ,on_delete= models.SET_NULL, null=True, blank=False)
    total_tokens_received = models.ForeignKey(CanvasCourse, on_delete = models.SET(0))
    leaderBoardId = models.AutoField(primary_key=True)
   
    def __str__(self):
        if self.parent is None:
            return self.name
        else:
            return "{} :: {}".format(self.parent, self.name)

    @property
    def is_leader_board(self):
        """
        Is the user a member of staff?
        """
        return self.is_leader_board       
