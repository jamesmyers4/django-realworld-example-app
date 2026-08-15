"""
Phase 6 — optional performance/load smoke (TEST-PLAN.md), not default-on.
`LimitOffsetPagination` (page size 20) is already in place on list
endpoints, per TEST-PLAN.md §1 -- this is a smoke check that pagination
keeps a large result set's response bounded and fast, not a load-test
tool. Excluded from `make test` (PR-gated), included in `make test-full`
(nightly) -- see Makefile and pytest.ini's `performance` marker.
"""
import time

import pytest

from conduit.apps.core.tests.factories import ArticleFactory


@pytest.mark.performance
@pytest.mark.django_db
class TestArticleListPaginationPerformance:
    def test_default_page_size_caps_response_at_20_articles(self, api_client):
        ArticleFactory.create_batch(50)

        response = api_client.get('/api/articles')

        assert response.status_code == 200
        body = response.json()
        assert len(body['articles']) == 20
        assert body['articlesCount'] == 50

    def test_listing_a_large_result_set_stays_fast(self, api_client):
        ArticleFactory.create_batch(200)

        start = time.time()
        response = api_client.get('/api/articles?limit=20')
        elapsed = time.time() - start

        assert response.status_code == 200
        # Generous smoke threshold -- this is meant to catch a pagination
        # regression (e.g. accidentally fetching the full unpaginated
        # queryset), not to enforce a tight production SLA.
        assert elapsed < 2.0
