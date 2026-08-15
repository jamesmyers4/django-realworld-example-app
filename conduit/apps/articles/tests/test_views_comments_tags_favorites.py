import pytest

from conduit.apps.core.tests.factories import ArticleFactory, CommentFactory, TagFactory


@pytest.mark.django_db
class TestCommentCreate:
    def test_create_requires_authentication(self, api_client):
        article = ArticleFactory(slug='commentable')
        response = api_client.post('/api/articles/commentable/comments', {
            'comment': {'body': 'Nice article'}
        }, format='json')
        assert response.status_code == 403

    def test_create_returns_201_with_comment_envelope(self, auth_client):
        ArticleFactory(slug='commentable')

        response = auth_client.post('/api/articles/commentable/comments', {
            'comment': {'body': 'Nice article'}
        }, format='json')

        assert response.status_code == 201
        assert response.json()['comment']['body'] == 'Nice article'

    def test_create_on_unknown_article_returns_404(self, auth_client):
        response = auth_client.post('/api/articles/does-not-exist/comments', {
            'comment': {'body': 'Nice article'}
        }, format='json')
        assert response.status_code == 404


@pytest.mark.django_db
class TestCommentList:
    def test_list_returns_comments_envelope_with_count(self, api_client):
        article = ArticleFactory(slug='commented')
        CommentFactory.create_batch(2, article=article)

        response = api_client.get('/api/articles/commented/comments')

        assert response.status_code == 200
        body = response.json()
        assert len(body['comments']) == 2
        assert body['commentsCount'] == 2

    def test_list_only_returns_comments_for_this_article(self, api_client):
        article_one = ArticleFactory(slug='article-one')
        article_two = ArticleFactory(slug='article-two')
        CommentFactory(article=article_one)
        CommentFactory(article=article_two)

        response = api_client.get('/api/articles/article-one/comments')

        assert response.json()['commentsCount'] == 1


@pytest.mark.django_db
class TestCommentDestroy:
    def test_destroy_requires_authentication(self, api_client):
        article = ArticleFactory(slug='commented')
        comment = CommentFactory(article=article)

        response = api_client.delete(
            '/api/articles/commented/comments/%d' % comment.pk
        )
        assert response.status_code == 403

    def test_destroy_returns_204_and_removes_comment(self, auth_client):
        article = ArticleFactory(slug='commented')
        comment = CommentFactory(article=article)

        response = auth_client.delete(
            '/api/articles/commented/comments/%d' % comment.pk
        )

        assert response.status_code == 204
        assert not article.comments.filter(pk=comment.pk).exists()

    def test_destroy_unknown_comment_returns_404(self, auth_client):
        article = ArticleFactory(slug='commented')

        response = auth_client.delete(
            '/api/articles/commented/comments/999999'
        )
        assert response.status_code == 404


@pytest.mark.django_db
class TestTagList:
    def test_list_returns_tags_envelope(self, api_client):
        TagFactory(tag='django', slug='django')
        TagFactory(tag='testing', slug='testing')

        response = api_client.get('/api/tags')

        assert response.status_code == 200
        assert set(response.json()['tags']) == {'django', 'testing'}

    def test_list_does_not_require_authentication(self, api_client):
        response = api_client.get('/api/tags')
        assert response.status_code == 200

    def test_list_is_not_paginated(self, api_client):
        TagFactory.create_batch(25)

        response = api_client.get('/api/tags')

        assert len(response.json()['tags']) == 25


@pytest.mark.django_db
class TestArticleFavorite:
    def test_favorite_requires_authentication(self, api_client):
        ArticleFactory(slug='favable')
        response = api_client.post('/api/articles/favable/favorite')
        assert response.status_code == 403

    def test_favorite_returns_201_with_favorited_true(self, auth_client):
        ArticleFactory(slug='favable')

        response = auth_client.post('/api/articles/favable/favorite')

        assert response.status_code == 201
        body = response.json()['article']
        assert body['favorited'] is True
        assert body['favoritesCount'] == 1

    def test_unfavorite_returns_200_with_favorited_false(self, auth_client):
        ArticleFactory(slug='favable')
        auth_client.post('/api/articles/favable/favorite')

        response = auth_client.delete('/api/articles/favable/favorite')

        assert response.status_code == 200
        body = response.json()['article']
        assert body['favorited'] is False
        assert body['favoritesCount'] == 0

    def test_favorite_unknown_article_returns_404(self, auth_client):
        response = auth_client.post('/api/articles/does-not-exist/favorite')
        assert response.status_code == 404
