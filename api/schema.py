import graphene

import api.queries.team


class Query(
    api.queries.team.Query,
    graphene.ObjectType,
):
    hello = graphene.String(default_value="Hi!")


schema = graphene.Schema(query=Query)
