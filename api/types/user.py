from graphene_django import DjangoObjectType

from accounts.models import MyUser as UserModel


class User(DjangoObjectType):
    class Meta:
        model = UserModel
