# Agentic MLOps Platform — Step‑by‑Step Implementation Plan (MVP)

**Version:** 1.0  
**Date:** 2025‑08‑17  
**Purpose:** A detailed, incremental plan to implement the MVP using **AWS App Runner + RDS + S3**, **LangGraph**, and a dual‑provider LLM design (orchestration vs codegen).  
**Style Note:** Structured to mirror the attached reference plan with phases, Issues, acceptance criteria, testing procedures, and GitHub mapping.

---

## 1) Strategy Overview
- **Incremental Delivery:** Each phase ends with working functionality and a demoable surface.
- **Determinism & Auditability First:** Typed state, checkpoints, event log, git‑backed diffs.
- **User Trust:** Reason Cards, policy & cost critics, HITL gate before codegen.
- **Cloud Footprint (MVP):** App Runner (web + worker), RDS Postgres (+ Proxy), S3 artifacts, CloudWatch logs.
- **GitHub Management:** Issues labeled by priority/component, grouped under milestones (**Phase 1 → Phase 5**) and a single **Projects v2 board**: *MVP Delivery*.

> **Repo layout (high level)**
```
repo/
├─ api/                # FastAPI (web service)
├─ worker/             # LangGraph runner
├─ libs/               # shared models, providers, policies
├─ infra/              # IaC for App Runner, RDS, S3, IAM
├─ tests/              # unit/integration/e2e/golden
├─ docs/               # user/dev docs
└─ tools/              # scripts, data generators, test fixtures
```

---

## 2) Phases at a Glance
- **Phase 1 – Foundations (Week 1‑2):** Repo scaffolding, CI, App Runner hello‑world, DB migrations, S3 bucket.
- **Phase 2 – Persistence & Jobs (Week 2‑3):** Typed state schema, PostgresSaver checkpoints, events table, DB‑backed job queue & worker loop, idempotency.
- **Phase 3 – Graph Core & Intake (Week 3‑4):** Deterministic LangGraph, Adaptive Intake (freeform → targeted Qs), SSE heartbeat channel.
- **Phase 4 – Planning → Critics → Policy → HITL (Week 4‑5):** Planner, technical & cost critics, policy evaluation, review UI & approval API.
- **Phase 5 – Codegen, Validators, Diffs & Reports (Week 5‑6):** Codegen provider, static validators, git + state diffs, artifact bundle, golden runs.
- **Phase 6 – Observability, Auth, Budgets & Hardening (Week 6‑7):** Logs, traces, OIDC authZ, budgets/rate‑limits, release gates.

> Each Issue below lists: **Epic**, **Labels**, **Milestone**, **Project**, **Acceptance Criteria**, **Testing**, **Definition of Done**.

---

## Phase 1 — Foundations (Week 1‑2)

### Issue #1: Repository & CI/CD Scaffolding
**Epic:** Foundations  
**Labels:** `setup`, `backend`, `p0-critical`  
**Milestone:** Phase 1 – Foundations  
**Project:** MVP Delivery  
**Acceptance Criteria**
- Monorepo structure created; Python toolchain pinned (uv/poetry + Python 3.11).
- Pre‑commit with ruff, black, mypy; GitHub Actions running unit tests & linters.
- Base FastAPI app with `/healthz` and version endpoint; basic README.
**Testing**
- `pytest -q`, lints pass; CI runs on PR and main.
**DoD**
- CI green on main; contributors can run api locally via `uvicorn api.main:app`.

### Issue #2: AWS Bootstrap (App Runner Hello‑World)
**Epic:** Foundations  
**Labels:** `deployment`, `infra`, `p0-critical`  
**Milestone:** Phase 1 – Foundations  
**Project:** MVP Delivery  
**Acceptance Criteria**
- App Runner service for **api** with HTTPS; environment secrets via SSM/Env.
- App Runner **worker** service skeleton (no jobs yet) can pull container.
- S3 bucket (artifacts) + RDS Postgres instance (with RDS Proxy) provisioned.
**Testing**
- `curl https://<api>/healthz` → 200; CloudWatch shows structured JSON logs.
**DoD**
- IaC committed; one‑button deploy (GitHub Actions) to staging.

### Issue #3: Base Data Models & Migrations
**Epic:** Foundations  
**Labels:** `database`, `backend`, `p0-critical`  
**Milestone:** Phase 1 – Foundations  
**Project:** MVP Delivery  
**Acceptance Criteria**
- Alembic initialized; tables: `projects`, `decision_sets(version)`, `events`, `artifacts`.
- CRUD endpoints for `projects`; optimistic locking field on `decision_sets`.
**Testing**
- `alembic upgrade head` on fresh DB; unit tests for model round‑trip.
**DoD**
- Migrations reproducible; DB URL only in secrets store.

---

## Phase 2 — Persistence & Jobs (Week 2‑3)

### Issue #4: Checkpointing with LangGraph PostgresSaver
**Epic:** Persistence  
**Labels:** `langgraph`, `backend`, `p0-critical`  
**Milestone:** Phase 2 – Persistence & Jobs  
**Project:** MVP Delivery  
**Acceptance Criteria**
- Add `PostgresSaver` checkpointer; `thread_id = decision_set_id`.
- Save/restore works across restarts with minimal demo graph.
**Testing**
- Unit test that injects state → checkpoint → reload → state equal.
**DoD**
- Checkpoints visible in DB; metrics/logs include `thread_id`.

### Issue #5: Event Log & Timeline API
**Epic:** Persistence  
**Labels:** `backend`, `api`, `p1-high`  
**Milestone:** Phase 2 – Persistence & Jobs  
**Project:** MVP Delivery  
**Acceptance Criteria**
- `events` table with `(event_id, decision_set_id, checkpoint_id, type, payload_jsonb)`.
- `GET /decision-sets/{id}/events` returns timeline; basic pagination.
**Testing**
- API test creates mock events; fetch & assert order, types, payload schema.
**DoD**
- Events show in staging timeline UI (temporary DevPage).

### Issue #6: DB‑Backed Job Queue + Worker Loop (SKIP LOCKED)
**Epic:** Jobs  
**Labels:** `worker`, `database`, `p0-critical`  
**Milestone:** Phase 2 – Persistence & Jobs  
**Project:** MVP Delivery  
**Acceptance Criteria**
- `jobs` table with priority, retries, backoff, lease fields.
- Worker claims jobs with `FOR UPDATE SKIP LOCKED` + leases; retry policy.
- Health endpoint for worker (in‑process metrics).
**Testing**
- Concurrency test: enqueue N jobs; start 2+ workers; assert single execution each.
- Fault‑injection: kill worker mid‑run → job re‑claimed after lease expiry.
**DoD**
- No duplicate processing under contention; metrics visible.

### Issue #7: Idempotency & Side‑Effect Guards
**Epic:** Persistence  
**Labels:** `backend`, `resilience`, `p1-high`  
**Milestone:** Phase 2 – Persistence & Jobs  
**Project:** MVP Delivery  
**Acceptance Criteria**
- `agent_runs` table storing per‑node `idem_key` and outputs.
- S3 object keys include content hash; duplicate writes harmless.
**Testing**
- Simulate retry; worker reuses cached result; S3 write not duplicated.
**DoD**
- Idempotent node execution verified in integration test.

---

## Phase 3 — Graph Core & Intake (Week 3‑4)

### Issue #8: Deterministic Graph Topology
**Epic:** Graph  
**Labels:** `langgraph`, `backend`, `p0-critical`  
**Milestone:** Phase 3 – Graph & Intake  
**Project:** MVP Delivery  
**Acceptance Criteria**
- Nodes wired in fixed order: `intake_extract → coverage_check → adaptive_questions? → planner → critic_tech → critic_cost → policy_eval → gate_hitl → codegen → validators → rationale_compile → diff_and_persist`.
- Runtime config passes a `StreamWriter` to nodes.
**Testing**
- Unit test executes entire happy path with stubs; asserts node order & outputs.
**DoD**
- Graph can run end‑to‑end with mock providers.

### Issue #9: Adaptive Intake (Freeform → Targeted Qs)
**Epic:** Intake  
**Labels:** `backend`, `langgraph`, `p1-high`  
**Milestone:** Phase 3 – Graph & Intake  
**Project:** MVP Delivery  
**Acceptance Criteria**
- Constraint schema & coverage score; ask minimal follow‑ups when below threshold.
- Interrupt gate for user answers; resume merges constraints.
**Testing**
- Unit: missing `budget_band` triggers a single follow‑up; state updated after resume.
**DoD**
- Demo flow: user text → constraints filled → planner entry conditions satisfied.

### Issue #10: SSE Streaming Channel with Heartbeats
**Epic:** UX Transparency  
**Labels:** `backend`, `api`, `p0-critical`  
**Milestone:** Phase 3 – Graph & Intake  
**Project:** MVP Delivery  
**Acceptance Criteria**
- `GET /streams/{decision_set_id}` streams `reason-card`, `policy-update`, `cost-update`, `diff-update`, `gate-waiting`, `run-error`, `run-complete`.
- Heartbeat `event: ping` every 10s; disconnect sets `stream_abandoned=true`.
**Testing**
- E2E test subscribes, verifies event sequence & heartbeat; simulate disconnect & resume via `/decision-sets/{id}/events`.
**DoD**
- Basic Dev UI displays streamed Reason Cards in a timeline.

---

## Phase 4 — Planner → Critics → Policy → HITL (Week 4‑5)

### Issue #11: Provider Abstractions (Orchestration & CodeGen)
**Epic:** Providers  
**Labels:** `backend`, `resilience`, `p0-critical`  
**Milestone:** Phase 4 – Planning & Policy  
**Project:** MVP Delivery  
**Acceptance Criteria**
- `OrchestrationProvider` + `CodeGenProvider` interfaces; temperature fixed; few‑shot pack registry by content hash; circuit breakers and fallbacks (non‑codegen).
- All LLM outputs validated via Pydantic models with retry‑on‑validation‑error.
**Testing**
- Provider stub & failure injection tests; ensure fallback and breaker cooldowns.
**DoD**
- Providers pluggable via env; telemetry (model, tokens, latency) logged.

### Issue #12: Planner (Capability Patterns)
**Epic:** Planning  
**Labels:** `backend`, `langgraph`, `p1-high`  
**Milestone:** Phase 4 – Planning & Policy  
**Project:** MVP Delivery  
**Acceptance Criteria**
- Compose plan from capability patterns (ingest/transform/store/feature/train/serve/observe/govern) under constraints.
- Output structured `Plan` model + candidate options.
**Testing**
- Golden input yields stable Plan; schema validation passes.
**DoD**
- Planner emits Reason Card with options considered and choice rationale.

### Issue #13: Critics (Technical & Cost)
**Epic:** Planning  
**Labels:** `backend`, `analysis`, `p1-high`  
**Milestone:** Phase 4 – Planning & Policy  
**Project:** MVP Delivery  
**Acceptance Criteria**
- Technical critic flags feasibility, coupling, failure domains.
- Cost critic emits `cost_estimate {monthly_usd, breakdown, method}` and deltas vs previous.
**Testing**
- Unit tests over mock BOMs; delta math verified; errors surface as Reason Cards.
**DoD**
- Critics stream updates; cost deltas visible in UI.

### Issue #14: Policy Engine (Pass/Warn/Fail)
**Epic:** Governance  
**Labels:** `backend`, `policy`, `p0-critical`  
**Milestone:** Phase 4 – Planning & Policy  
**Project:** MVP Delivery  
**Acceptance Criteria**
- Rules over constraints & plan: latency SLO, regions, budget band, data‑class.
- Aggregate `overall` with rule details; export to `/reports/policy.json`.
**Testing**
- Table‑driven tests for rules; regression suite for policy outcomes.
**DoD**
- Policy streamed before HITL; failures block codegen.

### Issue #15: HITL Gate & Approval API
**Epic:** Review  
**Labels:** `backend`, `api`, `p0-critical`  
**Milestone:** Phase 4 – Planning & Policy  
**Project:** MVP Delivery  
**Acceptance Criteria**
- Interrupt node waits for approval; `POST /decision-sets/{id}/approve {status, comment}` persists to `approvals` and resumes graph.
- Inline comments merged back into constraints before codegen.
**Testing**
- E2E: approval unblocks; rejection halts; comments appear in next Reason Card.
**DoD**
- Review loop usable from Dev UI.

---

## Phase 5 — Codegen, Validators, Diffs & Reports (Week 5‑6)

### Issue #16: Code Generation (Repo Skeletons)
**Epic:** Codegen  
**Labels:** `backend`, `codegen`, `p0-critical`  
**Milestone:** Phase 5 – Codegen & Diffs  
**Project:** MVP Delivery  
**Acceptance Criteria**
- Generate Python services (FastAPI), Terraform, GitHub Actions, docs.
- Write bundle to S3 under content‑hash paths; record in `artifacts`.
**Testing**
- Unit: manifest contains expected files; integration: S3 URLs signed and downloadable.
**DoD**
- Artifact zip downloadable; hash recorded; re‑runs produce same hash for same plan.

### Issue #17: Static Validators & Reports
**Epic:** Quality  
**Labels:** `backend`, `validation`, `p1-high`  
**Milestone:** Phase 5 – Codegen & Diffs  
**Project:** MVP Delivery  
**Acceptance Criteria**
- Run `ruff`, `mypy`, `pytest -q` (templates), `terraform validate`, secret scan.
- Export `/reports` (policy, cost, validators) into the artifact bundle.
**Testing**
- CI step executes validators; failing checks block artifact publish.
**DoD**
- `/reports` present and linked from UI.

### Issue #18: Diff‑First Persistence (State + Git)
**Epic:** Diffs  
**Labels:** `backend`, `git`, `p1-high`  
**Milestone:** Phase 5 – Codegen & Diffs  
**Project:** MVP Delivery  
**Acceptance Criteria**
- Server‑side git repo per project; commit plan/docs/manifest each version.
- API returns composite Change Summary: state DeepDiff + unified git diff + cost delta.
**Testing**
- Golden v1→v2 run yields deterministic diff; cost delta matches critic output.
**DoD**
- UI shows versioned diffs and cost change.

### Issue #19: Reason Cards & Rationale Export
**Epic:** UX Transparency  
**Labels:** `backend`, `api`, `p1-high`  
**Milestone:** Phase 5 – Codegen & Diffs  
**Project:** MVP Delivery  
**Acceptance Criteria**
- Each node emits a Reason Card (agent, inputs, candidates, choice, policy, cost, confidence, risks, links).
- Export rationale to `/reports/rationale.json` and embed in docs.
**Testing**
- Schema validation on Reason Cards; SSE payload snapshot tests.
**DoD**
- Timeline shows cards; download includes rationale bundle.

---

## Phase 6 — Observability, Auth, Budgets & Hardening (Week 6‑7)

### Issue #20: Observability (CW Logs + LangSmith)
**Epic:** Ops  
**Labels:** `monitoring`, `telemetry`, `p1-high`  
**Milestone:** Phase 6 – Hardening  
**Project:** MVP Delivery  
**Acceptance Criteria**
- Structured logs (request_id, run_id, thread_id, node_name, model, tokens, latency_ms).
- LangSmith tracing enabled per env; basic CloudWatch dashboards.
**Testing**
- Trigger runs; confirm correlation across logs & traces.
**DoD**
- On‑call can trace a bad output to a node and provider call.

### Issue #21: AuthN/AuthZ & Tenancy
**Epic:** Security  
**Labels:** `security`, `auth`, `p0-critical`  
**Milestone:** Phase 6 – Hardening  
**Project:** MVP Delivery  
**Acceptance Criteria**
- OIDC (Cognito/Auth0); JWT required on APIs & SSE; project‑scoped checks.
- S3 prefixes `projects/{project_id}/…`; DB queries always filter by `project_id`.
**Testing**
- Unauthorized requests rejected; cross‑tenant access tests fail as expected.
**DoD**
- Security review sign‑off; minimal RBAC documented.

### Issue #22: Budgets, Rate Limits & Cost Gating
**Epic:** Governance  
**Labels:** `policy`, `cost`, `p1-high`  
**Milestone:** Phase 6 – Hardening  
**Project:** MVP Delivery  
**Acceptance Criteria**
- Per‑project token/concurrency budgets; soft warn at 80%, hard stop at 100%.
- Gate: require HITL if Δcost exceeds thresholds; show delta in Change Summary.
**Testing**
- Simulate budget exhaustion; verify gate stops codegen and surfaces warning.
**DoD**
- Budget & cost deltas visible in UI and logs.

### Issue #23: Golden Runs, Determinism Budget & Quarantine
**Epic:** Quality  
**Labels:** `testing`, `resilience`, `p1-high`  
**Milestone:** Phase 6 – Hardening  
**Project:** MVP Delivery  
**Acceptance Criteria**
- Golden prompts & expected schemas; determinism budget (N retries then fail).
- Invalid payloads captured to quarantine bucket for triage.
**Testing**
- CI job runs golden suite; failure blocks release; quarantine populated on schema drift.
**DoD**
- “Release gate” requires green golden & validators.

### Issue #24: Artifact Ergonomics & Lifecycle
**Epic:** Ops  
**Labels:** `backend`, `storage`, `p2-medium`  
**Milestone:** Phase 6 – Hardening  
**Project:** MVP Delivery  
**Acceptance Criteria**
- Signed S3 URLs with TTL; lifecycle policy to expire zips after N days.
- `/reports` index page in bundle; secret scan blocks publish on hits.
**Testing**
- URL expires; secret scanner flags seeded token in a test artifact.
**DoD**
- Download experience consistent; zero secrets in artifacts.

---

## 3) Verification Matrix (by Phase)
**Phase 1**
- CI green; App Runner reachable; migrations apply on clean DB.
**Phase 2**
- Checkpoints survive restarts; jobs process exactly once; events visible.
**Phase 3**
- Intake closes required gaps; SSE stream & resume; minimal Dev UI works.
**Phase 4**
- Plan → critics → policy produce coherent artifacts; HITL pauses/resumes.
**Phase 5**
- Codegen bundle validated; diffs accurate; rationale exported.
**Phase 6**
- Logs/traces correlated; auth & tenancy enforced; budgets operate; golden suite stable.

---

## 4) GitHub Project Mapping
- **Project:** *MVP Delivery* (Projects v2) with views: Board, Roadmap, Risks.
- **Milestones:** Phase 1 … Phase 6 with due dates aligned to weeks.
- **Labels:** `p0-critical`, `p1-high`, `p2-medium`, `backend`, `worker`, `langgraph`, `policy`, `codegen`, `security`, `testing`, `infra`, `api`, `git`, `diffs`, `monitoring`.
- **Automation:** Auto‑move issues on PR open/merge; status field sync from CI checks.

---

## 5) Test Suites & Commands
- **Unit:** `pytest -q`, fast model/schema tests; provider stubs.
- **Integration:** `pytest -m integration` (API + DB + S3 containers).
- **End‑to‑End:** Playwright/Locust scripts for SSE + approval flows.
- **Golden:** `pytest tests/golden` seeds fixed inputs & snapshot Reason Cards.
- **Security/Static:** ruff, mypy, bandit, pip‑audit, `terraform validate`, secret scan.

---

## 6) Exit Criteria (MVP)
- p95 plan round‑trip ≤ 2 min; artifact ≤ 5 min.
- Positive HITL review loop; bundles downloadable; diffs & cost deltas clear.
- Auth on; budgets/rate limits enforced; golden suite green; dashboards active.

---

## 7) Appendices
- **A. SSE Event Contract**: `reason-card`, `policy-update`, `cost-update`, `diff-update`, `gate-waiting`, `run-error`, `run-complete`; 10s heartbeats.
- **B. Reason Card Schema (summarized)**: agent, inputs, candidates, choice, policy, cost, confidence, risks, links.
- **C. Policy Rules (starter set)**: latency SLO, budget band, region policy, data‑class.
- **D. Cost Method Tag**: `method: bom_v1` + deltas vs previous.

> **Notes:** This plan assumes OpenID Connect auth in Phase 6 and reserves RBAC, apply‑mode, and full lineage for post‑MVP releases. 

