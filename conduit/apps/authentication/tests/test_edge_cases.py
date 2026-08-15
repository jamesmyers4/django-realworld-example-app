"""Phase 4 — edge / negative / boundary cases (TEST-PLAN.md): duplicate
username/email on register, missing required fields, malformed JSON body.
"""
import pytest

from conduit.apps.core.tests.factories import UserFactory


@pytest.mark.django_db
class TestRegistrationEdgeCases:
    def test_duplicate_username_on_register_returns_400(self, api_client):
        UserFactory(username='taken')

        response = api_client.post('/api/users', {
            'user': {
                'username': 'taken',
                'email': 'different@example.com',
                'password': 'longenough123',
            }
        }, format='json')

        assert response.status_code == 400

    def test_duplicate_email_on_register_returns_400(self, api_client):
        UserFactory(email='taken@example.com')

        response = api_client.post('/api/users', {
            'user': {
                'username': 'different',
                'email': 'taken@example.com',
                'password': 'longenough123',
            }
        }, format='json')

        assert response.status_code == 400

    def test_register_with_no_user_key_returns_400(self, api_client):
        # RegistrationAPIView.post does request.data.get('user', {}) --
        # an empty dict fails validation on every required field rather
        # than raising a KeyError.
        response = api_client.post('/api/users', {}, format='json')
        assert response.status_code == 400

    def test_register_with_malformed_json_body_returns_400(self, api_client):
        response = api_client.post(
            '/api/users', data='{not valid json', content_type='application/json'
        )
        assert response.status_code == 400


@pytest.mark.django_db
class TestUserUpdateEdgeCases:
    def test_update_with_no_user_key_leaves_fields_unchanged(self, auth_client, user):
        response = auth_client.put('/api/user', {}, format='json')

        assert response.status_code == 200
        assert response.json()['user']['username'] == user.username
