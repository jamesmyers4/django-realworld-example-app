"""
Root-level pytest fixtures shared across every app's test suite.
"""
import pytest
from rest_framework.test import APIClient

from conduit.apps.core.tests.factories import UserFactory


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def create_user(db):
    def _create_user(**kwargs):
        return UserFactory(**kwargs)
    return _create_user


@pytest.fixture
def user(create_user):
    return create_user()


@pytest.fixture
def auth_client(api_client, user):
    """An APIClient already carrying a valid JWT for a freshly created user."""
    api_client.credentials(HTTP_AUTHORIZATION='Token ' + user.token)
    return api_client
