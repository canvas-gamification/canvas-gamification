from general.models.action import Action, ActionStatus, ActionVerb, ActionObjectType


def create_login_action(user):
    Action.create_action(
        actor=user,
        description='User logged in',
        token_change=0,
        status=ActionStatus.COMPLETE,
        verb=ActionVerb.LOGGED_IN,
        object_type=ActionObjectType.USER,
        object_id=user.id,
        data=None
    )


def create_logout_action(user):
    Action.create_action(
        actor=user,
        description='User logged out',
        token_change=0,
        status=ActionStatus.COMPLETE,
        verb=ActionVerb.LOGGED_OUT,
        object_type=ActionObjectType.USER,
        object_id=user.id,
        data=None
    )


def create_submission_action(submission):
    Action.create_action(
        actor=submission.user,
        description="User submitted a solution",
        token_change=0,
        status=ActionStatus.COMPLETE,
        verb=ActionVerb.SUBMITTED,
        object_type=ActionObjectType.SUBMISSION,
        object_id=submission.id,
        data={
            'answer': submission.answer,
        }
    )


def create_submission_evaluation_action(submission):
    Action.create_action(
        actor=submission.user,
        description="Submission was evaluated",
        token_change=submission.tokens_received,
        status=ActionStatus.COMPLETE,
        verb=ActionVerb.EVALUATED,
        object_type=ActionObjectType.SUBMISSION,
        object_id=submission.id,
        data={
            'answer': submission.answer,
            'grade': submission.grade,
            'is_correct': submission.is_correct,
            'is_partially_correct': submission.is_partially_correct,
            'status': submission.status,
        }
    )
