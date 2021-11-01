from graphene_django.types import DjangoObjectType

from canvas.models import Team as TeamModel


class Team(DjangoObjectType):
    class Meta:
        model = TeamModel
