"""Phase 4 — edge / negative / boundary cases (TEST-PLAN.md): follow-self,
double-favorite/unfavorite-when-not-favorited idempotency at the API level.
"""
import pytest

from conduit.apps.core.tests.factories import ArticleFactory, UserFactory


@pytest.mark.django_db
class TestFollowSelf:
    def test_follow_self_returns_400(self, api_client):
        user = UserFactory(username='selffollower')
        api_client.credentials(HTTP_AUTHORIZATION='Token ' + user.token)

        response = api_client.post('/api/profiles/selffollower/follow')

        # ProfileFollowAPIView.post (conduit/apps/profiles/views.py:63) uses
        # `follower.pk is followee.pk` -- an identity comparison, not `==`.
        # This assertion only holds because a fresh test DB assigns small
        # sequential PKs, which fall inside CPython's small-int cache
        # (roughly -5 to 256) where `is` and `==` happen to agree for ints.
        # See CONTEXT.md's "Known behavioral quirks" #2 -- this test
        # confirms the bug does NOT manifest at these PK values, it does
        # not confirm the check is reliable in general. Not fixed here.
        assert response.status_code == 400

    def test_follow_self_at_high_pk_bypasses_the_check(self, api_client):
        # Same call, but after padding the users table so this user's PK is
        # comfortably past 256 (outside CPython's small-int cache range).
        # Empirically confirmed (not assumed): at this PK range, `is`
        # between the two separately-queried `Profile.pk` int objects is
        # False even though their *values* are equal, so
        # `follower.pk is followee.pk` no longer catches the self-follow
        # case at all -- the ValidationError never fires and the follow
        # actually succeeds (201, not 400). This is the reference-equality
        # bug from CONTEXT.md's "Known behavioral quirks" #2 actually
        # manifesting, not a hypothetical. Answers TEST-PLAN.md Phase 4's
        # open question ("confirming whether the is-comparison bug ...
        # actually manifests") -- it does, once PKs leave the small-int
        # cache range. Characterized as current behavior, not fixed here.
        UserFactory.create_batch(300)  # push PKs well past the small-int cache
        user = UserFactory(username='selffollowerhighpk')
        api_client.credentials(HTTP_AUTHORIZATION='Token ' + user.token)

        response = api_client.post('/api/profiles/selffollowerhighpk/follow')

        assert response.status_code == 201
        assert response.json()['profile']['following'] is True


@pytest.mark.django_db
class TestFollowIdempotency:
    def test_following_twice_does_not_error(self, auth_client):
        UserFactory(username='followtarget')

        first = auth_client.post('/api/profiles/followtarget/follow')
        second = auth_client.post('/api/profiles/followtarget/follow')

        assert first.status_code == 201
        assert second.status_code == 201
        assert second.json()['profile']['following'] is True

    def test_unfollowing_when_not_following_does_not_error(self, auth_client):
        UserFactory(username='nevernfollowed')

        response = auth_client.delete('/api/profiles/nevernfollowed/follow')

        assert response.status_code == 200
        assert response.json()['profile']['following'] is False


@pytest.mark.django_db
class TestFavoriteIdempotency:
    def test_favoriting_twice_does_not_error_or_double_count(self, auth_client):
        ArticleFactory(slug='favme')

        first = auth_client.post('/api/articles/favme/favorite')
        second = auth_client.post('/api/articles/favme/favorite')

        assert first.status_code == 201
        assert second.status_code == 201
        assert second.json()['article']['favoritesCount'] == 1

    def test_unfavoriting_when_not_favorited_does_not_error(self, auth_client):
        ArticleFactory(slug='neverfavorited')

        response = auth_client.delete('/api/articles/neverfavorited/favorite')

        assert response.status_code == 200
        assert response.json()['article']['favoritesCount'] == 0
