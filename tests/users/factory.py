"""
Factory generation for all models related to the user model in UIA Django-Backend
"""

import factory
from django.contrib import auth

User = auth.get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    """
    Factory for Custom User model
    """

    class Meta:
        model = User

    email = factory.Sequence(lambda n: "test_email_%d@gmail.com" % n)
    password = factory.Sequence(lambda n: "test_user_password_%d" % n)

