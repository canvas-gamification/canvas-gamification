from django.db import models
import jsonfield

from accounts.models import MyUser


class ActionStatus:
    COMPLETE = 'Complete'
    PENDING = 'Pending'


class ActionVerb:
    CREATED = 'Created'
    COMPLETED = 'Completed'
    OPENED = 'Opened'
    DELETED = 'Deleted'
    DELIVERED = 'Delivered'
    READ = 'Read'
    SOLVED = 'Solved'
    SUBMITTED = 'Submitted'
    SENT = 'Sent'
    STARTED = 'Started'
    USED = 'Used'
    REGISTERED = 'Registered'
    EDITED = 'Edited'
    UNREAD = 'Unread'
    SKIPPED = 'Skipped'
    LOGGED_IN = 'Logged In'
    LOGGED_OUT = 'Logged Out'
    EVALUATED = 'Evaluated'
    UPDATED = 'Updated'
    DUPLICATED = 'Duplicated'


class ActionObjectType:
    QUESTION = 'Question'
    USER = 'User'
    SUBMISSION = 'Submission'
    COURSE = 'Course'
    EVENT = 'Event'
    COURSE_REGISTRATION = 'Course Registration'


ACTION_STATUS_CHOICES = [
    (ActionStatus.COMPLETE, ActionStatus.COMPLETE),
    (ActionStatus.PENDING, ActionStatus.PENDING),
]

ACTION_VERB_CHOICES = [
    (ActionVerb.CREATED, ActionVerb.CREATED),
    (ActionVerb.COMPLETED, ActionVerb.COMPLETED),
    (ActionVerb.OPENED, ActionVerb.OPENED),
    (ActionVerb.DELETED, ActionVerb.DELETED),
    (ActionVerb.DELIVERED, ActionVerb.DELIVERED),
    (ActionVerb.READ, ActionVerb.READ),
    (ActionVerb.SOLVED, ActionVerb.SOLVED),
    (ActionVerb.SUBMITTED, ActionVerb.SUBMITTED),
    (ActionVerb.SENT, ActionVerb.SENT),
    (ActionVerb.STARTED, ActionVerb.STARTED),
    (ActionVerb.USED, ActionVerb.USED),
    (ActionVerb.REGISTERED, ActionVerb.REGISTERED),
    (ActionVerb.EDITED, ActionVerb.EDITED),
    (ActionVerb.UNREAD, ActionVerb.UNREAD),
    (ActionVerb.SKIPPED, ActionVerb.SKIPPED),
    (ActionVerb.LOGGED_IN, ActionVerb.LOGGED_IN),
    (ActionVerb.LOGGED_OUT, ActionVerb.LOGGED_OUT),
    (ActionVerb.EVALUATED, ActionVerb.EVALUATED),
    (ActionVerb.UPDATED, ActionVerb.UPDATED),
    (ActionVerb.DUPLICATED, ActionVerb.DUPLICATED)
]

OBJECT_TYPE_CHOICES = [
    (ActionObjectType.QUESTION, ActionObjectType.QUESTION),
    (ActionObjectType.USER, ActionObjectType.USER),
    (ActionObjectType.SUBMISSION, ActionObjectType.SUBMISSION),
    (ActionObjectType.COURSE, ActionObjectType.COURSE),
    (ActionObjectType.EVENT, ActionObjectType.EVENT),
    (ActionObjectType.COURSE_REGISTRATION, ActionObjectType.COURSE_REGISTRATION),
]


class Action(models.Model):
    time_created = models.DateTimeField(auto_now_add=True)
    time_modified = models.DateTimeField(auto_now=True)

    actor = models.ForeignKey(MyUser, related_name='actions', on_delete=models.CASCADE)
    description = models.CharField(max_length=500)
    token_change = models.FloatField(default=0)
    status = models.CharField(max_length=100, choices=ACTION_STATUS_CHOICES)
    verb = models.CharField(max_length=100, choices=ACTION_VERB_CHOICES)
    object_type = models.CharField(max_length=100, choices=OBJECT_TYPE_CHOICES, null=True)
    object_id = models.IntegerField(null=True)
    data = jsonfield.JSONField(null=True)

    @classmethod
    def create_action(cls, actor, description, token_change, status, verb, object_type=None, object_id=None, data=None):
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
