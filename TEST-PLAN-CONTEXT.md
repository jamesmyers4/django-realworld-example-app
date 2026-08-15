# TEST-PLAN-CONTEXT.md — Test Automation Planner (working title)

## Status

v0.2. Revised after two live dogfeeding runs: Shenny (2026-08-14, gap-closure sequencing) and `django-realworld-example-app` (2026-08-14, bootstrap sequencing). Previously named CONTEXT.md.

## Revision log

- **v0.2 (this revision).** Incorporated findings from the `django-realworld-example-app` run: added "not applicable" as a third resolution path for always-ask questions with no live referent (distinct from "the repo already answered this"); added a conditional Runtime Viability Check pre-step for repos that don't already run; reframed the authorization/boundary-testing taxonomy entry to explain _why_ it gets sequenced early, not just that it's commonly skipped; required recommended defaults to be presented as pre-selectable options in the interview, not free text; clarified that CONTEXT.md is created (even as a minimal stub) during the planning session itself when none exists, and is expected to grow during implementation the same way TESTING.md already does. Also added a phase-sizing floor note (single-sitting sizing remains the default even under "let the plan decide") and a rule for security-relevant infer-but-confirm items, both from reviewing the plan itself rather than the run's self-reported feedback.
- **v0.1.** Incorporated five findings from the Shenny run.
- **v0.** Initial design-session output. Not yet run against anything.

## What this is

A Claude Skills plugin that assesses a codebase (existing or greenfield) and produces a governing test automation plan — the process and judgment calls a QA lead makes doing a test-automation intake, encoded as something repeatable rather than one-off consulting. The deliverable of a planning run is a document Claude Code can execute against in phased, committable sessions, plus a living doc that stays current as implementation proceeds.

## What this isn't

Not another "write me a test" generator. Several of those already exist — Playwright spec generators, Jest-to-Vitest migration skills, framework-specific test writers. This project sits a layer above that: it decides _what_ needs coverage, _in what order_, _with which tools_, and _under what constraints the dev actually has_ — the judgment work, not the typing work.

## Vocabulary

- **Planning session** — the pass where `test-plan` scans the repo, resolves the three-tier discipline, interviews the dev on what can't be inferred, and writes TEST-PLAN.md.
- **Implementation session** — a `test-implement` run that reads TEST-PLAN.md, executes the next open phase, and updates TESTING.md. Not yet exercised by either dogfeeding run so far — both have only stress-tested `test-plan`.
- **Three-tier discipline** — the rule set governing what gets inferred silently, confirmed with the dev, or must be asked outright.
- **Runtime viability check** — a conditional pre-step: confirming the app can actually run at all (and on what runtime version) before anything else proceeds. Only fires when the app doesn't already run; most real repos skip it entirely.
- **Golden master** — a checked-in snapshot of current, pre-existing, deterministic behavior used as a baseline when there's no spec to test against. Scoped narrowly to deterministic behavior — see the taxonomy entry below for how it relates to non-deterministic AI output.
- **Coverage sweep** — the completeness pass across the full taxonomy, done _before_ any sequencing decision.
- **TEST-PLAN.md** — the planning session's output. Phases, decisions, interview answers, sequencing. Written once, revised occasionally, not continuously updated.
- **TESTING.md** — the living doc. Created and updated during implementation sessions: current coverage state, how to run the suite, conventions, open findings.

## Architecture — the skills

### `test-plan` (user-invoked)

Does the scan, the coverage sweep, the three-tier resolution, the interview, and the sequencing pass. Writes TEST-PLAN.md. **Creates a CONTEXT.md — even a minimal stub, if the repo has none — during the planning session itself, not deferred to implementation.** It's expected to grow during implementation sessions the same way TESTING.md already does: a routing quirk found while implementing a phase, a version-compatibility ceiling hit while setting up the runtime, and similar discoveries get folded in as they happen rather than waiting for a dedicated pass. Touches an existing CLAUDE.md or CONTEXT.md only with explicit confirmation. Internally organized around domain-specific reference files (see Stack reference matrix) rather than one skill per domain — the domains aren't independent, a DB choice affects both API test-data strategy and E2E seeding, and a single pass reasoning across all of it avoids stitching together disconnected assessments afterward.

### `test-implement` (user-invoked, thin)

Opens TEST-PLAN.md, finds the next unchecked phase, executes it under whatever commit-mode was recorded during planning, updates TESTING.md and CONTEXT.md as it goes. Most of its value is discoverability plus one guardrail: if implementation hits something the plan didn't anticipate, stop and ask rather than guess. **Not yet exercised by any dogfeeding run** — both runs so far only produced a TEST-PLAN.md by hand-following the planning process; nothing has actually executed a phase yet.

### `test-maintain` (model-invoked, tiny)

"If this repo has a TESTING.md, read it before touching test code." No dedicated command. Per skill-creator guidance, model-invoked skills tend to undertrigger — this one will need real trigger evals once it exists, not just a plausible-sounding description.

## Process — `test-plan`

0. **Runtime viability check (conditional).** Only fires if the app doesn't already run. Attempt the app's existing build/run commands; if they fail, diagnose why (missing dependency, incompatible language-runtime version against a pinned framework version, etc.) and record the finding — including the actual compatibility ceiling if one exists — rather than silently picking a version or auto-installing anything. Most real repos skip this step entirely, since having a running app is usually a precondition for someone caring about adding tests in the first place.
1. **Scan.** Read the repo before asking anything. Languages, frameworks, existing test config, CI config, folder conventions.
2. **Coverage sweep.** Walk the full taxonomy and inventory what needs coverage and what already has it. This step is about completeness, not order. For E2E and BDD layers specifically, verifying coverage means reading test titles and selector/page-object usage inside the files, not diffing directory listings against the taxonomy. Any claim in the repo's own docs about cross-suite correspondence is a hypothesis to verify, not a fact to inherit.
3. **Three-tier resolution.** For everything found in step 2, resolve it via the discipline below.
4. **Interview.** Ask whatever step 3 flagged as always-ask. Recommended defaults are presented as pre-selectable options, not open-ended free text — this is a requirement for how the interview is presented, not just a nice-to-have; it's what keeps a several-question interview down to a handful of quick selections instead of essay answers.
5. **Sequencing pass.** Decide phase order using the sweep and interview answers — see the two named modes below.
6. **Write TEST-PLAN.md.** Phases, decisions, interview answers (including anything requiring manual external setup, flagged clearly), sequencing.
7. **Touch adjacent docs per the collision policy** — extend CLAUDE.md and an existing CONTEXT.md only with explicit confirmation; create a minimal CONTEXT.md stub if none exists at all (not gated behind confirmation, since there's nothing to overwrite); handle any existing TESTING.md-equivalent per its own policy below.

## Three-tier inference discipline

- **Always infer, never ask** — languages and frameworks in use, existing test runner config, CI config, folder conventions. Reading `package.json` / `.csproj` / CI YAML, not judgment.
- **Infer, but confirm** — anything that looks unintentional, half-finished, or buggy. Flag it ("found X — intentional, or a known issue?") rather than testing the bug as if it were spec, or silently guessing which one it is. **When the flagged item is security-relevant rather than merely quirky** (an authorization gap versus, say, a reference-equality bug that happens to work by coincidence), the resulting test should default to a treatment that can't be mistaken for a clean pass — an `xfail` with a reason, or a test explicitly named to flag the known issue (`test_KNOWN_BUG_no_ownership_check`, for example) — rather than a plain green assertion of current behavior. This matters most precisely when commit mode is autonomous and nothing is necessarily reviewed before landing.
- **Never infer, always ask** — team size, risk tolerance, budget for paid tooling, timeline, whether the codebase is pre-launch or production-critical, and the interview question set below. Two carve-outs:
  - **Already documented.** If the repo has already unambiguously documented an answer to a specific always-ask question in its own docs, don't pose it as a blank open question — treat it like infer-but-confirm instead: state the inferred answer, cite the source, and ask only for correction.
  - **Not applicable.** Some of these questions assume a live team and product roadmap behind the repo at all — team size, budget, timeline, pre-launch-vs-production. For a fixed archival, teaching, or QA-target repo, there may be no team to ask and no launch to plan around. In that case the answer isn't inferred _or_ asked — it's marked not applicable, with one line of stated reasoning, rather than silently dropped or asked as if a real answer were expected.

## Coverage taxonomy

- Unit tests
- Integration / API contract tests
- E2E happy path
- Edge, negative, and boundary cases
- Accessibility (WCAG / Section 508)
- **Golden master / characterization** — for pre-existing, _deterministic_ behavior with no real spec to test against. Narrowly scoped: pinning exact output as correct-by-definition. Related to, but distinct from, AI/LLM output testing below — same underlying motivation, different technique, because the failure mode flips when output is expected to legitimately vary between runs.
- **Authorization / boundary testing** — can role or tenant A see or act on role or tenant B's data. Disproportionately likely to contain a real, currently-shipping bug when it hasn't been tested — not merely a commonly-skipped category, but one where the absence of coverage and the presence of an actual defect tend to go together. Sequence it earlier than typical edge-case work in a bootstrap run for that reason, not only because it's often missed.
- Cross-browser / responsive
- **AI/LLM pipeline output testing** — for pipelines with non-deterministic output. Reusable pattern (generalized from Drover's Grader subsystem): treat this as grading pre-supplied `{input, output, rubric}` triples via LLM-as-judge — the test doesn't generate the output itself, an adapter or fixture supplies input/output pairs, and grading is a pure function over them. Use more than one judge model or model-family per check rather than a single judge, to guard against single-model bias. Keep hosted-API-cost grading opt-in or scheduled, not blocking on every push, and gate escalation to a hosted judge behind an explicit data-sensitivity flag if the content being graded could be sensitive. A "skipped" outcome is a legitimate first-class result for a check, not a failure.
- Visual regression — optional, flagged rather than default-on (tooling/cost overhead)
- Performance / load — optional, flagged rather than default-on, same reasoning

## Interview question set

| Question                                                                      | Asked when                                                               | Recommended default                                                    | Notes                                                                                                                                                      |
| ----------------------------------------------------------------------------- | ------------------------------------------------------------------------ | ---------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Commit/review mode — manual review per commit, or autonomous commit-as-you-go | Always                                                                   | Manual review on the first plan; autonomous once trust is established  | Recorded in TEST-PLAN.md, read by `test-implement`                                                                                                         |
| CI schedule                                                                   | Always                                                                   | PR-gated smoke/unit, scheduled nightly full regression                 | Flag anything needing an external account or manual setup                                                                                                  |
| BDD/Cucumber-style layer                                                      | When the repo has non-technical stakeholders or ambiguous business rules | Skip by default                                                        | Real authoring overhead — recommend only when it's earning its keep                                                                                        |
| Temp/test DB strategy                                                         | When a real DB is in the stack                                           | Ephemeral container (Testcontainers or equivalent)                     | SQLite-in-memory only when the app itself already runs on SQLite                                                                                           |
| Coverage depth / risk tolerance                                               | Always                                                                   | Thorough on core paths, smoke-only on low-risk or rarely-changed areas | Feeds directly into sequencing                                                                                                                             |
| Session/runway budget                                                         | Always                                                                   | No universal default — ask directly                                    | Sets `test-implement`'s checkpoint cadence. See phase-sizing note under Sequencing philosophy — "let the plan decide" is not license for unbounded phases. |
| Visual regression opt-in                                                      | When the repo has significant UI surface                                 | Off by default                                                         | Tooling and baseline-maintenance cost                                                                                                                      |
| Existing test-doc filename                                                    | When the repo already has one                                            | Prefer renaming to TESTING.md                                          | If declined, record the actual location as a pointer instead                                                                                               |

## Sequencing philosophy

Decided last, after the coverage sweep — not first. Two named modes, both now validated against a real run:

- **Bootstrap sequencing** — for repos where the sweep comes back mostly Gap. Fast, isolated, deterministic layers first (unit, API/integration), since they usually become fixtures the E2E layer reuses. Then integration, then E2E happy path, then edge cases and grey-area coverage, then optional layers last. Validated on `django-realworld-example-app`.
- **Gap-closure sequencing** — for repos where the sweep comes back mostly Covered. Order by: fix any stale baseline first, then novel/high-value gaps per the risk-tolerance answer, then CI-signal-timing gaps, then lower-stakes/smoke-tier items last. Validated on Shenny.

**Phase-sizing floor.** "No strong preference — let the plan decide" resolves _what_ defines a phase boundary (natural coverage boundaries versus a stated time-box) — it is not license for a phase to grow unbounded. Single-sitting-sized phases remain the implicit default even under this option; only the explicit "long sessions" answer licenses multi-phase-per-sitting sizing. Whether this is actually being respected in practice, or whether "let the plan decide" quietly produces an oversized first phase by default, is open — `django-realworld-example-app`'s Phase 0 (test-framework scaffolding, fixtures, a Docker test-runner target, and a full CI workflow all in one phase) is a plausible instance of the latter, but this can only really be confirmed once a phase is actually executed by `test-implement` rather than just planned.

**Resolved:** the exact bootstrap/gap-closure threshold remains open, but both modes are now real, validated outcomes rather than a theoretical split — one data point each, in opposite directions.

## Pre-existing doc handling

- **Existing TESTING.md-equivalent** — default is to suggest a rename for portability. If the dev wants to keep their own name, record the actual filename as a pointer instead of forcing it. If none exists, it's created during implementation, not planning.
- **Existing CLAUDE.md or CONTEXT.md** — per-file, explicit confirm: append a testing-vocabulary section, write a separate doc, or skip. Never silently overwrite a doc the dev already owns. **If no CONTEXT.md exists at all, create a minimal stub during the planning session** (not gated behind confirmation, since nothing is being overwritten) and expect it to grow during implementation as discoveries happen — see Architecture above.

## Stack reference matrix (seed)

Strategic shape comes first; this exists so it has somewhere to grow, not as an exhaustive catalog. Once `test-plan` is actually built, each row family becomes its own file under `references/`, loaded only when the scan finds a match.

### Common full-stack combinations (recognize-by-name)

Useful for the scan step to recognize an entire stack at once — a repo's `package.json`/lockfile/build-file combination usually maps directly onto one of these:

- **LAMP/LEMP** (Linux + Apache/Nginx + MySQL/MariaDB + PHP) — still the largest single population of live websites; low cost, huge legacy footprint, includes classic WordPress/Drupal-style CMS stacks.
- **Next.js + PostgreSQL** (+ Vercel, Prisma/Drizzle, Tailwind) — de facto modern default for new SaaS/web apps. Shenny's own family.
- **T3** (Next.js + TypeScript + tRPC + Prisma/Drizzle + Auth.js) — end-to-end-typed variant of the above, common among TS-first indie/startup teams.
- **JAMstack** (Next.js/Astro/SvelteKit + headless CMS + edge/CDN) — static-first, content/marketing-heavy sites.
- **MERN / MEAN / MEVN / PERN** — Node + Express + {React/Angular/Vue} + {MongoDB/Postgres}. PERN swaps Mongo for Postgres and leans more relational/enterprise than the others.
- **Python (FastAPI or Django) + Postgres** (+ React/Next.js frontend) — FastAPI leans async/model-serving/AI-adjacent backends; Django leans CRUD/admin-heavy apps. `django-realworld-example-app` is a real (if dated — Django 1.10) example of this family, API-only.
- **Laravel (PHP) + MySQL/Postgres** — modern PHP, frequently deployed on LAMP/LEMP infra underneath.
- **Ruby on Rails + Postgres** — convention-over-configuration, strong for MVP/full-featured SaaS.
- **.NET (ASP.NET Core + C#) + SQL Server/Postgres**, often paired with Angular, React, or Blazor — enterprise/government-heavy.
- **Java + Spring Boot + Postgres/Oracle**, paired with React/Angular — the enterprise/regulated-industry workhorse.
- **Nuxt (Vue) or SvelteKit** — full-stack meta-framework counterparts to Next.js.
- **Go + Postgres**, often behind a separate frontend — high-performance microservices/APIs/CLIs.
- **Phoenix (Elixir) + Postgres** (+ LiveView) — highly concurrent, minimal-JS real-time UIs.
- **Serverless/edge** (Cloudflare Workers, Vercel Edge, AWS Lambda + D1/Postgres/KV) — latency-sensitive, globally distributed.
- **AI-native/hybrid** (Python/FastAPI or Node orchestration + vector DB + LLM SDKs + React/Next.js frontend) — Shenny is a real example of this layered on top of Next.js.
- **Mobile** — React Native + Expo, Flutter, or native (Swift/SwiftUI, Kotlin/Jetpack Compose) for performance-critical or hardware-heavy apps.

Useful priors regardless of which combination a repo turns out to be: TypeScript has functionally superseded plain JS for serious new work, PostgreSQL is the leading relational choice among professional teams even where a stack's "classic" name says MySQL or Mongo, and Docker is close to universal. **For older or archived stacks specifically, the pinned framework version may cap the newest usable language-runtime version** — `django-realworld-example-app`'s pinned Django 1.10 tops out at Python 3.7 (3.8+ breaks on a `__classcell__`/metaclass change Django's Python-2/3 compat layer at that version doesn't survive) — which is exactly what the Runtime viability check step exists to catch and record.

### By domain (component-level detail once a combination is recognized)

**Frontend:** React (CRA/Vite), Next.js, Angular, Vue/Nuxt, Svelte/SvelteKit, static/vanilla, legacy jQuery
**Backend:** Node (Express/Fastify), .NET (ASP.NET Core), Python (Django/Flask/FastAPI), Java (Spring), Ruby on Rails, PHP (Laravel/legacy)
**Database:** PostgreSQL, SQL Server, MySQL, SQLite, MongoDB
**E2E:** Playwright (recommended default for anything modern); Selenium (legacy — migrate-in-place for new specs, don't rip out a working suite); Cypress (alternative, flag ecosystem overlap with Playwright)
**Unit/integration:** Vitest (recommended default, current JS/TS); Jest (legacy JS/TS, document a migration path); xUnit/NUnit/MSTest (.NET); pytest (Python — used for `django-realworld-example-app`'s Phase 0/1, alongside `pytest-django`); JUnit (Java); RSpec (Ruby)
**BDD/Cucumber-family:** Cucumber.js (JS/TS), Reqnroll/SpecFlow (.NET), behave (Python), Cucumber-JVM (Java) — gated behind the interview question, not default-on
**CI/CD:** GitHub Actions (default absent a strong reason otherwise), GitLab CI, Azure DevOps, CircleCI, Jenkins (legacy/on-prem)
**Environment/infra:** Docker Compose (default for ephemeral test environments), Kubernetes (namespace-based test environments for larger orgs), serverless/edge deploy targets (needs a preview-environment-based approach, not local container spin-up), Testcontainers (recommended default wherever a real DB needs to sit inside a test run)

## Open questions / ADR candidates

- Whether `test-plan` / `test-implement` should ship as two skills or collapse into one — current lean is two, thin.
- Project name and whether the skills get a shared namespace prefix once it's chosen.
- `test-maintain`'s trigger reliability — still unvalidated, needs real trigger evals once it exists.
- **`test-implement` itself is entirely unvalidated.** Both dogfeeding runs so far have only exercised `test-plan` — nothing has actually executed a phase, tested whether commit-mode fidelity holds (does autonomous mode really commit as it goes, does manual-review really stop), or watched CONTEXT.md/TESTING.md actually grow during implementation the way the architecture now says they should. This is arguably the highest-value next run, ahead of surveying a third stack.
- The bootstrap/gap-closure sequencing threshold — softened from fully open to "two validated data points, exact boundary still unknown."
- Phase-sizing floor under "let the plan decide" — see Sequencing philosophy. Needs an actual execution to confirm either way.
- Monorepo/multi-service handling — not yet exercised by any run.
- Distribution — Matt Pocock's `mattpocock/skills` ships via `npx skills add` plus the official `claude.com/plugins` marketplace. Precedent worth using later; not a v0 concern.

## Naming

Still open. Candidates in keeping with the one-word convention across Drover / Reeve / treeLine / Shenny: **Proctor**, **Marshal**, **Docket**, **Foreman**.

## Dogfeeding plan

### Run 1 — Shenny (complete)

Chosen because it already had mature test infrastructure and its own governing docs. Validated gap-closure sequencing and the three-tier discipline's core split. Findings folded into v0.1.

### Run 2 — django-realworld-example-app (complete)

Chosen as an unfamiliar-stack, archived, thin-test-coverage counterpart to Shenny — official Django implementation of the RealWorld/Conduit spec, archived since 2022, 16 unresolved open issues, no test suite. Validated bootstrap sequencing for the first time, surfaced real pre-existing bugs (a missing object-level authorization check, a reference-equality bug that happens to work by coincidence), and surfaced a real runtime-viability gap (a pinned 2016-era Django release capping the usable Python version) that the process had no place to record before this revision. Findings folded into v0.2.

### Next run — recommendation

Both runs so far have stress-tested `test-plan` only. `test-implement` has never actually executed a single phase. The strongest next move is likely running `test-implement` against one of the two existing plans (`django-realworld-example-app`'s bootstrap plan is the more interesting target, given it has six unexecuted phases and known bugs already flagged) rather than adding a third stack survey — several of the currently-open questions (phase-sizing floor, commit-mode fidelity, CONTEXT.md's during-implementation growth pattern) can only be resolved by watching something actually get built, not by writing another plan.
