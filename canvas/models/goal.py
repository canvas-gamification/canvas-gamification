from django.db import models
from django.utils import timezone

from canvas.models.models import CanvasCourseRegistration
from course.models.models import DIFFICULTY_CHOICES, QuestionCategory
from course.services.question import get_solved_practice_questions_count


class Goal(models.Model):
    course_reg = models.ForeignKey(CanvasCourseRegistration, on_delete=models.CASCADE, related_name="goals")
    category = models.ForeignKey(QuestionCategory, on_delete=models.CASCADE, related_name="goals")
    difficulty = models.CharField(max_length=50, choices=DIFFICULTY_CHOICES, null=True, blank=True)
    initial_solved = models.IntegerField(blank=True)
    number_of_questions = models.IntegerField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    def get_initial_solved(self):
        return self.initial_solved if self.initial_solved is not None else 0

    @property
    def progress(self):
        return (
            get_solved_practice_questions_count(self.course_reg.user_id, self.category_id, self.difficulty)
            - self.get_initial_solved()
        )

    @property
    def is_finished(self):
        return timezone.now() > self.end_date

    def save(self, *args, **kwargs):
        if self.initial_solved is None:
            self.initial_solved = get_solved_practice_questions_count(
                self.course_reg.user_id, self.category_id, self.difficulty
            )
        if self.start_date is None:
            self.start_date = timezone.now()
        super().save(*args, **kwargs)
