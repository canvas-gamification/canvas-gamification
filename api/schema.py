import graphene

import api.queries.team
from api.mutations.team import CreateTeamMutation


class Query(
    api.queries.team.Query,
    graphene.ObjectType,
):
    hello = graphene.String(default_value="Hi!")


class Mutation(
    graphene.ObjectType,
):
    create_team = CreateTeamMutation.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)
