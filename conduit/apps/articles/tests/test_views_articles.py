import pytest

from conduit.apps.core.tests.factories import ArticleFactory, TagFactory, UserFactory


@pytest.mark.django_db
class TestArticleCreate:
    def test_create_requires_authentication(self, api_client):
        response = api_client.post('/api/articles', {
            'article': {
                'title': 'A Title', 'description': 'Desc', 'body': 'Body',
            }
        }, format='json')
        assert response.status_code == 403

    def test_create_returns_201_with_article_envelope(self, auth_client):
        response = auth_client.post('/api/articles', {
            'article': {
                'title': 'A Title', 'description': 'Desc', 'body': 'Body',
            }
        }, format='json')

        assert response.status_code == 201
        body = response.json()['article']
        assert body['title'] == 'A Title'
        assert body['slug']
        assert body['favorited'] is False
        assert body['favoritesCount'] == 0

    def test_create_sets_author_to_requesting_user(self, auth_client, user):
        response = auth_client.post('/api/articles', {
            'article': {
                'title': 'A Title', 'description': 'Desc', 'body': 'Body',
            }
        }, format='json')

        assert response.json()['article']['author']['username'] == user.username

    def test_create_with_tag_list_creates_tags(self, auth_client):
        response = auth_client.post('/api/articles', {
            'article': {
                'title': 'A Title', 'description': 'Desc', 'body': 'Body',
                'tagList': ['django', 'testing'],
            }
        }, format='json')

        assert response.status_code == 201
        assert set(response.json()['article']['tagList']) == {'django', 'testing'}

    def test_create_missing_title_returns_400(self, auth_client):
        response = auth_client.post('/api/articles', {
            'article': {'description': 'Desc', 'body': 'Body'}
        }, format='json')
        assert response.status_code == 400


@pytest.mark.django_db
class TestArticleRetrieve:
    def test_retrieve_by_slug_returns_article_envelope(self, api_client):
        article = ArticleFactory(title='Findable', slug='findable')

        response = api_client.get('/api/articles/findable')

        assert response.status_code == 200
        assert response.json()['article']['title'] == 'Findable'

    def test_retrieve_unknown_slug_returns_404(self, api_client):
        response = api_client.get('/api/articles/does-not-exist')
        assert response.status_code == 404


@pytest.mark.django_db
class TestArticleUpdate:
    def test_update_requires_authentication(self, api_client):
        article = ArticleFactory(slug='updatable')
        response = api_client.put('/api/articles/updatable', {
            'article': {'title': 'New Title'}
        }, format='json')
        assert response.status_code == 403

    def test_update_by_author_changes_title(self, auth_client, user):
        article = ArticleFactory(slug='updatable', author=user.profile)

        response = auth_client.put('/api/articles/updatable', {
            'article': {'title': 'New Title'}
        }, format='json')

        assert response.status_code == 200
        assert response.json()['article']['title'] == 'New Title'

    def test_update_unknown_slug_returns_404(self, auth_client):
        response = auth_client.put('/api/articles/does-not-exist', {
            'article': {'title': 'New Title'}
        }, format='json')
        assert response.status_code == 404


@pytest.mark.django_db
class TestArticleList:
    def test_list_returns_articles_envelope_with_count(self, api_client):
        ArticleFactory.create_batch(3)

        response = api_client.get('/api/articles')

        assert response.status_code == 200
        body = response.json()
        assert len(body['articles']) == 3
        assert body['articlesCount'] == 3

    def test_list_filters_by_author(self, api_client):
        alice = UserFactory(username='alice')
        bob = UserFactory(username='bob')
        ArticleFactory(author=alice.profile)
        ArticleFactory(author=bob.profile)

        response = api_client.get('/api/articles?author=alice')

        body = response.json()
        assert body['articlesCount'] == 1
        assert body['articles'][0]['author']['username'] == 'alice'

    def test_list_filters_by_tag(self, api_client):
        tagged = ArticleFactory()
        tagged.tags.add(TagFactory(tag='python', slug='python'))
        ArticleFactory()

        response = api_client.get('/api/articles?tag=python')

        body = response.json()
        assert body['articlesCount'] == 1
        assert body['articles'][0]['slug'] == tagged.slug

    def test_list_filters_by_favorited(self, api_client):
        favoriter = UserFactory()
        favorited_article = ArticleFactory()
        favoriter.profile.favorite(favorited_article)
        ArticleFactory()

        response = api_client.get(
            '/api/articles?favorited=%s' % favoriter.username
        )

        body = response.json()
        assert body['articlesCount'] == 1
        assert body['articles'][0]['slug'] == favorited_article.slug

    def test_list_respects_limit(self, api_client):
        ArticleFactory.create_batch(5)

        response = api_client.get('/api/articles?limit=2')

        assert len(response.json()['articles']) == 2
        assert response.json()['articlesCount'] == 5

    def test_list_respects_offset(self, api_client):
        ArticleFactory.create_batch(5)

        response = api_client.get('/api/articles?limit=2&offset=4')

        assert len(response.json()['articles']) == 1
