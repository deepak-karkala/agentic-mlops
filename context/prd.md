# Agentic MLOps Platform – MVP Architecture, Deployment Options & Roadmap

**Version:** 0.9 (MVP-ready)  
**Author:** <your name / team>  
**Date:** 2025‑08‑15

---

## 1) Executive Summary
A collaborative, multi‑agent system that **designs, critiques, and generates** production‑quality MLOps systems. The MVP delivers a **comprehensive architecture report** plus a **code artifact bundle (repo zip)** covering services, IaC, CI, and validation reports—without deploying any cloud resources. The design emphasizes trust: policy checks, cost/latency critics, deterministic diffs, and typed state with an event log.

**Key decisions for MVP**
- Dual‑provider LLM stack: **Orchestration** (OpenAI Agents SDK or LangGraph) + **Code generation** (Anthropic Claude Code), behind a common provider interface.
- Deployment (recommended): **AWS App Runner (web) + App Runner (worker) + RDS Postgres + S3** with a DB‑backed job queue. Alternative options listed in §8.
- State: Postgres with **versioned decision sets**, **event log**, and **artifact hashes**.
- Trust features in MVP: **policy engine**, **two critics (tech & cost)**, **diff‑first UX (git‑backed)**, and **static validation** of generated repos.

---

## 2) Problem & Value Proposition
Teams waste weeks translating high‑level requirements into consistent, audited MLOps infrastructure. Our product turns **natural‑language constraints** into **reviewable designs & code** with explainability (critics), repeatability (events & diffs), and safety (policy checks), while preserving human control (HITL gates).

**Primary outcomes:**
- Hours → days from requirements to vetted repo.
- Traceable decision history; easy iteration on constraints.
- Vendor‑agnostic capability composition (not just pre‑canned pipelines).

---

## 3) Target Users & Representative Use Cases
- **Founding ML teams / Series A–B startups:** First production ML stack (RAG + batch training).
- **Platform teams in mid‑size enterprises:** Standardize patterns across clouds; generate compliant infra repos.
- **Consultancies / SIs:** Accelerate discovery → proposal → code artifacts.

---

## 4) Scope: MVP vs. Non‑Goals
**In‑scope (MVP)**
- Constraint intake → proposed architecture → policy/critic check → HITL approval → **repo generation (zip)**.
- Diffs across iterations; typed state and event log.
- Static validation (linters, schema checks, IaC validate) without cloud deploy.

**Out‑of‑scope (MVP)**
- Applying IaC, spinning cloud resources, running training/inference.
- Complex RBAC/e‑sign and full compliance automation (planned).
- Durable queue/broker beyond DB‑backed jobs (upgrade path defined).

---

## 5) Core Features (MVP)
1) **Constraint & Context Intake**  
   - Natural‑language input; extraction to a typed constraint schema: budget, regions, data‑class, latency/SLO, throughput, tooling prefs.

2) **Planning & Composition**  
   - Agents compose **capability patterns** (ingest, transform, store, feature, train, serve, observe, govern) per cloud.
   - Patterns are opinionated but composable; planner chooses under constraints.

3) **Critics & Policy Engine**  
   - **Technical critic:** checks feasibility, coupling, bottlenecks, failure domains.  
   - **Cost critic:** order‑of‑magnitude monthly estimate from patterns/IaC.  
   - **Policy engine:** latency/budget/region/PII rules → pass/fail report.

4) **Diff‑First UX**  
   - Git‑backed diffs for architecture docs, repo manifests, and cost deltas (USD + %).  
   - Summary of changes persists alongside every decision set.

5) **Repo Generation (Zip)**  
   - Python services (FastAPI skeletons), IaC (Terraform), GitHub Actions, sample tests.  
   - `/reports` folder: policy report, IaC validate output, lint/test summaries, SBOM.

6) **Typed State & Event Log**  
   - Postgres models for projects, decision sets, artifacts, agent runs, approvals, cost estimates, and events.

---

## 6) System Architecture (MVP)

```mermaid
flowchart TD
  U[User] -->|Constraints / Edits| API[FastAPI Web Service]
  API -->|enqueue| DB[(Postgres)]
  W[Worker Service] -->|poll jobs| DB
  W -->|LLM calls (orchestration)| Orchestrator[(OpenAI Agents SDK / LangGraph)]
  W -->|codegen| CodeGen[(Claude Code via Provider API)]
  W -->|repo & reports| S3[(S3 Artifacts)]
  W -->|events, decision sets, runs| DB
  API -->|diffs & reports| U
```

**Notes**
- Single worker process suffices for MVP; can scale horizontally later.  
- All long‑running tasks run in the worker; API remains responsive.  
- DB is the job queue (lightweight): `jobs` table with retries and backoff.

---

## 7) Data Model (Initial)
- `projects(id, name, owner_id, created_at, ...)`
- `decision_sets(id, project_id, parent_id, version, status, constraints_jsonb, plan_jsonb, summary_md, created_at, updated_at)`
- `artifacts(id, decision_set_id, path, sha256, kind, size_bytes, created_at)`
- `agent_runs(id, decision_set_id, agent, provider, model, input_jsonb, output_jsonb, tokens_total, latency_ms, ok, created_at)`
- `approvals(id, decision_set_id, gate, actor, status, comment, created_at)`
- `cost_estimates(id, decision_set_id, monthly_usd, breakdown_jsonb, method, created_at)`
- `events(id, decision_set_id, type, payload_jsonb, created_at)`
- `jobs(id, type, payload_jsonb, status, retries, next_run_at, created_at, updated_at)`

**Rules**
- Optimistic locking on `decision_sets`.  
- Every material change emits an `events` row.  
- All artifacts stored in S3 with SHA‑256 in DB for integrity and diffing.

---

## 8) Deployment Options (MVP‑friendly)

### Option A — **Vercel (API/UI) + tiny worker VM + RDS + S3**
- **What:** Keep Vercel for web; add one small VM/container (e.g., Fly.io/EC2 t4g.small) as a worker polling the DB.  
- **Pros:** Fastest to ship; minimal ops; good DX.  
- **Cons:** Two platforms; custom wiring for networking/secrets; egress between clouds; billing split.  
- **Fit:** Good for immediate demo/POC; less ideal for enterprise buyers.

### Option B — **AWS App Runner (recommended)**
- **What:** App Runner service for **FastAPI (web)** and a second App Runner service for the **worker**; **RDS Postgres**; **S3** for artifacts.  
- **Pros:** Fully managed build/deploy, HTTPS, autoscaling without cluster mgmt; single‑cloud story; simplest AWS path.  
- **Cons:** Limited background job primitives (we roll our own via DB); fewer knobs than ECS.  
- **Fit:** Best MVP trade‑off: low ops, unified cloud, straightforward scale to SQS later.

### Option C — **ECS on Fargate (web + worker) + RDS + S3**
- **What:** One ECS service for API; one ECS service for worker; optional **SQS** instead of DB‑backed jobs.  
- **Pros:** Mature, flexible networking/IAM; easy path to queues, batched workers, and private subnets.  
- **Cons:** More infra to set up (task defs, ALB, IAM, logs).  
- **Fit:** Great when you want **SQS** right away and stricter VPC/IAM controls.

### Option D — **AWS Lambda + API Gateway + (SQS + Lambda worker) + RDS**
- **What:** API in Lambda; long tasks enqueued to SQS; Lambda workers process and write to RDS/S3.  
- **Pros:** Serverless scale‑to‑zero; no container mgmt.  
- **Cons:** Concurrency/timeout limits; cold starts; coordination complexity for multi‑step jobs.  
- **Fit:** Works if tasks can be chunked <15min and you want pure serverless.

### Option E — **Elastic Beanstalk (web + worker tiers) + RDS + S3**
- **What:** Classic PaaS; separate worker environment consumes SQS.  
- **Pros:** Simple setup; good for teams familiar with Beanstalk.  
- **Cons:** Older stack; less momentum vs App Runner/ECS.  
- **Fit:** Acceptable if team has Beanstalk experience; otherwise prefer B or C.

**Recommendation for MVP:** **Option B (App Runner + RDS + S3)**. It’s one cloud, low‑ops, supports the **single worker** pattern today, and upgrades cleanly:
- Add **SQS** later without changing the API/worker services.  
- Migrate worker to **ECS/Fargate** if you need CPU‑heavy workloads.

---

## 9) Tech Stack (MVP)
**Backend & Orchestration**  
- FastAPI, Pydantic, SQLAlchemy.  
- Orchestration: OpenAI Agents SDK **or** LangGraph.  
- Code‑gen provider: Anthropic Claude Code (plus optional OpenAI Code model) behind a `CodeGenProvider` interface.

**Data & Storage**  
- Postgres (AWS RDS), S3 for artifacts/zips, optional Redis (ElastiCache) later for caching.

**Build & CI for Generated Repos**  
- GitHub Actions, `ruff`, `mypy`, `pytest`, `pip‑audit`, `cyclonedx`, `terraform validate`, `tflint`, `hadolint`, `actionlint`.

**Observability & Telemetry**  
- Structured JSON logs; request IDs; per‑LLM call metrics (tokens, latency, model).  
- OpenTelemetry exporters later; minimal dashboards first (CloudWatch Logs Insights).

**Security (MVP)**  
- Server‑side key management; no secrets in generated repos.  
- Redaction in logs; project‑scoped data isolation.

---

## 10) Implementation Strategy

### Step 1 — Foundations (Week 1–2)
- Project scaffolding: API, DB migrations, S3 client.  
- Data model tables and **event log**.  
- `jobs` table and **single worker** service with retry/backoff.

### Step 2 — Provider Abstraction & Schemas (Week 2–3)
- `CodeGenProvider` + `OrchestrationProvider` interfaces.  
- Pydantic schemas for **all agent I/O**; fail closed with validation.

### Step 3 — Capability Patterns & Planner (Week 3–4)
- Define capability taxonomy; implement 2–3 patterns per capability per cloud (AWS first).  
- Planner composes patterns under constraints.

### Step 4 — Critics & Policies (Week 4–5)
- Implement **technical critic** and **cost critic**.  
- Policy engine with pass/fail report; persist in `/reports`.

### Step 5 — Repo Generation & Static Validation (Week 5–6)
- Codegen for services + IaC + CI.  
- Run validators; create zip with `/reports` + diffs; store in S3.

### Step 6 — Diff‑First UX & Review Flow (Week 6–7)
- Server‑side git for artifacts; show unified diffs (docs + repo tree + cost).  
- HITL approvals recorded in DB.

### Step 7 — Pilot & Hardening (Week 7–8)
- Golden scenarios; prompt library; regression harness.  
- Observability, basic rate limiting, and backpressure controls.

---

## 11) APIs (Illustrative)
- `POST /projects` – create project.  
- `POST /projects/{id}/constraints` – add/modify constraints → enqueues job.  
- `GET /projects/{id}/decision-sets` – list with versions/diffs.  
- `GET /decision-sets/{id}` – plan, critics, policy, artifacts.  
- `POST /decision-sets/{id}/approve` – record HITL approval.  
- `POST /decision-sets/{id}/generate` – force regeneration (admin).

---

## 12) Testing & Evaluation
- **Golden prompts**: canonical inputs with expected plan structure.  
- **Determinism**: temperature controls, seed, tool‑call contracts.  
- **Static checks**: IaC validate, linters, type checks, SBOM, SCA; all in `/reports`.  
- **Acceptance metrics**: proposal acceptance rate, diff size, time‑to‑artifact, LLM error rates.

---

## 13) Security & Privacy (MVP Baseline)
- Keys stored server‑side; scoped per project.  
- PII redaction in logs; configurable data retention.  
- No outbound credentials in artifacts.

**Future:** per‑tenant KMS keys, Vault integration, workload identity, data‑class tagging and policy enforcement.

---

## 14) Roadmap – Planned for Future
- **Apply Mode:** dry‑run, cost/permission checks, staged apply to sandbox, smoke tests, rollback.  
- **RBAC & Approvals:** roles (Owner, Architect, Reviewer, FinOps) with e‑sign audit.  
- **Agent Telemetry & Replay:** per‑agent trace store, replay/fork, blacklist suggestions.  
- **Durable Orchestration:** move to SQS → ECS workers; optional Temporal/Step Functions.  
- **Evented Lineage:** link data/model/prompt/infra versions to decisions.  
- **Adapters:** multi‑cloud capability layer; provider feature flags.  
- **Compliance Copilot & FinOps Copilot.**  
- **Repo‑ingest “Fix‑my‑MLOps.”**  
- **Challenge Packs & Adversarial Critics.**

---

## 15) Non‑Functional Requirements
- **SLOs (MVP):** p95 plan roundtrip ≤ 2 min; artifact generation ≤ 5 min; availability 99.5%.  
- **Scalability:** horizontal App Runner/ECS scale; DB connection pooling; backpressure via job polling.  
- **Reliability:** idempotent job execution keyed by decision set; exponential backoff.

---

## 16) Risks & Mitigations
- **Provider instability** → dual‑provider interface, circuit breakers, cached few‑shots.  
- **Non‑deterministic outputs** → strict JSON schemas, validators, regression harness.  
- **User trust** → diffs, policy reports, static validation, design rationale in docs.  
- **Scope creep** → capability patterns constrain search; roadmap gates.

---

## 17) Decision: Deployment Choice (for this MVP)
**Adopt Option B (AWS App Runner + RDS + S3)**. Rationale: single‑cloud buyer appeal, minimal ops, clean path to SQS/ECS later without redesign. If the team prefers deeper VPC/IAM control from day one, choose Option C (ECS Fargate) with SQS.

---

## 18) Appendices
- **A. Example Policy Rules** (latency, regions, budget, data‑class).  
- **B. Example Capability Patterns** per cloud.  
- **C. Example Diff Report Format** (doc diff, repo manifest diff, cost delta).  
- **D. Example `/reports` bundle layout.**



---

## 19) Transparent Reasoning & Agent Rationale (User‑Facing)
**Goal:** Build trust by exposing *what ran*, *why a choice was made*, and *what alternatives were rejected*—without leaking raw model chain‑of‑thought or secrets.

**What we show (summarized as “Reason Cards” per decision):**
- **Agent & Step:** name, version, run ID, timestamps.
- **Trigger & Inputs:** constraints referenced, artifacts consulted, prior decisions.
- **Options Considered:** short list of candidates with pros/cons.
- **Decision & Rationale:** concise justification mapped to explicit constraints/policies.
- **Policy & Cost Impact:** pass/fail checks, estimated monthly delta, latency/availability implications.
- **Confidence & Risks:** score with top uncertainties and suggested probes.
- **Links:** diff to previous version, cost report, related events.

**How it’s produced:**
- Each agent returns a **structured rationale** object (pydantic) – *not* free‑form hidden CoT.
- The worker converts it into a **Decision Ledger** entry and emits an `event` (e.g., `plan_proposed`, `critic_passed`).
- Rationale is embedded in the generated **Design Rationale** section and exported into `/reports/rationale.json` in the repo zip.

**Spec (illustrative):**
```json
{
  "decision_id": "uuid",
  "agent": "planner|critic.tech|critic.cost|codegen",
  "trigger": "constraints_updated|user_approve|regen",
  "inputs": {"constraints_keys": ["budget","regions","sla"], "artifacts": ["capability:ingest:s3-batch"]},
  "candidates": [{"id":"optA","summary":"…","tradeoffs":["…"]}],
  "choice": {"id":"optA","justification":"…"},
  "policy_results": {"budget":"pass","region":"pass","pii":"warn"},
  "impacts": {"monthly_usd": 420, "p95_latency_ms": 180},
  "confidence": 0.74,
  "risks": ["quota risk on bedrock:us-east-1"],
  "links": {"diff":"/diffs/ds_12_vs_13.md","cost":"/reports/cost.json"}
}
```

**UI patterns:**
- **Timeline** of agent runs with expandable Reason Cards (lazy‑loaded to keep the UI responsive). 
- **“What just happened?”** side panel after each recompute.
- **Export**: rationale bundle inside the repo’s `/reports` and embedded in docs.

**Privacy & Safety:** redact secrets/PII; never expose raw prompts or provider transcripts; internal “debug mode” gated behind admin.

---

## 20) Input Strategy – Guided vs. Freeform (Adaptive Intake)
**Recommendation:** Hybrid, **adaptive** approach that starts freeform and escalates to targeted questions only when coverage is insufficient or conflicts are detected.

**Flow:**
1. **Freeform First:** user writes requirements → extractor maps to a typed **Constraint Schema**.
2. **Coverage Check:** compute a **Constraint Coverage Score** (e.g., required fields: cloud/region, budget band, workload types, SLOs, data‑class).
3. **Adaptive Questioner:** if coverage < threshold or constraints conflict, ask the **minimum** set of high‑value questions (batch vs streaming, serverless vs containers, budget band, compliance flags, preferred stack, existing assets).
4. **Guided Mode (optional):** offer a 2–5 minute wizard up front for users who prefer structure; responses persist as the **Intake Snapshot**.
5. **Proceed to Planning:** planner composes capability patterns; any remaining gaps are tracked as open questions and surfaced in Reason Cards.

**Constraint Schema (starter fields):** `cloud`, `regions`, `budget_band`, `data_classification`, `sla_latency_ms`, `availability_target`, `throughput`, `workload_types[batch,streaming,online]`, `deployment_pref[serverless,containers]`, `storage_prefs`, `observability_prefs`, `team_constraints (languages, skills)`, `existing_stack`, `compliance (GDPR/HIPAA etc.)`.

**UX:** two entry points — **Quick Start (freeform)** and **Guided Setup**. Show live **coverage meter** and highlight missing/ambiguous items; never block progress unless a policy requires it (e.g., region or data‑class).

**Metrics:** question count per session, acceptance rate of first plan, rework rate, time‑to‑artifact, unresolved‑constraints after planning.

---



---

## 21) Implementation Details (LangGraph)
**Goal:** Make the MVP’s multi‑agent flow deterministic, observable, and resumable on AWS App Runner while using LangGraph’s primitives.

### 21.1 Graph Topology (fixed, deterministic)
Nodes (in order):
1. **intake_extract** → parse freeform input into **Constraint Schema**.
2. **coverage_check** → compute coverage score; emit missing/ambiguous fields.
3. **adaptive_questions** → (optional) minimal follow‑ups; loop until threshold.
4. **planner** → compose capability patterns into a candidate plan.
5. **critic_tech** → feasibility, coupling, bottlenecks; emit risks.
6. **critic_cost** → coarse BOM + monthly estimate; compute deltas vs previous.
7. **policy_eval** → apply rules; pass/warn/fail with explanations.
8. **gate_hitl** *(interrupt)* → require user approval; capture inline comments.
9. **codegen** → generate repo skeletons (services, IaC, CI, docs).
10. **validators** → run static checks; compile `/reports`.
11. **rationale_compile** → transform per‑node rationale → **Reason Cards** + **Design Rationale** doc section.
12. **diff_and_persist** → commit artifacts to git/S3; write `decision_set` + `events`; output composite Change Summary.

> Each node yields structured **stream events** for the UI (see §22.3).

### 21.2 Shared State & Checkpointing
- **State keys:** `constraints`, `coverage`, `plan`, `candidates`, `policy`, `cost`, `hitl`, `artifacts`, `reports`, `diff_summary`, `run_meta`.
- **Checkpointer:** LangGraph PostgresSaver. `thread_id` = `decision_set_id` (UUID). Each node **merges** into state; we store a pointer to the latest checkpoint in `decision_sets` for time‑travel.

### 21.3 Idempotency & Side‑effects
- **Idempotency key:** `sha256(thread_id | node_name | canonical_json(input))`.
- Before executing a node, look up `agent_runs(idem_key)`; if `ok=true`, **reuse** output.
- **Artifacts:** write to S3 under `projects/{pid}/ds_{ver}/{sha256}-{filename}`; duplicates are harmless; DB stores hashes.
- **Optimistic locking:** update `decision_sets` with `version` and `updated_at`; on conflict, reload and retry with backoff.

### 21.4 Provider Abstractions & Resilience
- Interfaces: `OrchestrationProvider` (OpenAI Agents SDK or LangGraph-native tools) and `CodeGenProvider` (Anthropic Claude Code, optional OpenAI). 
- **Schema‑first:** every tool/LLM output validated via Pydantic; failures produce a user‑friendly Reason Card.
- **Circuit breakers:** cooldown per provider/model on 429/5xx; fall back for *non‑codegen* nodes.
- **Determinism:** fixed temperature/top‑p; **few‑shot pack registry** loaded by content hash ID.

### 21.5 Policy Engine & Cost Critic (MVP)
- **Rules:** JSONLogic/Python rules over `constraints` + `plan` (e.g., `budget_band`, `regions`, `data_classification`, `sla_latency_ms`).
- **Cost:** extract BOM from patterns/IaC (instances, storage GB, requests/s); estimate monthly USD → `cost_estimates`.
- **Surfacing:** policy + cost deltas streamed before HITL; stored in `/reports/policy.json` and `/reports/cost.json`.

### 21.6 Streaming & UX on App Runner
- SSE endpoint streams `reason-card`, `policy-update`, `cost-update`, `diff-update`, `gate-waiting`, `run-error`, `run-complete`.
- Heartbeats every 10s; disconnect handling marks `stream_abandoned=true/false`.
- Events include `project_id`, `decision_set_id`, `run_id`, `node_name`, `ts` for multi‑tenant correlation.

### 21.7 Diff‑First Persistence
- **Server‑side git repo per project**; commit plan/docs/repo manifests each version.
- **DeepDiff** on state objects + **unified text diffs** on markdown/code; compose into a single Change Summary.

### 21.8 HITL Ergonomics
- Inline comments on plan; persisted to `approvals` and fed back into `planner` on resume.
- Approvals can **expire**; reminders via email/webhook; stale runs marked accordingly.

### 21.9 Testing & Eval
- **Golden runs** with frozen inputs; assert on schemas, policy pass, presence of mandatory capabilities.
- **Determinism budget:** on N consecutive schema failures, capture payloads to a quarantine bucket.

### 21.10 Security & Hygiene (MVP)
- Redact secrets/PII in logs and Reason Cards; no secrets in generated repos.
- Per‑environment LangSmith projects with retention; request/trace IDs carried end‑to‑end.

### 21.11 AWS App Runner Notes
- Two services: **api** (FastAPI) and **worker**; worker has higher CPU/mem. 
- **RDS Proxy** for Postgres pooling; S3 same region; SSE‑S3 enabled. 
- Structured logs to CloudWatch: `{request_id, run_id, thread_id, node_name, model, tokens, latency_ms}`.

---

## 22) API & Contracts Appendix

### 22.1 REST Endpoints (MVP)
- `POST /projects` → create project.
- `POST /projects/{id}/constraints` → add/modify constraints; returns `{decision_set_id, stream_url}`.
- `GET /streams/{decision_set_id}` → SSE stream (see §22.3).
- `GET /decision-sets/{id}` → details (plan, critics, policy, artifacts, diffs).
- `GET /decision-sets/{id}/events` → event log timeline.
- `POST /decision-sets/{id}/approve` → HITL approval `{status, comment}`.

**Idempotency:** Clients may send `Idempotency-Key` header on mutating routes; server dedupes on this key.

### 22.2 Core Schemas (abridged)
**Reason Card**
```json
{
  "decision_id": "uuid",
  "agent": "planner|critic.tech|critic.cost|codegen",
  "node_name": "critic_cost",
  "trigger": "constraints_updated|user_approve|regen",
  "inputs": {"constraints_keys": ["budget_band","regions"], "artifacts": ["capability:ingest:s3-batch"]},
  "candidates": [{"id":"optA","summary":"…","tradeoffs":["…"]}],
  "choice": {"id":"optA","justification":"…"},
  "policy_results": {"budget":"pass","region":"pass","pii":"warn"},
  "impacts": {"monthly_usd": 420, "p95_latency_ms": 180},
  "confidence": 0.74,
  "risks": ["quota risk in us-east-1"],
  "links": {"diff":"/diffs/ds_12_vs_13.md","cost":"/reports/cost.json"},
  "ts": "2025-08-17T10:15:22Z"
}
```

**Policy Results**
```json
{
  "rules": [
    {"id":"latency_slo","status":"pass","detail":"p95<=200ms"},
    {"id":"budget_band","status":"warn","detail":"est $420 > target $400"},
    {"id":"region_policy","status":"pass","detail":"all resources in eu-west-1"}
  ],
  "overall": "warn"
}
```

**Cost Estimate**
```json
{
  "monthly_usd": 420.0,
  "breakdown": [
    {"service":"s3","qty":"500GB","usd": 12.5},
    {"service":"ec2-fargate","qty":"vCPU-hrs","usd": 350.0}
  ],
  "method": "bom_v1",
  "delta_vs_prev_usd": 55.0,
  "delta_vs_prev_pct": 15.1
}
```

**Diff Summary**
```json
{
  "docs_changed": ["plan.md"],
  "files_added": 7,
  "files_removed": 1,
  "files_modified": 12,
  "cost_delta_usd": 55.0,
  "state_keys_changed": ["plan","policy","cost"],
  "git_commit": "a1b2c3d"
}
```

### 22.3 SSE Event Types
Events are `event:` lines with JSON payloads on `data:` lines.
- `reason-card` → Reason Card payload
- `policy-update` → Policy Results
- `cost-update` → Cost Estimate
- `diff-update` → Diff Summary
- `gate-waiting` → `{decision_set_id, gate:"pre-codegen", ts}`
- `run-error` → `{decision_set_id, node_name, message, ts}`
- `run-complete` → `{decision_set_id, version, ts}` (always emitted last)
- Heartbeats → `event: ping` with empty `{}` every 10s

### 22.4 Error Model
```json
{
  "error": {
    "code": "validation_failed|rate_limited|provider_down|conflict|not_found",
    "message": "human readable",
    "retry_after_s": 30,
    "run_id": "uuid",
    "node_name": "critic_cost"
  }
}
```

### 22.5 Webhooks (optional)
- `plan.ready`, `gate.waiting`, `run.complete`, `run.error` – signed with HMAC; retry with backoff.

---



---

## 23) Operational Hardening (MVP+)
This section folds in final guardrails so the MVP feels production‑minded without increasing scope.

### 23.1 AuthN/AuthZ & Multi‑Tenancy
- **Identity:** OIDC (Amazon Cognito or Auth0). API validates JWT on every request & SSE connection.
- **Authorization:** Project‑scoped access checks on all routes; include `project_id` in every DB query and SSE payload.
- **Data partitioning:** S3 prefixes `projects/{project_id}/…`; DB tables carry `project_id` (indexed). Optional RLS later.
- **Webhooks:** Signed with HMAC; replay protection via `idempotency_key` + expiry.
- **Audit:** Correlate `request_id`, `run_id`, `thread_id`, and `user_id` in logs & events.

### 23.2 Job Claiming & Exactly‑Once Semantics
- **Claim pattern:** Single SQL round‑trip with `FOR UPDATE SKIP LOCKED` + lease.
- **Lease fields:** `lease_expires_at`, `worker_id`, `retries`.
- **Renewal:** Workers renew lease periodically; on crash, expired jobs are re‑claimable.
- **Idempotency:** Per‑node `idem_key = sha256(thread_id|node|canonical_json(input))` gates side effects; artifacts written with content‑hash keys.

**Example (illustrative SQL):**
```sql
UPDATE jobs SET status='running', worker_id=:wid,
  lease_expires_at=NOW() + INTERVAL '5 minutes'
WHERE id = (
  SELECT id FROM jobs
  WHERE status='queued' AND next_run_at <= NOW()
  ORDER BY priority DESC, created_at ASC
  FOR UPDATE SKIP LOCKED
  LIMIT 1
)
RETURNING *;
```

### 23.3 Schema Evolution & Migrations
- **Migrations:** Alembic from day one; version stamps on `events` and `decision_sets`.
- **State upgrades:** On‑read transform hook when Pydantic models change.
- **Backfills:** Lightweight scripts to re‑compute derived fields (e.g., cost deltas) for old rows.

### 23.4 Prompt & Few‑Shot Governance
- **Pack registry:** Few‑shot packs checked into a server‑side git repo; each referenced by **content hash**.
- **Traceability:** Every Reason Card/event includes `prompt_pack_hash`; diffs show "Prompt pack vX→vY" when it changes.
- **Controls:** Fixed temperature/top‑p; provider circuit breakers/cooldowns per model.

### 23.5 Budgets, Rate Limits & Cost Gating
- **Per‑project budgets:** token & concurrency quotas; soft warn at 80%, hard stop at 100%.
- **Cost critic thresholds:** Require HITL if `Δcost_usd > Y` or `Δcost_pct > X%` vs previous decision set.
- **Pre‑run estimator:** Planner predicts token usage; pause if projected spend exceeds remaining budget.

### 23.6 Streaming Resilience & Artifact Hygiene
- **SSE:** Heartbeats every 10s; max stream duration; `run-complete` (terminal) + `decision_set_summary` events.
- **Resume path:** UI can reconstruct via `GET /decision-sets/{id}/events` + latest checkpoint.
- **Artifacts:** Time‑boxed **signed S3 URLs**; lifecycle rules (e.g., expire zips after 14 days).
- **Secret scans:** Validators fail build if secrets/personal tokens detected in artifacts.

### 23.7 Testing & Release Gates
- **Golden runs:** Deterministic inputs with assertions on schemas, policy overall != `fail`, and presence of mandatory capabilities.
- **Property‑based tests:** Fuzz constraint inputs to test extractor/coverage and planner robustness.
- **Quarantine bucket:** Persist failing LLM payloads under safeguards for triage.
- **Release gate:** Ship only if golden & property tests pass and validation reports are green.

### 23.8 Observability & SLOs
- **Dashboards:** time‑to‑artifact, SSE disconnect rate, job retries, LLM error codes, cost deltas.
- **Alerts:** sustained 5xx on API, job retry storms, policy `fail` spikes, budget threshold crossings.

### 23.9 Updated Architecture Diagram (App Runner)
```mermaid
flowchart TD
  U[User] -->|OIDC Login| IDP[(Cognito/Auth0)]
  IDP --> API[App Runner: FastAPI]
  U <-->|SSE (Reason Cards)| API
  API -->|enqueue/queries| RDS[(RDS Postgres via RDS Proxy)]
  W[App Runner: Worker] -->|claim jobs| RDS
  W -->|LLM orchestration| Orchestrator[(OpenAI Agents SDK / LangGraph)]
  W -->|code generation| CodeGen[(Claude Code)]
  W -->|zip & reports| S3[(S3 Artifacts)]
  API -->|serve signed URLs| U
  API --> CW[(CloudWatch Logs)]
  W --> CW
  API -->|webhooks (HMAC)| EXT[(User Systems)]
```

**Notes:** SSE heartbeats enabled; signed URLs time‑boxed; all DB/S3 access scoped by `project_id`; jobs use SKIP LOCKED + leases.

