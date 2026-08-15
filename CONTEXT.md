# CONTEXT.md — django-realworld-example-app

Minimal stub created 2026-08-14 during the test-implement catch-up session
(TEST-PLAN.md was written under TEST-PLAN-CONTEXT.md v0.1, before this
file's creation was made a mandatory part of that process in v0.2). Expected
to grow during implementation sessions the same way TESTING.md does — see
TEST-PLAN-CONTEXT.md's Architecture section.

## Domain vocabulary

This is a Django REST Framework backend implementing the
[RealWorld](https://github.com/gothinkster/realworld) "Conduit" API spec —
a Medium-style blogging API (articles, comments, tags, profiles,
follow/favorite). No frontend lives in this repo; it's API-only, mounted
under `/api/`.

Four Django apps under `conduit/apps/`:

- **authentication** — custom `User` model, JWT issuance
  (`conduit/apps/authentication/backends.py`).
- **profiles** — `Profile`, one-to-one with `User`; follow/favorite M2M
  relations.
- **articles** — `Article`, `Comment`, `Tag`.
- **core** — shared `TimestampedModel` base, custom DRF exception handler,
  JSON-envelope renderers, a random-string util.

Each app follows the same file convention: `models.py`, `serializers.py`,
`views.py`, `urls.py`, `renderers.py`.

The articles router is built with `trailing_slash=False`, so routes are
`/api/articles`, not `/api/articles/` — a 404 on the trailing-slash form is
expected, not a bug.

## Known behavioral quirks (pre-existing, not to be silently fixed)

1. **No object-level authorization check on article edit or comment
   delete.** `ArticleViewSet.update()`
   (`conduit/apps/articles/views.py:87`) and
   `CommentsDestroyAPIView.destroy()`
   (`conduit/apps/articles/views.py:149`) both gate only on
   `IsAuthenticatedOrReadOnly` — *any* authenticated user can edit *any*
   article or delete *any* comment, not just their own. Security-relevant,
   not merely quirky — characterized under test as
   `test_KNOWN_BUG_no_ownership_check`-style tests (or `xfail` with a
   reason), never as a plain green assertion, so it can't be mistaken for a
   clean pass. Not to be fixed as part of test-implement work.

2. **Reference-equality bug in follow-self check.**
   `ProfileFollowAPIView.post()` (`conduit/apps/profiles/views.py:63`) does
   `if follower.pk is followee.pk` — identity comparison on integers, not
   `==`. Happens to work today only because both PKs fall inside CPython's
   small-int cache; not reliable in general. Characterized as current
   behavior under test, not treated as correct-by-definition or fixed.

## Runtime ceiling

Django 1.10.5 is pinned in `requirements.txt` (2016-era) and wasn't asked
to be upgraded. **Python 3.7 is the newest Python this pinned Django
version actually runs on** — Python 3.8+ breaks at import time
(`RuntimeError: __class__ not set defining 'AbstractBaseUser' ... Was
__classcell__ propagated to type.__new__?`), a metaclass/`__classcell__`
handling change Python made in 3.8 that Django's `six`-based Python 2/3
compat layer at this version doesn't survive. The repo runs in Docker on
`python:3.7-slim` (see `Dockerfile` at repo root) for exactly this reason —
this is a hard ceiling, not a preference.

## See also

- `TEST-PLAN.md` — the governing test automation plan (phases, sequencing,
  interview answers).
- `TESTING.md` — living test-suite doc, created during Phase 0.
- `IMPLEMENTATION-OBSERVATIONS.md` — process notes from running
  test-implement against this plan.
