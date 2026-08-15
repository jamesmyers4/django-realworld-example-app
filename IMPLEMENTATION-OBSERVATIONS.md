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

*(filled in as each phase completes)*

## Commit-mode fidelity

Recorded answer: autonomous commit-as-you-go, no stop-for-review. Watching
for: does that actually hold once a phase turns out to need judgment calls
mid-stream (e.g. a fixture design decision not spelled out in TEST-PLAN.md)?

*(filled in as phases land)*

## CONTEXT.md growth during implementation

TEST-PLAN-CONTEXT.md's architecture section predicts CONTEXT.md grows
during implementation "the same way TESTING.md already does" — a routing
quirk found while implementing a phase, a version-compatibility ceiling hit
while setting up the runtime, and similar discoveries folded in as they
happen. Tracking here whether that actually occurs, or whether — like
TESTING.md's coverage-state checklist — it's TESTING.md that ends up doing
most of the real-time updating while CONTEXT.md stays closer to static
reference material once the initial stub is written.

*(filled in as phases land)*
