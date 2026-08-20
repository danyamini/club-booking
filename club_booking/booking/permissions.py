def is_mechanic(user):
    return user.is_authenticated and (user.is_superuser or user.groups.filter(name='Mechanic').exists())
def is_operator(user):
    return user.is_authenticated and (user.is_superuser or user.groups.filter(name='Operator').exists())