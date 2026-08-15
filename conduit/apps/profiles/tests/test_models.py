import pytest

from conduit.apps.core.tests.factories import ArticleFactory, UserFactory


@pytest.mark.django_db
class TestProfileFollow:
    def test_follow_adds_relation(self):
        alice = UserFactory().profile
        bob = UserFactory().profile

        alice.follow(bob)

        assert alice.is_following(bob) is True

    def test_follow_is_not_symmetrical(self):
        alice = UserFactory().profile
        bob = UserFactory().profile

        alice.follow(bob)

        assert bob.is_following(alice) is False

    def test_is_followed_by_reflects_the_other_side(self):
        alice = UserFactory().profile
        bob = UserFactory().profile

        alice.follow(bob)

        assert bob.is_followed_by(alice) is True
        assert alice.is_followed_by(bob) is False

    def test_unfollow_removes_relation(self):
        alice = UserFactory().profile
        bob = UserFactory().profile

        alice.follow(bob)
        alice.unfollow(bob)

        assert alice.is_following(bob) is False

    def test_unfollow_when_not_following_is_a_noop(self):
        alice = UserFactory().profile
        bob = UserFactory().profile

        alice.unfollow(bob)

        assert alice.is_following(bob) is False

    def test_is_following_false_when_never_followed(self):
        alice = UserFactory().profile
        bob = UserFactory().profile

        assert alice.is_following(bob) is False


@pytest.mark.django_db
class TestProfileFavorite:
    def test_favorite_adds_relation(self):
        profile = UserFactory().profile
        article = ArticleFactory()

        profile.favorite(article)

        assert profile.has_favorited(article) is True

    def test_unfavorite_removes_relation(self):
        profile = UserFactory().profile
        article = ArticleFactory()

        profile.favorite(article)
        profile.unfavorite(article)

        assert profile.has_favorited(article) is False

    def test_unfavorite_when_not_favorited_is_a_noop(self):
        profile = UserFactory().profile
        article = ArticleFactory()

        profile.unfavorite(article)

        assert profile.has_favorited(article) is False

    def test_has_favorited_false_when_never_favorited(self):
        profile = UserFactory().profile
        article = ArticleFactory()

        assert profile.has_favorited(article) is False


@pytest.mark.django_db
class TestProfileStringMethod:
    def test_str_returns_username(self):
        user = UserFactory(username='profilestrtest')
        assert str(user.profile) == 'profilestrtest'
