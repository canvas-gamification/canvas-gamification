import graphene

from api.types import Team
from canvas.models import Team as TeamModel


class CreateTeamMutation(graphene.Mutation):
    class Arguments:
        event_id = graphene.ID(required=True)
        name = graphene.String(required=True)

    team = graphene.Field(Team)

    @classmethod
    def mutate(cls, root, info, event_id, name):
        team = TeamModel.create(event_id=event_id, name=name)
        return CreateTeamMutation(team=team)
