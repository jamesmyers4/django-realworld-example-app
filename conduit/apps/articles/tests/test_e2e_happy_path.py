"""
Phase 5 — E2E happy path (TEST-PLAN.md). API-level only, no browser
involved since there's no frontend in this repo. One scripted flow through
register -> login -> create article -> tag/list/filter -> comment ->
favorite -> follow -> feed, asserting the full response shape at each
step rather than isolated status codes.

The feed step doesn't actually reach ArticlesFeedAPIView -- see the inline
comment at that step and CONTEXT.md quirk #4 (a route-shadowing bug found
while writing this exact test). Kept in the flow and asserted against its
real (broken) outcome rather than skipped, so the test stays an honest
end-to-end trace of what a client hitting this API actually experiences.
"""
import pytest


@pytest.mark.django_db
def test_full_happy_path_flow(api_client):
    # 1. Register two users: an author and a reader.
    author_response = api_client.post('/api/users', {
        'user': {
            'username': 'author1',
            'email': 'author1@example.com',
            'password': 'authorpass123',
        }
    }, format='json')
    assert author_response.status_code == 201
    author_body = author_response.json()['user']
    assert author_body['username'] == 'author1'
    assert 'token' in author_body

    reader_response = api_client.post('/api/users', {
        'user': {
            'username': 'reader1',
            'email': 'reader1@example.com',
            'password': 'readerpass123',
        }
    }, format='json')
    assert reader_response.status_code == 201
    reader_body = reader_response.json()['user']

    # 2. Login as the author (a second, independent auth round-trip from
    # registration's own token).
    login_response = api_client.post('/api/users/login', {
        'user': {'email': 'author1@example.com', 'password': 'authorpass123'}
    }, format='json')
    assert login_response.status_code == 200
    author_token = login_response.json()['user']['token']
    assert author_token

    author_client = api_client
    author_client.credentials(HTTP_AUTHORIZATION='Token ' + author_token)

    # 3. Create an article, with tags.
    create_response = author_client.post('/api/articles', {
        'article': {
            'title': 'A Happy Path Article',
            'description': 'Walking the whole flow',
            'body': 'From register to feed.',
            'tagList': ['e2e', 'happy-path'],
        }
    }, format='json')
    assert create_response.status_code == 201
    article = create_response.json()['article']
    assert article['title'] == 'A Happy Path Article'
    assert article['author']['username'] == 'author1'
    assert set(article['tagList']) == {'e2e', 'happy-path'}
    assert article['favorited'] is False
    assert article['favoritesCount'] == 0
    slug = article['slug']

    # 4. List/filter: article shows up in the global list, by author, and
    # by tag; the tag itself shows up in the tag list.
    list_response = author_client.get('/api/articles')
    assert list_response.status_code == 200
    assert list_response.json()['articlesCount'] == 1

    by_author_response = author_client.get('/api/articles?author=author1')
    assert by_author_response.json()['articlesCount'] == 1

    by_tag_response = author_client.get('/api/articles?tag=e2e')
    assert by_tag_response.json()['articlesCount'] == 1

    tags_response = author_client.get('/api/tags')
    assert set(tags_response.json()['tags']) >= {'e2e', 'happy-path'}

    # 5. Switch to the reader and comment on the article.
    reader_client = api_client
    reader_client.credentials(
        HTTP_AUTHORIZATION='Token ' + reader_body['token']
    )

    comment_response = reader_client.post(
        '/api/articles/%s/comments' % slug,
        {'comment': {'body': 'Great walkthrough!'}}, format='json'
    )
    assert comment_response.status_code == 201
    assert comment_response.json()['comment']['body'] == 'Great walkthrough!'
    assert comment_response.json()['comment']['author']['username'] == 'reader1'

    comments_list_response = reader_client.get(
        '/api/articles/%s/comments' % slug
    )
    assert comments_list_response.json()['commentsCount'] == 1

    # 6. Reader favorites the article.
    favorite_response = reader_client.post('/api/articles/%s/favorite' % slug)
    assert favorite_response.status_code == 201
    favorited_article = favorite_response.json()['article']
    assert favorited_article['favorited'] is True
    assert favorited_article['favoritesCount'] == 1

    # Reflected back when the reader retrieves the article directly, too.
    retrieve_response = reader_client.get('/api/articles/%s' % slug)
    assert retrieve_response.json()['article']['favorited'] is True

    # 7. Reader follows the author.
    follow_response = reader_client.post('/api/profiles/author1/follow')
    assert follow_response.status_code == 201
    assert follow_response.json()['profile']['following'] is True

    profile_response = reader_client.get('/api/profiles/author1')
    assert profile_response.json()['profile']['following'] is True

    # 8. Reader's feed should show the author's article -- but doesn't.
    # KNOWN BUG (CONTEXT.md quirk #4): the article-detail route
    # (`articles/(?P<slug>[^/.]+)$`, registered via the DefaultRouter) is
    # wired up before the explicit `articles/feed` pattern in
    # conduit/apps/articles/urls.py, so this request resolves to
    # ArticleViewSet.retrieve(slug='feed') instead of ArticlesFeedAPIView --
    # confirmed via django.urls.resolve(), not assumed. The feed endpoint
    # is unreachable as currently routed; this asserts that actual (broken)
    # behavior rather than the happy-path outcome the plan expected, per
    # this session's characterize-don't-fix discipline.
    feed_response = reader_client.get('/api/articles/feed')
    assert feed_response.status_code == 404

    # 9. Author edits the article; the change is visible to the reader too.
    author_client.credentials(HTTP_AUTHORIZATION='Token ' + author_token)
    update_response = author_client.put('/api/articles/%s' % slug, {
        'article': {'title': 'A Happy Path Article (Revised)'}
    }, format='json')
    assert update_response.status_code == 200
    assert update_response.json()['article']['title'] == (
        'A Happy Path Article (Revised)'
    )

    reader_client.credentials(
        HTTP_AUTHORIZATION='Token ' + reader_body['token']
    )
    final_retrieve = reader_client.get('/api/articles/%s' % slug)
    assert final_retrieve.json()['article']['title'] == (
        'A Happy Path Article (Revised)'
    )
