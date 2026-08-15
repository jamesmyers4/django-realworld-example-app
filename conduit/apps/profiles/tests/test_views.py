import pytest

from conduit.apps.core.tests.factories import UserFactory


@pytest.mark.django_db
class TestProfileRetrieve:
    def test_retrieve_profile_returns_profile_envelope(self, api_client):
        UserFactory(username='someuser')

        response = api_client.get('/api/profiles/someuser')

        assert response.status_code == 200
        body = response.json()
        assert body['profile']['username'] == 'someuser'
        assert body['profile']['following'] is False

    def test_retrieve_profile_does_not_require_authentication(self, api_client):
        UserFactory(username='someuser')
        response = api_client.get('/api/profiles/someuser')
        assert response.status_code == 200

    def test_retrieve_unknown_profile_returns_404(self, api_client):
        response = api_client.get('/api/profiles/nobody-here')
        assert response.status_code == 404


@pytest.mark.django_db
class TestProfileFollow:
    def test_follow_requires_authentication(self, api_client):
        UserFactory(username='someuser')
        response = api_client.post('/api/profiles/someuser/follow')
        assert response.status_code == 403

    def test_follow_returns_201_with_following_true(self, auth_client):
        UserFactory(username='someuser')

        response = auth_client.post('/api/profiles/someuser/follow')

        assert response.status_code == 201
        assert response.json()['profile']['following'] is True

    def test_unfollow_returns_200_with_following_false(self, auth_client):
        UserFactory(username='someuser')
        auth_client.post('/api/profiles/someuser/follow')

        response = auth_client.delete('/api/profiles/someuser/follow')

        assert response.status_code == 200
        assert response.json()['profile']['following'] is False

    def test_follow_unknown_profile_returns_404(self, auth_client):
        response = auth_client.post('/api/profiles/nobody-here/follow')
        assert response.status_code == 404
