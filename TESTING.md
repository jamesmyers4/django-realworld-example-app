# TESTING.md — django-realworld-example-app

Living test-suite doc. Created during Phase 0 of TEST-PLAN.md's bootstrap
sequence; updated as each subsequent phase lands. See TEST-PLAN.md for the
governing plan and CONTEXT.md for domain background.

## Running the suite

Everything runs inside the same Python 3.7 container the app itself runs
in — Django 1.10.5 (pinned) doesn't import on Python 3.8+, see CONTEXT.md's
"Runtime ceiling" section. There is no supported way to run this suite
directly against a host Python; use Docker.

```
make test        # PR-gated: everything except the optional performance-smoke layer
make test-full    # nightly: everything, including performance-smoke
```

Both targets rebuild the image first, so they always run against current
source. To run a subset directly:

```
make build
docker run --rm conduit-test pytest conduit/apps/articles/tests/test_models.py -v
```

## Layout

- `conftest.py` (repo root) — shared fixtures: `api_client` (DRF
  `APIClient`), `create_user`/`user` (factory-backed), `auth_client` (an
  `api_client` pre-authenticated with a fresh user's JWT).
- `conduit/apps/core/tests/factories.py` — `factory_boy` factories shared
  across all apps' suites: `UserFactory`, `ArticleFactory`, `CommentFactory`,
  `TagFactory`. `ProfileFactory` deliberately does not exist — `Profile` is
  always created via the `post_save` signal on `User`
  (`conduit/apps/authentication/signals.py`), so factories that need a
  profile do `UserFactory().profile` rather than constructing one directly
  (constructing one directly would violate the `OneToOneField` and collide
  with the signal-created row).
- Per-app `conduit/apps/<app>/tests/` — one `tests/` package per app,
  mirroring the source layout. `test_models.py`, `test_views.py`,
  `test_serializers.py` etc. as needed per app.
- `conduit/settings_test.py` — test-only settings override (in-memory
  SQLite, fast password hasher). Selected via `pytest.ini`'s
  `DJANGO_SETTINGS_MODULE`.
- `pytest.ini` — registers the `performance` marker (opt-in, excluded from
  `make test`, included in `make test-full`) and points at
  `conduit.settings_test`.

## Conventions

- DB-touching tests take the `db` fixture (or `pytest.mark.django_db`)
  explicitly — pytest-django fails fast on tests that touch the DB without
  declaring it, which is intentional signal, not friction.
- API-level tests use `api_client`/`auth_client` from the root `conftest.py`
  rather than constructing a `Client()`/`APIClient()` per test file.
- Tests characterizing a known, pre-existing bug (see CONTEXT.md's "Known
  behavioral quirks") are never plain green assertions — they're named
  `test_KNOWN_BUG_*` or marked `xfail` with a reason, so a reader (or CI)
  can't mistake "current behavior is pinned" for "this is correct."

## Coverage state

Tracked against TEST-PLAN.md's phase list. Updated as phases land — see
IMPLEMENTATION-OBSERVATIONS.md for the process notes behind each phase
boundary.

- [x] Phase 0 — test infra bootstrap
- [x] Phase 1 — unit tests (58 tests: `UserManager`, JWT generation/expiry,
      `Profile` follow/favorite, `core.utils.generate_random_string`,
      `core_exception_handler`, `RegistrationSerializer`/`LoginSerializer`/
      `ArticleSerializer`/`CommentSerializer` field validation)
- [x] Phase 2 — integration / API contract tests (46 tests: registration,
      login, current-user retrieve/update; profile retrieve/follow/unfollow;
      article list with author/tag/favorited filters and pagination,
      create, retrieve, update; comment create/list/destroy; tag list;
      article favorite/unfavorite)
- [x] Phase 3 — authorization / boundary testing (10 tests: the two
      security-relevant characterization tests for the ownership-check gap
      — `test_KNOWN_BUG_*`, see CONTEXT.md — cross-user article edit and
      comment delete; unauthenticated access to protected mutation
      endpoints; invalid/expired/malformed/wrong-scheme JWT handling)
- [x] Phase 4 — edge / negative / boundary cases (18 tests: duplicate
      username/email on register, missing required fields, malformed JSON
      body, pagination offset past the end of the result set, follow-self
      at low and high PKs, double-favorite/unfavorite-when-not-favorited
      and double-follow/unfollow-when-not-following idempotency. Also
      surfaced a third, previously-uncharacterized bug — see CONTEXT.md
      quirk #3, duplicate explicit article slug — beyond the two flagged
      in TEST-PLAN.md §2)
- [x] Phase 5 — E2E happy path (1 scripted flow: register x2 -> login ->
      create article with tags -> list/filter by author/tag -> tag list ->
      comment -> favorite -> follow -> feed -> edit -> re-retrieve,
      asserting full response shape at each step. Surfaced a fourth
      previously-uncharacterized bug — see CONTEXT.md quirk #4,
      `/api/articles/feed` is unreachable due to route shadowing)
- [x] Phase 6 — optional (performance smoke, 2 tests: default page size
      caps a 50-article result set at 20, listing 200 articles stays
      under a generous smoke threshold). Marked `@pytest.mark.performance`
      — excluded from `make test`/PR-gated CI, included in
      `make test-full`/nightly. Visual regression, cross-browser, and
      AI/LLM output testing are all N/A for this repo (§1) and out of
      scope.

**All six phases complete.** 135 tests total (133 always-run + 2
performance-marked). See IMPLEMENTATION-OBSERVATIONS.md for the full
process retrospective.

## Open findings

None yet beyond what TEST-PLAN.md's §2 already flagged (the two known
behavioral quirks, tracked in CONTEXT.md).
