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
- [ ] Phase 1 — unit tests
- [ ] Phase 2 — integration / API contract tests
- [ ] Phase 3 — authorization / boundary testing
- [ ] Phase 4 — edge / negative / boundary cases
- [ ] Phase 5 — E2E happy path
- [ ] Phase 6 — optional (performance smoke)

## Open findings

None yet beyond what TEST-PLAN.md's §2 already flagged (the two known
behavioral quirks, tracked in CONTEXT.md).
