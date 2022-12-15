from django.db import models
from django.db.models import Sum
from django.utils import timezone

from canvas.models.models import CanvasCourseRegistration
from canvas.services.goal import get_goal_stats
from course.models.models import DIFFICULTY_CHOICES, QuestionCategory
from course.services.question import get_solved_practice_questions_count


class Goal(models.Model):
    course_reg = models.ForeignKey(CanvasCourseRegistration, on_delete=models.CASCADE, related_name="goals")
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    claimed = models.BooleanField(default=False, blank=True)

    @property
    def is_finished(self):
        return timezone.now() > self.end_date

    @property
    def progress(self):
        return sum([goal_item.progress for goal_item in self.goal_items.all()])

    @property
    def number_of_questions(self):
        return self.goal_items.aggregate(Sum("number_of_questions"))["number_of_questions__sum"]

    @property
    def stats(self):
        return get_goal_stats(self)

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

    @property
    def progress(self):
        return get_solved_practice_questions_count(
            self.user.id, self.category_id, self.difficulty, self.goal.start_date, self.goal.end_date
        )

    @property
    def category_name(self):
        return self.category.full_name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
