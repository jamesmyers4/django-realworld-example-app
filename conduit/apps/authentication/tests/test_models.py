import time

import jwt
import pytest
from django.conf import settings
from django.db.utils import IntegrityError

from conduit.apps.authentication.models import User
from conduit.apps.core.tests.factories import UserFactory


@pytest.mark.django_db
class TestUserManager:
    def test_create_user_sets_password(self):
        user = User.objects.create_user(
            username='jane', email='jane@example.com', password='secret123'
        )
        assert user.check_password('secret123')

    def test_create_user_normalizes_email_domain(self):
        user = User.objects.create_user(
            username='jane', email='jane@EXAMPLE.com', password='secret123'
        )
        assert user.email == 'jane@example.com'

    def test_create_user_requires_username(self):
        with pytest.raises(TypeError):
            User.objects.create_user(
                username=None, email='jane@example.com', password='secret123'
            )

    def test_create_user_requires_email(self):
        with pytest.raises(TypeError):
            User.objects.create_user(
                username='jane', email=None, password='secret123'
            )

    def test_create_user_creates_related_profile_via_signal(self):
        user = User.objects.create_user(
            username='jane', email='jane@example.com', password='secret123'
        )
        assert user.profile is not None

    def test_create_superuser_sets_staff_and_superuser_flags(self):
        user = User.objects.create_superuser(
            username='admin', email='admin@example.com', password='secret123'
        )
        assert user.is_staff is True
        assert user.is_superuser is True

    def test_create_superuser_requires_password(self):
        with pytest.raises(TypeError):
            User.objects.create_superuser(
                username='admin', email='admin@example.com', password=None
            )

    def test_duplicate_username_raises_integrity_error(self):
        UserFactory(username='dupe')
        with pytest.raises(IntegrityError):
            UserFactory(username='dupe')

    def test_duplicate_email_raises_integrity_error(self):
        UserFactory(email='dupe@example.com')
        with pytest.raises(IntegrityError):
            UserFactory(email='dupe@example.com')


@pytest.mark.django_db
class TestJWTToken:
    def test_token_property_returns_decodable_jwt(self):
        user = UserFactory()
        payload = jwt.decode(user.token, settings.SECRET_KEY)
        assert payload['id'] == user.pk

    def test_token_expiry_is_approximately_60_days_out(self):
        user = UserFactory()
        payload = jwt.decode(user.token, settings.SECRET_KEY)

        sixty_days_seconds = 60 * 24 * 60 * 60
        expected_exp = int(time.time()) + sixty_days_seconds

        # Allow a few seconds of slack for the wall-clock time taken to
        # generate the token and run the assertion.
        assert abs(payload['exp'] - expected_exp) < 5

    def test_each_call_generates_a_token_valid_for_this_user(self):
        user = UserFactory()
        token_one = user.token
        token_two = user.token

        assert jwt.decode(token_one, settings.SECRET_KEY)['id'] == user.pk
        assert jwt.decode(token_two, settings.SECRET_KEY)['id'] == user.pk


@pytest.mark.django_db
class TestUserStringMethods:
    def test_str_returns_email(self):
        user = UserFactory(email='str-test@example.com')
        assert str(user) == 'str-test@example.com'

    def test_get_full_name_returns_username(self):
        user = UserFactory(username='fullnametest')
        assert user.get_full_name() == 'fullnametest'

    def test_get_short_name_returns_username(self):
        user = UserFactory(username='shortnametest')
        assert user.get_short_name() == 'shortnametest'
