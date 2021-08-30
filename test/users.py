from accounts.models import MyUser


def add_user(username, email, password):
    return MyUser.objects.create_user(username, email, password)


def add_base_user():
    return add_user("test_user", "test@s202.ok.ubc.ca", "aaaaaaaa")
