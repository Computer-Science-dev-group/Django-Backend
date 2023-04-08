"""
Factory generation for all models in UIA Django-Backend
"""

import factory
from django.contrib import auth

User = auth.get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    """
    Factory for User
    """

    class Meta:
        model = User

    username = factory.Sequence(lambda n: "test_user_%d" % n)
    password = factory.Sequence(lambda n: "test_user_password_%d" % n)
