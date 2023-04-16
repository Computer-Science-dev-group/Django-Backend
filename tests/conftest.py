from pytest_factoryboy import register

from users import factory

register(factory.UserFactory)

