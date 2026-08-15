# IMPLEMENTATION-OBSERVATIONS.md — django-realworld-example-app

Process notes from running `test-implement` (by hand, per
TEST-PLAN-CONTEXT.md v0.2 — no installed skill available in this session
either, same situation as the TEST-PLAN.md planning session) against this
repo's TEST-PLAN.md. This is the first time `test-implement` has actually
executed a phase against either of the two existing plans — see
TEST-PLAN-CONTEXT.md's "Next run" recommendation, which named this
specific gap. This doc is the actual point of the run: TEST-PLAN-CONTEXT.md
itself only gets better if what actually happened during implementation is
recorded, not just what the plan predicted.

## CONTEXT.md catch-up

TEST-PLAN.md was written under TEST-PLAN-CONTEXT.md v0.1, before v0.2 made
CONTEXT.md creation a mandatory, non-deferred part of the planning session.
No CONTEXT.md existed in this repo at the start of this session. Created
one now, as a one-time catch-up, before starting Phase 0 — domain
vocabulary, the two flagged quirks with file:line, and the Python 3.7
ceiling, all sourced directly from TEST-PLAN.md's own §0/§2/§4 rather than
re-deriving anything. This isn't a new finding so much as confirmation that
the "create a minimal stub when none exists" rule is easy to apply
retroactively when the source material (TEST-PLAN.md) already contains
everything the stub needs — the stub was assembly, not new analysis.

## Phase boundaries: plan vs. actual

**Phase 0.** Executed exactly as TEST-PLAN.md scoped it — pytest/pytest-django
tooling, factory_boy factories, in-memory-SQLite test settings, a
Makefile-driven Docker test target, and a full GitHub Actions workflow, all
as one phase/one commit. This directly answers TEST-PLAN-CONTEXT.md's open
"phase-sizing floor" question, which specifically flagged this exact phase
as "a plausible instance" of an oversized default first phase, pending
actual execution. In practice it wasn't oversized: it fit in a single
sitting with room to spare, validated end-to-end (image build, pytest
collection, a real DB-touching test), and didn't need splitting. One data
point, not a general proof — but the concern doesn't seem to bear out here.

**Phase 1.** Also executed as one phase/one commit, per TEST-PLAN.md's
scope (UserManager, JWT, Profile follow/favorite, core.utils, exception
handler, serializer validation) — 58 tests. Also fit a single sitting
without strain. One deviation worth noting: TEST-PLAN.md's Phase 1
description says it "includes the two characterization items from §2 (1-2)
as explicit, clearly-labeled tests of *current* behavior." In practice
those two items are both *view-layer* behavior (`ArticleViewSet.update`,
`CommentsDestroyAPIView.destroy`, `ProfileFollowAPIView.post`) — they can't
be exercised as unit tests without going through the API client, and
TEST-PLAN.md's own Phase 3 (Authorization / boundary testing) is where
cross-user article-edit and comment-delete are actually listed as test
subjects. Interpreted this as a phase-labeling slip in the plan rather than
a real requirement to unit-test view methods in isolation — deferred both
characterization tests to Phase 3, where the plan's own phase *content*
(not just its Phase 1 prose aside) already puts them. Recorded here since
it's a real plan/content mismatch, not a judgment call that should pass
silently under autonomous commit mode.

**Phase 2.** One phase/one commit, matching TEST-PLAN.md's four per-app
blocks (authentication, profiles, articles, articles
comments/tags/favorites) — 46 tests. Fit a single sitting.

**Phase 3.** One phase/one commit, matching TEST-PLAN.md's scope exactly:
the two `test_KNOWN_BUG_*` characterization tests deferred here from Phase
1 (see above), unauthenticated access to protected mutation endpoints, and
invalid/expired/malformed JWT handling — 10 tests. Also fit a single
sitting.

## Commit-mode fidelity

Recorded answer: autonomous commit-as-you-go, no stop-for-review. Watching
for: does that actually hold once a phase turns out to need judgment calls
mid-stream (e.g. a fixture design decision not spelled out in TEST-PLAN.md)?

Held for both Phase 0 and Phase 1 without stopping, including through two
judgment calls TEST-PLAN.md didn't spell out: (1) the fixture design for
`Profile` — TEST-PLAN.md never mentions that `Profile` is signal-created
off `User` rather than independently constructable, which shapes every
factory that needs one (`ArticleFactory.author`, `CommentFactory.author`
both go through `UserFactory().profile` rather than a `ProfileFactory`);
(2) the Phase 1/Phase 3 placement mismatch for the two characterization
tests, resolved by following the plan's phase *content* over its Phase 1
prose aside (see above). Neither warranted a stop under the recorded
commit mode — both are exactly the kind of small in-flight call autonomous
mode is supposed to absorb, and both are logged here rather than passed
through silently.

**Phase 2.** One phase/one commit again, matching TEST-PLAN.md's four
per-app blocks (authentication, profiles, articles, articles
comments/tags/favorites) — 46 tests. First real mid-phase surprise: every
`IsAuthenticated`-gated endpoint returns 403 for an unauthenticated
request, not 401 — DRF only emits 401 when the active authenticator
implements `authenticate_header()`, and the app's custom `JWTAuthentication`
doesn't. Wrote the tests assuming 401 (the more common REST convention),
watched 7 of them fail identically, confirmed the cause by reading DRF's
`exception_handler` source directly rather than guessing, then fixed the
assertions. Autonomous commit mode absorbed this without stopping — it's
exactly the "found something the plan didn't anticipate, but not judgment
enough to warrant asking" case, as opposed to `test-implement`'s one named
guardrail (stop and ask when implementation hits something *unanticipated
in a way that needs a decision*, not just a wrong assumption to correct
against ground truth already in the code).

The 403-not-401 thread came back in Phase 3 and needed correcting a second
time. Phase 2 had found "missing credentials → 403" and recorded that as
the fact. Writing Phase 3's JWT-handling tests (malformed/expired/
nonexistent-user/inactive-user tokens) assumed those would be genuine 401s,
since `JWTAuthentication._authenticate_credentials` explicitly raises
`AuthenticationFailed`, a 401-status exception by default. All five failed
identically. Reading `APIView.handle_exception` directly (rather than
guessing again) showed the coercion to 403 is unconditional — both
`NotAuthenticated` and `AuthenticationFailed` get flattened by the same
`get_authenticate_header()` check, regardless of which one was raised or
why. Rewrote CONTEXT.md's note to state the general rule instead of the
narrower one Phase 2 had recorded. Worth flagging on its own: a note
written mid-plan from a narrower vantage point can be *correct but
incomplete* rather than wrong, and a later phase broadening it isn't the
same failure mode as Phase 2's outright-wrong 401 guess — both still
needed the same fix-in-place response under autonomous mode, since nothing
here rose to the level `test-implement`'s stop-and-ask guardrail is meant
for.

## CONTEXT.md growth during implementation

TEST-PLAN-CONTEXT.md's architecture section predicts CONTEXT.md grows
during implementation "the same way TESTING.md already does" — a routing
quirk found while implementing a phase, a version-compatibility ceiling hit
while setting up the runtime, and similar discoveries folded in as they
happen. Tracking here whether that actually occurs, or whether — like
TESTING.md's coverage-state checklist — it's TESTING.md that ends up doing
most of the real-time updating while CONTEXT.md stays closer to static
reference material once the initial stub is written.

Through Phase 0 and Phase 1: neither needed a CONTEXT.md edit — both real
discoveries in those phases (the Profile-fixture wrinkle, the Phase 1/3
mismatch) were process/plan findings, which belong here, not in
CONTEXT.md's domain-vocabulary/app-facts scope. That held only until Phase
2 turned up an actual app-behavior fact (the 403-not-401 status code on
every `IsAuthenticated` endpoint) — added to CONTEXT.md's new "API
behavior notes" section immediately, alongside the two original quirks.
So the more precise version of the hypothesis holds: CONTEXT.md's growth
really is gated on hitting a new fact about the *app* specifically, not on
phase count or elapsed time — Phase 0/1 didn't surface one, Phase 2 did,
and the file only moved when that happened.

Phase 3 adds a wrinkle to that: it didn't just add to CONTEXT.md, it
*rewrote* an existing entry — the 403-not-401 note went from "missing
credentials only" to "every auth-failure mode, unconditionally" (see
Commit-mode fidelity above). TESTING.md's growth so far has been purely
additive (checklist ticks, new coverage-note lines); CONTEXT.md's first
edit past the initial stub was a correction, not an addition. Worth
watching whether that's a coincidence of this specific fact (status-code
behavior tested piecemeal across two phases) or a real difference in kind
between the two docs — TESTING.md tracks what's been covered, which only
grows, while CONTEXT.md tracks what's true about the app, which can turn
out to have been incompletely understood the first time it was written
down.
