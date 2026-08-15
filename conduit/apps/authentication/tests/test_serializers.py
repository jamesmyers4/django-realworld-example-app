import pytest

from conduit.apps.authentication.serializers import (
    LoginSerializer, RegistrationSerializer
)
from conduit.apps.core.tests.factories import UserFactory


@pytest.mark.django_db
class TestRegistrationSerializer:
    def test_valid_payload_is_valid(self):
        serializer = RegistrationSerializer(data={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'longenough123',
        })
        assert serializer.is_valid() is True

    def test_missing_username_is_invalid(self):
        serializer = RegistrationSerializer(data={
            'email': 'newuser@example.com',
            'password': 'longenough123',
        })
        assert serializer.is_valid() is False
        assert 'username' in serializer.errors

    def test_missing_email_is_invalid(self):
        serializer = RegistrationSerializer(data={
            'username': 'newuser',
            'password': 'longenough123',
        })
        assert serializer.is_valid() is False
        assert 'email' in serializer.errors

    def test_missing_password_is_invalid(self):
        serializer = RegistrationSerializer(data={
            'username': 'newuser',
            'email': 'newuser@example.com',
        })
        assert serializer.is_valid() is False
        assert 'password' in serializer.errors

    def test_password_shorter_than_minimum_is_invalid(self):
        serializer = RegistrationSerializer(data={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'short',
        })
        assert serializer.is_valid() is False
        assert 'password' in serializer.errors

    def test_duplicate_username_is_invalid(self):
        UserFactory(username='taken')
        serializer = RegistrationSerializer(data={
            'username': 'taken',
            'email': 'someoneelse@example.com',
            'password': 'longenough123',
        })
        assert serializer.is_valid() is False
        assert 'username' in serializer.errors

    def test_duplicate_email_is_invalid(self):
        UserFactory(email='taken@example.com')
        serializer = RegistrationSerializer(data={
            'username': 'someoneelse',
            'email': 'taken@example.com',
            'password': 'longenough123',
        })
        assert serializer.is_valid() is False
        assert 'email' in serializer.errors

    def test_token_field_is_read_only(self):
        serializer = RegistrationSerializer(data={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'longenough123',
            'token': 'client-supplied-token-should-be-ignored',
        })
        assert serializer.is_valid() is True
        assert 'token' not in serializer.validated_data


@pytest.mark.django_db
class TestLoginSerializer:
    def test_valid_credentials_returns_email_username_and_token(self):
        UserFactory(
            username='loginuser', email='login@example.com',
            password='correcthorse123'
        )
        serializer = LoginSerializer(data={
            'email': 'login@example.com',
            'password': 'correcthorse123',
        })
        assert serializer.is_valid() is True
        assert serializer.validated_data['username'] == 'loginuser'

    def test_missing_email_is_invalid(self):
        serializer = LoginSerializer(data={'password': 'whatever123'})
        assert serializer.is_valid() is False

    def test_missing_password_is_invalid(self):
        serializer = LoginSerializer(data={'email': 'login@example.com'})
        assert serializer.is_valid() is False

    def test_wrong_password_is_invalid(self):
        UserFactory(email='login@example.com', password='correcthorse123')
        serializer = LoginSerializer(data={
            'email': 'login@example.com',
            'password': 'wrongpassword',
        })
        assert serializer.is_valid() is False

    def test_unknown_email_is_invalid(self):
        serializer = LoginSerializer(data={
            'email': 'nobody@example.com',
            'password': 'whatever123',
        })
        assert serializer.is_valid() is False

    def test_inactive_user_is_invalid(self):
        UserFactory(
            email='inactive@example.com', password='correcthorse123',
            is_active=False,
        )
        serializer = LoginSerializer(data={
            'email': 'inactive@example.com',
            'password': 'correcthorse123',
        })
        assert serializer.is_valid() is False
