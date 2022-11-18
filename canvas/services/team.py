from typing import Optional

from rest_framework.exceptions import PermissionDenied

from accounts.models import MyUser
from canvas.models.models import Event
from canvas.models.team import Team
from canvas.utils.utils import get_course_registration
import api.error_messages as ERROR_MESSAGES


def create_and_join_team(event: Event, user: MyUser, name: Optional[str]) -> Team:
    course_reg = get_course_registration(user, event.course)

    leave_team(event, user)
    team = Team()
    team.event = event
    team.name = name if name is not None else user.get_full_name() + "'s Team"
    team.save()
    team.course_registrations.set([course_reg])
    return team


def get_my_team(event: Event, user: MyUser) -> Team:
    course_reg = get_course_registration(user, event.course)
    team = event.team_set.filter(course_registrations=course_reg).all()

    if len(team) == 0:
        return create_and_join_team(event, user, None)

    return team.get()


def join_team(team: Team, user: MyUser):
    course_reg = get_course_registration(user, team.event.course)

    if not course_reg.is_verified:
        raise PermissionDenied(ERROR_MESSAGES.TEAM.NOT_REGISTERED)

    if team.is_private and not team.who_can_join.filter(id=course_reg.id).exists():
        raise PermissionDenied(ERROR_MESSAGES.TEAM.PRIVATE)

    if team.course_registrations.count() >= team.event.max_team_size:
        raise PermissionDenied(ERROR_MESSAGES.TEAM.FULL)

    leave_team(team.event, user)
    team.course_registrations.add(course_reg)


def leave_team(event: Event, user: MyUser):
    course_reg = get_course_registration(user, event.course)
    team = event.team_set.filter(course_registrations=course_reg).all()
    if len(team) == 0:
        return
    team = team.get()
    if team.course_registrations.count() == 1:
        team.delete()
    else:
        team.course_registrations.remove(course_reg)
