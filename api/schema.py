import graphene

from api.types import Team
from canvas.models import Team as TeamModel


class Query(graphene.ObjectType):
    hello = graphene.String(default_value="Hi!")
    teams = graphene.List(Team)

    def resolve_teams(root, info):
        return TeamModel.objects.all()


schema = graphene.Schema(query=Query)
