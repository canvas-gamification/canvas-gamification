from django.db import models
import jsonfield

from accounts.models import MyUser


class ActionStatus:
    COMPLETE = "Complete"
    PENDING = "Pending"


class ActionVerb:
    CLICKED = "Clicked"
    COMPLETED = "Completed"
    CREATED = "Created"
    DELETED = "Deleted"
    DELIVERED = "Delivered"
    DUPLICATED = "Duplicated"
    EDITED = "Edited"
    EVALUATED = "Evaluated"
    LOGGED_IN = "Logged In"
    LOGGED_OUT = "Logged Out"
    OPENED = "Opened"
    READ = "Read"
    REGISTERED = "Registered"
    SENT = "Sent"
    SKIPPED = "Skipped"
    SOLVED = "Solved"
    STARTED = "Started"
    SUBMITTED = "Submitted"
    UNREAD = "Unread"
    UPDATED = "Updated"
    USED = "Used"
    JOINED = "Joined"


class ActionObjectType:
    BUTTON = "Button"
    COURSE = "Course"
    COURSE_REGISTRATION = "Course Registration"
    EVENT = "Event"
    GOAL = "Goal"
    GOAL_ITEM = "Goal Item"
    QUESTION = "Question"
    SUBMISSION = "Submission"
    USER = "User"
    TEAM = "Team"


ACTION_STATUS_CHOICES = [
    (ActionStatus.COMPLETE, ActionStatus.COMPLETE),
    (ActionStatus.PENDING, ActionStatus.PENDING),
]

ACTION_VERB_CHOICES = [
    (ActionVerb.CLICKED, ActionVerb.CLICKED),
    (ActionVerb.COMPLETED, ActionVerb.COMPLETED),
    (ActionVerb.CREATED, ActionVerb.CREATED),
    (ActionVerb.DELETED, ActionVerb.DELETED),
    (ActionVerb.DELIVERED, ActionVerb.DELIVERED),
    (ActionVerb.DUPLICATED, ActionVerb.DUPLICATED),
    (ActionVerb.EDITED, ActionVerb.EDITED),
    (ActionVerb.EVALUATED, ActionVerb.EVALUATED),
    (ActionVerb.LOGGED_IN, ActionVerb.LOGGED_IN),
    (ActionVerb.LOGGED_OUT, ActionVerb.LOGGED_OUT),
    (ActionVerb.OPENED, ActionVerb.OPENED),
    (ActionVerb.READ, ActionVerb.READ),
    (ActionVerb.REGISTERED, ActionVerb.REGISTERED),
    (ActionVerb.SENT, ActionVerb.SENT),
    (ActionVerb.SKIPPED, ActionVerb.SKIPPED),
    (ActionVerb.SOLVED, ActionVerb.SOLVED),
    (ActionVerb.STARTED, ActionVerb.STARTED),
    (ActionVerb.SUBMITTED, ActionVerb.SUBMITTED),
    (ActionVerb.UNREAD, ActionVerb.UNREAD),
    (ActionVerb.UPDATED, ActionVerb.UPDATED),
    (ActionVerb.USED, ActionVerb.USED),
    (ActionVerb.JOINED, ActionVerb.JOINED),
]

OBJECT_TYPE_CHOICES = [
    (ActionObjectType.BUTTON, ActionObjectType.BUTTON),
    (ActionObjectType.COURSE, ActionObjectType.COURSE),
    (ActionObjectType.COURSE_REGISTRATION, ActionObjectType.COURSE_REGISTRATION),
    (ActionObjectType.EVENT, ActionObjectType.EVENT),
    (ActionObjectType.GOAL, ActionObjectType.GOAL),
    (ActionObjectType.GOAL_ITEM, ActionObjectType.GOAL_ITEM),
    (ActionObjectType.QUESTION, ActionObjectType.QUESTION),
    (ActionObjectType.SUBMISSION, ActionObjectType.SUBMISSION),
    (ActionObjectType.USER, ActionObjectType.USER),
    (ActionObjectType.TEAM, ActionObjectType.TEAM),
]


class Action(models.Model):
    time_created = models.DateTimeField(auto_now_add=True)
    time_modified = models.DateTimeField(auto_now=True)

    actor = models.ForeignKey(MyUser, related_name="actions", on_delete=models.CASCADE)
    description = models.CharField(max_length=500)
    token_change = models.FloatField(default=0)
    status = models.CharField(max_length=100, choices=ACTION_STATUS_CHOICES)
    verb = models.CharField(max_length=100, choices=ACTION_VERB_CHOICES)
    object_type = models.CharField(max_length=100, choices=OBJECT_TYPE_CHOICES, null=True)
    object_id = models.IntegerField(null=True)
    data = jsonfield.JSONField(null=True)

    @classmethod
    def create_action(
        cls,
        actor,
        description,
        token_change,
        status,
        verb,
        object_type=None,
        object_id=None,
        data=None,
    ):
        action = Action(
            actor=actor,
            description=description,
            token_change=token_change,
            status=status,
            verb=verb,
            object_type=object_type,
            object_id=object_id,
            data=data,
        )
        action.save()
