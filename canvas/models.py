from django.db import models
import canvasapi
from accounts.models import MyUser


class CanvasCourse(models.Model):
    name = models.CharField(max_length=500)
    url = models.URLField()
    course_id = models.IntegerField()
    token = models.CharField(max_length=500)
    
    allow_registration = models.BooleanField(default=False)
    visible_to_students = models.BooleanField(default=False)
    start_date = models.DateTimeField(null=True)
    end_date = models.DateTimeField(null=True)

    verification_assignment_group_name = models.CharField(max_length=100)
    verification_assignment_group_id = models.IntegerField(null=True, blank=True)
    verification_assignment_name = models.CharField(max_length=100)
    verification_assignment_id = models.IntegerField(null=True, blank=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._canvas = None
        self._course = None

    @property
    def canvas(self):
        if not self._canvas:
            self._canvas = canvasapi.Canvas(self.url, self.token)
        return self._canvas

    @property
    def course(self):
        if not self._course:
            self._course = self.canvas.get_course(self.course_id)
        return self._course

    @property
    def verification_assignment(self):
        if not self._verification_assignment:
            self._verification_assignment = self.course.get_assignment(self.verification_assignment_id)
        return self._verification_assignment

    def create_verification_assignment_group(self):
        if self.verification_assignment_group_id:
            return
        ag = self.course.create_assignment_group(name=self.verification_assignment_group_name)
        self.verification_assignment_group_id = ag.id

    def create_verification_assignment(self):
        if self.verification_assignment_id:
            return

        a = self.course.create_assignment({
            'points_possible': 100,
            'name': self.verification_assignment_name,
            'assignment_group_id': self.verification_assignment_group_id,
            'published': True
        })
        self.verification_assignment_id = a.id

    def save(self, *args, **kwargs):
        self.create_verification_assignment_group()
        self.create_verification_assignment()
        super().save(*args, **kwargs)


def random_verification_code():
    import random
    return random.randint(1, 100)


class CanvasCourseRegistration(models.Model):
    course = models.ForeignKey(CanvasCourse, on_delete=models.CASCADE, db_index=True)
    user = models.ForeignKey(MyUser, on_delete=models.CASCADE, db_index=True)

    canvas_user_id = models.IntegerField(null=True, blank=True)
    is_verified = models.BooleanField(default=False, db_index=True)
    is_blocked = models.BooleanField(default=False, db_index=True)

    verification_code = models.IntegerField(default=random_verification_code)
    verification_attempts = models.IntegerField(default=3)

    @property
    def canvas_user(self):
        if self.canvas_user_id is None:
            return None
        if not self._canvas_user:
            self._canvas_user = self.course.course.get_user(self.canvas_user_id) 
        return self._canvas_user

    def send_verification_code(self):
        self.course.verification_assignment.submissions_bulk_update(grade_data={
            self.canvas_user_id: {
                'posted_grade': self.verification_code,
            }
        })

    def check_verification_code(self, code):
        if self.is_blocked:
            return False
        if self.verification_code == code:
            self.is_verified = True
            self.save()
            return True
        self.verification_attempts -= 1
        if self.verification_attempts <= 0:
            self.is_blocked = True
        self.save()

        return False
