from graphene_django.types import DjangoObjectType
from graphene import relay

from canvas.models import Team as TeamModel


class Team(DjangoObjectType):
    class Meta:
        model = TeamModel
        filter_fields = ('name',)
        interfaces = (relay.Node,)
