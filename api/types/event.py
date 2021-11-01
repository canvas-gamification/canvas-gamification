from graphene import relay
from graphene_django import DjangoObjectType

from canvas.models import Event as EventModel


class Event(DjangoObjectType):
    class Meta:
        model = EventModel
        interfaces = (relay.Node,)
