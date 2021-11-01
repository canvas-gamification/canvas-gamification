import graphene

from api.types import Team
from graphene import relay
from graphene_django.filter import DjangoFilterConnectionField


class Query(graphene.ObjectType):
    team = relay.Node.Field(Team)
    teams = DjangoFilterConnectionField(Team)