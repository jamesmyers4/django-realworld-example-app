"""Phase 3 — invalid/expired/malformed JWT handling (TEST-PLAN.md).

Every case below returns 403, not 401 -- see CONTEXT.md's "API behavior
notes". DRF's `APIView.handle_exception` coerces both `NotAuthenticated`
and `AuthenticationFailed` down to 403 whenever `get_authenticate_header()`
returns falsy, and it's falsy here because `JWTAuthentication` doesn't
override `authenticate_header()`. That's true uniformly -- missing
credentials, a malformed token, an expired token, a token for a user that
no longer exists, and a deactivated user's token all hit the same code
path and all come back 403.
"""
import jwt
import pytest
from django.conf import settings

from conduit.apps.core.tests.factories import UserFactory


@pytest.mark.django_db
class TestInvalidOrMalformedJWT:
    def test_malformed_token_returns_403(self, api_client):
        api_client.credentials(HTTP_AUTHORIZATION='Token not-a-real-jwt')
        response = api_client.get('/api/user')
        assert response.status_code == 403

    def test_token_for_nonexistent_user_returns_403(self, api_client):
        token = jwt.encode(
            {'id': 999999, 'exp': 99999999999}, settings.SECRET_KEY,
            algorithm='HS256'
        ).decode('utf-8')

        api_client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        response = api_client.get('/api/user')
        assert response.status_code == 403

    def test_expired_token_returns_403(self, api_client):
        user = UserFactory()
        token = jwt.encode(
            {'id': user.pk, 'exp': 1}, settings.SECRET_KEY, algorithm='HS256'
        ).decode('utf-8')

        api_client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        response = api_client.get('/api/user')
        assert response.status_code == 403

    def test_wrong_auth_scheme_prefix_returns_403(self, api_client):
        user = UserFactory()
        api_client.credentials(HTTP_AUTHORIZATION='Bearer ' + user.token)
        response = api_client.get('/api/user')
        # `Bearer` isn't the expected `Token` prefix, so JWTAuthentication
        # returns None (declines to authenticate) rather than raising --
        # same end result (403) as every other case in this file, just a
        # different path to get there (permission denial vs. an explicit
        # AuthenticationFailed).
        assert response.status_code == 403

    def test_inactive_user_token_returns_403(self, api_client):
        user = UserFactory(is_active=False)
        api_client.credentials(HTTP_AUTHORIZATION='Token ' + user.token)
        response = api_client.get('/api/user')
        assert response.status_code == 403
