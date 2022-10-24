from django.db import models
from django.db.models import Sum
from django.utils import timezone

from canvas.models.models import CanvasCourseRegistration
from course.models.models import DIFFICULTY_CHOICES, QuestionCategory
from course.services.question import get_solved_practice_questions_count


class Goal(models.Model):
    course_reg = models.ForeignKey(CanvasCourseRegistration, on_delete=models.CASCADE, related_name="goals")
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    @property
    def is_finished(self):
        return timezone.now() > self.end_date

    @property
    def progress(self):
        return sum([goal_item.progress for goal_item in self.goal_items.all()])

    @property
    def number_of_questions(self):
        return self.goal_items.aggregate(Sum("number_of_questions"))["number_of_questions__sum"]

    def save(self, *args, **kwargs):
        if self.start_date is None:
            self.start_date = timezone.now()
        super().save(*args, **kwargs)


class GoalItem(models.Model):
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE, related_name="goal_items")
    category = models.ForeignKey(QuestionCategory, on_delete=models.CASCADE, related_name="goal_items")
    difficulty = models.CharField(max_length=50, choices=DIFFICULTY_CHOICES, null=True, blank=True)
    initial_solved = models.IntegerField(blank=True)
    number_of_questions = models.IntegerField()

    @property
    def user(self):
        return self.goal.course_reg.user

    def get_initial_solved(self):
        return self.initial_solved if self.initial_solved is not None else 0

    @property
    def progress(self):
        return (
            get_solved_practice_questions_count(self.user.id, self.category_id, self.difficulty)
            - self.get_initial_solved()
        )

    def save(self, *args, **kwargs):
        if self.initial_solved is None:
            self.initial_solved = get_solved_practice_questions_count(self.user.id, self.category_id, self.difficulty)
        super().save(*args, **kwargs)
