# **Comprehensive Implementation Plan: The Resilient Agentic MLOps Platform (v2)**

This plan details how to build your platform's features using LangGraph, incorporating the advanced resilience, security, and ergonomic patterns outlined in your updated roadmap.

#### **1. System Architecture & Operational Foundation (per Roadmap §8, §23.11)**

We will adopt the recommended **Option B: AWS App Runner** for its balance of managed simplicity and a clear path to scalability.

*   **Core Components:**
    *   **API Service (App Runner):** FastAPI service for all synchronous user interactions (intake, approvals, fetching diffs/events).
    *   **Worker Service (App Runner):** A separate, more resource-intensive service for running the LangGraph workflows.
    *   **Database (AWS RDS Postgres with RDS Proxy):** The source of truth for projects, decision sets, events, jobs, and checkpoints. The proxy handles efficient connection pooling.
    *   **Artifact Store (AWS S3):** For storing zipped code bundles, reports, and committed plan documents. It will be in the same AWS region as the services, with SSE-S3 encryption enabled by default.

*   **Observability:**
    *   **Tracing:** LangSmith will be enabled via environment variables (`LANGCHAIN_TRACING_V2`, `LANGCHAIN_API_KEY`).
    *   **Logging:** All services will emit structured JSON logs to Amazon CloudWatch. Crucially, every log entry will include `request_id`, `run_id`, `thread_id`, and `node_name` to allow direct correlation between application logs and LangSmith traces.

#### **2. State, Persistence, and Idempotency (per Roadmap §7, §21.2, §21.3, §23.2)**

This is the bedrock of the system's resilience and auditability. We will implement a multi-layered persistence strategy.

1.  **LangGraph State & Checkpointing:**
    *   **State Schema:** A central `MLOpsProjectState` TypedDict will define the shared memory for the main workflow, including `constraints`, `plan`, `policy_results`, `cost_estimate`, etc.
    *   **Checkpointer:** We will use `langgraph.checkpoint.postgres.PostgresSaver`, configured to connect to our RDS instance. The `thread_id` for a given workflow run will correspond to its `decision_set_id`.

2.  **Explicit Audit Event Log:**
    *   **Rationale:** While checkpoints store the *state*, the `events` table provides a lightweight, human-readable log of *what happened*. It's optimized for UI timelines and auditing.
    *   **Implementation:** A utility function, `log_event(state, event_type, payload)`, will be called at the end of each significant node. It will write a new row to the `events` table, including the `decision_set_id` and the `checkpoint_id` of the state *after* the event, creating a direct link for time-travel. The FastAPI backend will expose a `/decision-sets/{id}/events` endpoint to serve this timeline.

3.  **Idempotency & Exactly-Once Semantics (Critical for Resilience):**
    *   **Node-Level Idempotency:** The worker will use the `agent_runs` table. Before executing a node, it will compute an idempotency key: `sha256(thread_id | node_name | canonical_json_hash(input_state))`. If a successful run with this key exists in `agent_runs`, the worker will skip execution and return the cached output.
    *   **Side-Effect Guards:** All writes to S3 will use a content-based hash as the object key (e.g., `s3://.../artifacts/{sha256-of-content}.zip`). This makes uploads naturally idempotent.
    *   **Optimistic Locking:** The `decision_sets` table will have a `version` integer column. All `UPDATE` statements will include `WHERE id = ? AND version = ?`. If the update affects 0 rows, it signifies a race condition. The worker will catch this, reload the latest state, and retry the operation with exponential backoff.

#### **3. The Adaptive Intake Workflow (per Roadmap §20, §21.1)**

This initial phase is a self-contained graph that ensures all prerequisites are met before the main planning starts.

*   **State Schema:** A dedicated `IntakeState` will manage the process, holding the `raw_query`, the Pydantic `ConstraintSchema` object, `missing_fields`, and `intake_messages`.
*   **Graph Nodes & Flow:**
    1.  **`extract_constraints`:** An LLM-powered node that uses tool-calling to populate the `ConstraintSchema` Pydantic model from the user's text.
    2.  **`coverage_check`:** A deterministic Python node that calculates a "Constraint Coverage Score" and identifies mandatory missing fields.
    3.  **`adaptive_questioner`:** An LLM-powered node that generates a question for the user *only if* the coverage check fails.
    4.  **`gate_user_input` (Interrupt):** The graph pauses using `interrupt_after` to wait for the user's response.
*   **Control Flow:** A conditional edge after `coverage_check` either proceeds to the main planning workflow or loops back through the `adaptive_questioner` and `gate_user_input`.

#### **4. Deterministic Agent Orchestration (per Roadmap §21.1)**

As specified, the core workflow is a fixed, sequential graph, providing predictability and simplifying debugging.

*   **LangGraph Implementation:** We will use **normal edges** (`builder.add_edge(...)`) to define the precise order of execution for the planning and generation agents. The graph topology will follow the sequence defined in section `21.1` of your roadmap, from `planner` to `critic_tech`, `critic_cost`, `policy_eval`, the `gate_hitl` interrupt, and finally to `codegen` and `validators`.

#### **5. Provider Resilience & Determinism (per Roadmap §16, §21.4)**

*   **Provider Abstraction:** All LLM calls will be routed through `OrchestrationProvider` and `CodeGenProvider` interfaces.
*   **Resilience:** We will implement circuit breakers (using a library like `pybreaker`) within these providers to handle transient 429/5xx errors. For non-codegen steps, we will configure `.with_fallbacks()` to a secondary model/provider.
*   **Determinism:** All LLM calls will use a fixed `temperature=0`. Few-shot examples will be managed in a "pack registry" (a version-controlled file or simple DB table) and referenced by a content hash ID in the `ReasonCard` to ensure reproducibility.
*   **Schema-First Validation:** Every LLM output that expects a structure (e.g., a plan, a tool call) will be immediately validated against its Pydantic model. A validation failure will trigger an internal retry loop where the error is fed back to the LLM, asking it to correct its output.

#### **6. Streaming, "Reason Cards", and SSE Resilience (per Roadmap §19, §21.6, §22.3)**

This is the core of the user-facing transparency.

*   **LangGraph Implementation:**
    *   Each node in the graph will be a function that accepts the `StreamWriter` from the runtime config.
    *   After performing its logic, the node will construct a `ReasonCard` Pydantic object and immediately stream it using `writer.write([("reason-card", card.model_dump())])`. Other event types (`policy-update`, `cost-update`) will be streamed similarly from their respective nodes.
*   **SSE Resilience on App Runner:**
    *   The FastAPI SSE endpoint will send a `event: ping` heartbeat every 10 seconds to prevent idle connection timeouts.
    *   The worker's `writer.write()` calls will be wrapped in a `try...except` block. A disconnection will be caught, and a `stream_abandoned=True` flag will be set in the database for the corresponding run.
    *   A final `event: run-complete` message will always be sent, allowing the UI to reliably terminate the stream.

#### **7. Human-in-the-Loop (HITL) Ergonomics (per Roadmap §21.8)**

*   **LangGraph Implementation:**
    *   We will use `langgraph.interrupt.interrupt_after` to create the `gate_hitl` node.
    *   When the user approves via the API, they can include an optional `comment` field.
    *   When resuming the graph, this comment is passed in the input. A dedicated node immediately after the interrupt (`process_approval_feedback`) will parse this comment and update the `constraints` in the state before the `codegen` agent runs.

#### **8. Diff-First UX (Git + State) (per Roadmap §5, §21.7)**

*   **LangGraph Implementation:**
    *   The `diff_and_persist` node at the end of the workflow will be responsible for this.
    *   It will use a library like `pygit2` to programmatically manage a server-side Git repository for each project. It will commit the human-readable plan documents and repo manifest.
    *   The FastAPI `/decision-sets/{id}` endpoint will fetch the current and parent `decision_set` checkpoints from Postgres to compute a state diff using `deepdiff`. It will also use `pygit2` to compute a `git diff` between the two associated commits, returning a single, composite "Change Summary" JSON object to the UI.

#### **9. Code Generation and Validation (per Roadmap §5, §21.1)**

*   **LangGraph Implementation:** The `codegen` node will orchestrate the Anthropic Code SDK as a tool. The `validators` node will then execute a series of checks on the generated code *in a sandboxed environment* before zipping. This includes running `ruff`, `terraform validate`, and a secret scanner. The results will be compiled into the `/reports` directory.

#### **10. Testing & Evaluation Harness (per Roadmap §12, §21.9)**

*   **Implementation:** We will create a `pytest` suite for "golden runs." These tests will invoke the full graph with deterministic inputs and assert on the final state and generated reports. Key assertions will include:
    *   The final Pydantic `plan` object is valid.
    *   The `policy_eval` result is `pass`.
    *   Specific, mandatory "capability patterns" are present in the plan.
*   The "determinism budget" will be implemented: if a node's schema validation retry loop fails 3 times, it will raise a special exception, and a global error handler in the worker will save the invalid payload to a designated S3 quarantine bucket for triage.