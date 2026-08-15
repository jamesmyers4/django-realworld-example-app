# TEST-PLAN.md — django-realworld-example-app

Planning-session output, produced by hand-following the `test-plan` process
described in `TEST-PLAN-CONTEXT.md` (v0.1) — no installed `test-plan` skill
was available in this session, so this document was written by applying
that process directly rather than invoking it. Written 2026-08-14.

## 0. Repo scan

- **Stack**: Django 1.10.5 + Django REST Framework 3.4.4, custom JWT auth
  (PyJWT 1.4.2), SQLite (`db.sqlite3`, dev-only). No frontend in this repo —
  it's a backend implementing the [RealWorld](https://github.com/gothinkster/realworld)
  "Conduit" API spec (a Medium-style blogging API: articles, comments, tags,
  profiles, follow/favorite).
- **App layout**: four Django apps under `conduit/apps/` — `authentication`
  (custom `User` model, JWT issuance), `profiles` (`Profile`, one-to-one
  with `User`, follow/favorite M2M relations), `articles` (`Article`,
  `Comment`, `Tag`), `core` (shared `TimestampedModel` base, custom DRF
  exception handler, JSON-envelope renderers, a random-string util). Each
  app follows the same file convention: `models.py`, `serializers.py`,
  `views.py`, `urls.py`, `renderers.py`.
- **Routing**: all API routes are mounted under `/api/`, and the articles
  router is built with `trailing_slash=False` — so it's `/api/articles`,
  not `/api/articles/`.
- **Existing test config**: none. No `tests/` directories, no `pytest.ini`/
  `tox.ini`, no CI config (no `.github/`, no other CI YAML). This is a
  from-zero repo for test purposes.
- **Runtime**: containerized this session — see `Dockerfile` /
  `.dockerignore` added at repo root. Python 3.7-slim, confirmed working
  end-to-end (`migrate`, `runserver`, register/login/JWT round trip, article
  list). Details in the "Docker runtime" section below.

## 1. Coverage sweep

Full taxonomy walk. Status is `Gap` (nothing exists), `N/A` (category
doesn't apply to this repo), or `Note` (deterministic-behavior candidate
worth pinning). Everything here was read from actual view/model/serializer
code, not inferred from directory listings.

| Category | Status | Notes |
|---|---|---|
| Unit tests | Gap | `UserManager`, JWT generation/expiry, `Profile` follow/favorite methods, `core.utils.generate_random_string`, custom exception handler, serializer field validation |
| Integration / API contract | Gap | Every endpoint below has zero coverage |
| E2E happy path | Gap | API-level only (no browser/frontend in this repo) — register → login → create article → tag → comment → favorite → follow → feed |
| Edge / negative / boundary | Gap | Duplicate username/email/slug, malformed body, pagination bounds, follow-self, double-favorite |
| Accessibility (WCAG/508) | N/A | No UI in this repo |
| Golden master / characterization | Note | Two spots worth pinning explicitly — see §2 items 1–2 |
| Authorization / boundary testing | **Gap — high priority** | See §2 item 1: article edit and comment delete have no ownership check at all |
| Cross-browser / responsive | N/A | No UI in this repo |
| AI/LLM pipeline output testing | N/A | No LLM/AI pipeline in this app |
| Visual regression | N/A (off by default anyway) | No UI in this repo |
| Performance / load | Optional, not default-on | `LimitOffsetPagination` (page size 20) already in place on list endpoints, which is the main lever |

Sweep is overwhelmingly `Gap` → per TEST-PLAN-CONTEXT.md's sequencing
philosophy, this run uses **bootstrap sequencing**, not gap-closure.

## 2. Three-tier resolution

**Always infer, never ask** (read directly from code/config, not judgment):
Django 1.10.5 / DRF 3.4.4 / PyJWT 1.4.2 pinned in `requirements.txt`;
SQLite dev DB; custom JWT auth backend (`conduit/apps/authentication/backends.py`);
no existing test runner, CI, or test-doc file of any kind.

**Infer, but confirm** — flagged rather than silently assumed one way or
the other:

1. **No object-level authorization check on article edit or comment
   delete.** `ArticleViewSet.update()` (`conduit/apps/articles/views.py:87`)
   and `CommentsDestroyAPIView.destroy()` (`conduit/apps/articles/views.py:149`)
   both gate only on `IsAuthenticatedOrReadOnly` — *any* authenticated user
   can edit *any* article or delete *any* comment, not just their own.
   Confirm: known/intentional simplification (this is a widely-forked
   tutorial app, so plausible), or a real gap to characterize as a bug?
   Recommendation below assumes "characterize current behavior under test,
   don't silently harden it," per this doc's own guidance not to treat a
   bug as spec.
2. **Reference-equality bug in follow-self check.**
   `ProfileFollowAPIView.post()` (`conduit/apps/profiles/views.py:63`) does
   `if follower.pk is followee.pk` — identity comparison on integers, not
   `==`. It happens to work today only because both PKs fall inside
   CPython's small-int cache; not reliable in general. Treat as a bug to
   test-and-fix-later, not something to bake into a golden master as
   correct-by-definition.
3. **No delete endpoint for articles at all** — `ArticleViewSet` mixes in
   `Create`/`List`/`Retrieve` only, no `Destroy`. Confirm this is in-scope
   for the RealWorld spec as implemented here (it appears to be — no route
   exists to test against either way) rather than a coverage gap.
4. `DEBUG = True` and a hardcoded `SECRET_KEY` are committed in
   `conduit/settings.py`. Pre-existing condition, not touched per this
   task's scope (app source is off-limits) — noted here only so it isn't
   mistaken for something the test suite should silently paper over.

**Never infer, always ask** — resolved via interview this session:

| Question | Answer |
|---|---|
| Commit/review mode | Autonomous commit-as-you-go |
| CI schedule | PR-gated smoke/unit + nightly full regression (needs a CI YAML; no external accounts required) |
| Coverage depth / risk tolerance | Thorough on core paths (auth, articles CRUD, comments, follow/favorite); smoke-only elsewhere |
| Session/runway budget | No preference stated — defaulting to one phase per session (this doc's own recommended default) |

Not asked, resolved by the carve-out / defaults instead, since nothing here
was ambiguous enough to need a person:

- **BDD/Cucumber layer**: skip by default. No non-technical stakeholders,
  and the business rules aren't ambiguous — they're pinned by the public
  RealWorld API spec this repo implements.
- **Temp/test DB strategy**: SQLite in-memory, since the app itself already
  runs on SQLite.
- **Visual regression opt-in**: off by default — no UI surface exists to
  regress.
- **Existing test-doc filename**: none found, so `TESTING.md` will be
  created fresh during implementation rather than renamed from anything.
- **Team size / budget / timeline / pre-launch-vs-prod**: not asked. This
  repo is an archived (2022), unmaintained tutorial app being used as a
  fixed QA test target, not a live product with a team or a launch date —
  those questions don't have a meaningful answer here. Noted as process
  feedback in §5.

## 3. Sequencing — bootstrap mode

Fast, isolated, deterministic layers first (they become fixtures the later
layers reuse), then integration, then E2E, then edge/grey-area, then
optional layers last.

- **Phase 0 — Test infra bootstrap.** `pytest` + `pytest-django`, a
  `factory_boy` (or plain fixtures) setup for `User`/`Profile`/`Article`,
  isolated in-memory SQLite settings for the test run, a `docker compose`
  or Makefile target that runs the suite inside the same Python 3.7
  container the app runs in, and a GitHub Actions workflow skeleton
  (PR-gated job + nightly scheduled job, per the interview answer).
- **Phase 1 — Unit tests.** `UserManager.create_user`/`create_superuser`
  validation; JWT token generation and 60-day expiry
  (`User._generate_jwt_token`); `Profile.follow`/`unfollow`/`favorite`/
  `unfavorite`/`is_following`/`has_favorited`; `core.utils.generate_random_string`;
  `core.exceptions.core_exception_handler`; serializer-level field
  validation (required fields, uniqueness) independent of the view layer.
  Includes the two characterization items from §2 (1–2) as explicit,
  clearly-labeled tests of *current* behavior — not silently patched.
- **Phase 2 — Integration / API contract tests**, one block per app:
  - `authentication`: register, login, current-user retrieve + update,
    including the JWT-envelope response shape.
  - `profiles`: retrieve profile, follow/unfollow, `favorited`/`following`
    flags on nested profile payloads.
  - `articles`: list (with `author`/`tag`/`favorited` query filters and
    pagination), create, retrieve, update.
  - `articles` (comments/tags/favorite): comment create/list/destroy, tag
    list, favorite/unfavorite.
- **Phase 3 — Authorization / boundary testing.** Cross-user article edit,
  cross-user comment delete (both expected to currently *succeed* per §2
  item 1 — test asserts and documents that, doesn't assume it should fail),
  unauthenticated access to protected endpoints, invalid/expired/malformed
  JWT handling.
- **Phase 4 — Edge / negative / boundary cases.** Duplicate username/email
  on register, duplicate slug on article create, missing required fields,
  malformed JSON body, pagination offset past the end of the result set,
  follow-self (including confirming whether the `is`-comparison bug from
  §2 item 2 actually manifests at low PKs in a fresh test DB), double-favorite/
  unfavorite-when-not-favorited idempotency.
- **Phase 5 — E2E happy path** (API-level, no browser involved since there's
  no frontend): one scripted flow through register → login → create
  article → tag/list/filter → comment → favorite → follow → feed, asserting
  the full response shape at each step rather than isolated status codes.
- **Phase 6 — Optional, not default-on.** Performance/load smoke on the
  paginated list endpoints. Visual regression, cross-browser, and AI/LLM
  output testing are all `N/A` for this repo (§1) and not part of this
  plan.

## 4. Docker runtime (this session's setup work)

Added at repo root, nothing in `conduit/` touched:

- **`Dockerfile`** — `python:3.7-slim`, installs `requirements.txt` as
  pinned, runs `manage.py migrate --noinput && manage.py runserver
  0.0.0.0:8000` on container start.
- **`.dockerignore`** — excludes `.git`, `__pycache__`, the dev
  `db.sqlite3`, and the Docker files themselves from the build context.
- No `docker-compose.yml` — the only external dependency is SQLite, which
  needs no separate service.

**Why Python 3.7, not something newer**: Django 1.10.5 is pinned in
`requirements.txt` (2016-era) and wasn't asked to be upgraded. I bisected
across `python:3.6-slim` through `python:3.9-slim`:

- 3.6 and 3.7 — clean install, `manage.py check`/`migrate`/`runserver` all
  work.
- 3.8 and 3.9 — install succeeds (pure-Python wheels), but importing
  `django.contrib.auth.models` fails hard at startup:
  `RuntimeError: __class__ not set defining 'AbstractBaseUser' ... Was
  __classcell__ propagated to type.__new__?` — a metaclass/`__classcell__`
  handling change Python made in 3.8 that Django's `six`-based Python 2/3
  compat layer (still in use at Django 1.10) doesn't survive.

So **3.7 is the newest Python this pinned Django version actually runs
on** — that's the boundary, not a preference call.

**Verified working end-to-end** inside the container: `manage.py check`,
`manage.py migrate` (applies all 20 migrations across `admin`, `articles`,
`auth`, `authentication`, `contenttypes`, `profiles`, `sessions` cleanly),
`manage.py runserver`, `GET /api/articles` → `200` with a real paginated
envelope, and `POST /api/users` → `201` with a working user record and a
decodable JWT. Note the router's `trailing_slash=False`: it's
`/api/articles`, not `/api/articles/` — a 404 on the trailing-slash form is
expected, not a bug.

## 5. Feedback on TEST-PLAN-CONTEXT.md

Concrete notes from actually running the process by hand against this
repo, offered in the same spirit as the Shenny run's process-observations
log that fed v0.1:

1. **The always-ask interview doesn't have an escape hatch for "this
   question has no meaningful referent here."** The carve-out in the
   three-tier discipline covers *documented* answers ("the repo already
   says X"), but team size / budget / timeline / pre-launch-vs-prod assume
   there's a live team and a product roadmap behind the repo at all. That's
   not true for a fixed archival/QA-target repo like this one — there's no
   team to ask, no launch. I resolved it by treating "not applicable to
   this repo" as its own outcome and saying so, but the doc doesn't
   currently name that as a legitimate third path alongside "answered
   silently" and "ask the human." Worth adding explicitly, since it'll
   recur for any dogfeeding run against a repo that isn't itself someone's
   live product (open-source archives, teaching repos, CTF targets).

2. **Runtime/environment setup (get-it-running-at-all) isn't in the process
   at all, but for an archived/unmaintained repo it's a real, sometimes
   nontrivial pre-step** — here it meant bisecting four Python versions
   against a Django release from 2016 to find the actual compatibility
   ceiling, which isn't a scan/sweep/interview/sequence activity as
   currently defined, but it directly gates whether any of Phase 0 can
   even happen (there's no test infra without a working interpreter
   first). The stack reference matrix's "Docker is close to universal"
   prior is a fine default, but for older stacks specifically, *which
   language runtime version to target* is itself a decision the process
   currently has no place to record or reason about. Might be worth a
   named pre-step ("Runtime viability check") ahead of Scan, at least for
   repos flagged as archived/legacy.

3. **"Infer, but confirm" earned its keep here in a way worth calling
   out**: the object-level-authorization gap (§2 item 1) is exactly the
   kind of thing that's easy to either silently test-as-correct or
   silently "fix" while writing tests — the discipline of stopping to flag
   it by name, with file:line, and defer the should-this-be-a-test-of-
   current-behavior-or-a-bug-report call, worked well and is worth keeping
   exactly as specified. No change suggested here, just a confirmation
   that this part of the process held up on a second, very different
   stack.

4. **The authorization/boundary-testing category description
   ("Frequently the category devs skip entirely") undersells how it
   actually surfaces in practice** — it's not just skipped, it's the
   category most likely to contain a real, currently-shipping bug (as
   here), which makes it worth sequencing earlier than "after edge cases"
   in a bootstrap run specifically, not just flagging as commonly-missed.
   Current bootstrap ordering puts it before edge/negative cases already
   (§3 Phase 3 vs Phase 4), which is right — just noting the doc's prose
   about this category could say why it deserves that priority rather than
   only that it's often skipped.

5. **Minor**: the interview question table's "Recommended default" column
   was genuinely useful for moving through the interview fast (I could
   present each question with its own recommended option pre-selected
   rather than open-ended) — worth explicitly telling implementers of the
   `test-plan` skill to surface defaults the same way, since it cut a
   4-question interview down to a couple of clicks each instead of
   free-text answers.
