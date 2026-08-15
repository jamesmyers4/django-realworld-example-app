"""
Phase 3 — authorization / boundary testing (TEST-PLAN.md).

Includes the two security-relevant characterization tests flagged in
CONTEXT.md's "Known behavioral quirks": neither `ArticleViewSet.update()`
nor `CommentsDestroyAPIView.destroy()` check that the requesting user
owns the article/comment they're modifying. These are deliberately named
`test_KNOWN_BUG_*` rather than plain green assertions, per
TEST-PLAN-CONTEXT.md's rule for security-relevant infer-but-confirm items
("a treatment that can't be mistaken for a clean pass") — this is current
behavior being pinned under test, not a spec being endorsed. Do not "fix"
these by adding an ownership check; that's explicitly out of scope for
this test-implement run.
"""
import pytest

from conduit.apps.core.tests.factories import ArticleFactory, CommentFactory, UserFactory


@pytest.mark.django_db
class TestArticleOwnershipGap:
    def test_KNOWN_BUG_any_authenticated_user_can_edit_any_article(
        self, api_client
    ):
        owner = UserFactory()
        attacker = UserFactory()
        article = ArticleFactory(author=owner.profile, title='Original Title')

        api_client.credentials(HTTP_AUTHORIZATION='Token ' + attacker.token)
        response = api_client.put('/api/articles/%s' % article.slug, {
            'article': {'title': 'Hijacked Title'}
        }, format='json')

        # conduit/apps/articles/views.py:87 (ArticleViewSet.update) gates
        # only on IsAuthenticatedOrReadOnly -- there is no check that
        # `request.user` is the article's author. This currently succeeds.
        assert response.status_code == 200
        assert response.json()['article']['title'] == 'Hijacked Title'

        article.refresh_from_db()
        assert article.title == 'Hijacked Title'


@pytest.mark.django_db
class TestCommentOwnershipGap:
    def test_KNOWN_BUG_any_authenticated_user_can_delete_any_comment(
        self, api_client
    ):
        article = ArticleFactory()
        comment_owner = UserFactory()
        attacker = UserFactory()
        comment = CommentFactory(article=article, author=comment_owner.profile)

        api_client.credentials(HTTP_AUTHORIZATION='Token ' + attacker.token)
        response = api_client.delete(
            '/api/articles/%s/comments/%d' % (article.slug, comment.pk)
        )

        # conduit/apps/articles/views.py:149
        # (CommentsDestroyAPIView.destroy) gates only on
        # IsAuthenticatedOrReadOnly -- there is no check that `request.user`
        # authored the comment. This currently succeeds.
        assert response.status_code == 204
        assert not article.comments.filter(pk=comment.pk).exists()


@pytest.mark.django_db
class TestUnauthenticatedAccessToProtectedEndpoints:
    """Confirms the 403-not-401 behavior (see CONTEXT.md) is consistent
    across every protected article/comment mutation, not just the ones
    Phase 2 happened to cover."""

    def test_update_article_without_credentials_returns_403(self, api_client):
        article = ArticleFactory()
        response = api_client.put('/api/articles/%s' % article.slug, {
            'article': {'title': 'New Title'}
        }, format='json')
        assert response.status_code == 403

    def test_delete_comment_without_credentials_returns_403(self, api_client):
        article = ArticleFactory()
        comment = CommentFactory(article=article)
        response = api_client.delete(
            '/api/articles/%s/comments/%d' % (article.slug, comment.pk)
        )
        assert response.status_code == 403

    def test_create_article_without_credentials_returns_403(self, api_client):
        response = api_client.post('/api/articles', {
            'article': {'title': 'T', 'description': 'D', 'body': 'B'}
        }, format='json')
        assert response.status_code == 403
