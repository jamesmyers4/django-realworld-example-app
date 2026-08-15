import pytest

from conduit.apps.core.tests.factories import UserFactory


@pytest.mark.django_db
class TestRegistration:
    def test_register_returns_201_with_user_envelope(self, api_client):
        response = api_client.post('/api/users', {
            'user': {
                'username': 'newbie',
                'email': 'newbie@example.com',
                'password': 'longenough123',
            }
        }, format='json')

        assert response.status_code == 201
        body = response.json()
        assert body['user']['username'] == 'newbie'
        assert body['user']['email'] == 'newbie@example.com'
        assert 'token' in body['user']
        assert 'password' not in body['user']

    def test_register_missing_password_returns_400(self, api_client):
        response = api_client.post('/api/users', {
            'user': {
                'username': 'newbie',
                'email': 'newbie@example.com',
            }
        }, format='json')

        assert response.status_code == 400
        assert 'errors' in response.json()


@pytest.mark.django_db
class TestLogin:
    def test_login_with_valid_credentials_returns_200_with_token(self, api_client):
        UserFactory(
            username='loginuser', email='login@example.com',
            password='correcthorse123'
        )

        response = api_client.post('/api/users/login', {
            'user': {'email': 'login@example.com', 'password': 'correcthorse123'}
        }, format='json')

        assert response.status_code == 200
        body = response.json()
        assert body['user']['email'] == 'login@example.com'
        assert 'token' in body['user']

    def test_login_with_wrong_password_returns_400(self, api_client):
        UserFactory(email='login@example.com', password='correcthorse123')

        response = api_client.post('/api/users/login', {
            'user': {'email': 'login@example.com', 'password': 'wrongpassword'}
        }, format='json')

        assert response.status_code == 400


@pytest.mark.django_db
class TestCurrentUser:
    def test_get_current_user_requires_authentication(self, api_client):
        response = api_client.get('/api/user')
        assert response.status_code == 403

    def test_get_current_user_returns_user_envelope(self, auth_client):
        response = auth_client.get('/api/user')

        assert response.status_code == 200
        body = response.json()
        assert 'username' in body['user']
        assert 'email' in body['user']
        assert 'bio' in body['user']
        assert 'image' in body['user']

    def test_update_current_user_bio(self, auth_client):
        response = auth_client.put('/api/user', {
            'user': {'bio': 'A new bio'}
        }, format='json')

        assert response.status_code == 200
        assert response.json()['user']['bio'] == 'A new bio'

    def test_update_current_user_persists(self, auth_client, user):
        auth_client.put('/api/user', {
            'user': {'username': 'renamed'}
        }, format='json')

        user.refresh_from_db()
        assert user.username == 'renamed'
