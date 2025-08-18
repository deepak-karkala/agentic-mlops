# Agentic MLOps Platform — Step‑by‑Step Implementation Plan

**Version:** 1.0
**Date**: 2025-08-18
**Purpose**: A detailed, incremental implementation plan focused on early prototyping and progressive feature enhancement, using AWS App Runner, LangGraph, and a dual-provider LLM design.
**GitHub Management**: All issues will be tracked on a single **Projects v2 board**: *Agentic MLOps - MVP Delivery*.

---

## 1. Phase 1: Foundation & "Hello, Agent!" (Weeks 1-2)

**Goal**: Establish the core infrastructure, a basic frontend/backend, and a simple, demonstrable end-to-end "thin slice" of functionality. This phase proves the core deployment and communication loop.

### **Issue #1: Repository & CI/CD Scaffolding**
- **Epic**: Foundation
- **Labels**: `setup`, `ci-cd`, `p0-critical`
- **Milestone**: Phase 1 - Foundation

- **Description**: Set up the monorepo structure, Python/Next.js toolchains, and a basic CI pipeline to ensure code quality and automated checks from day one.
- **Acceptance Criteria**:
    - [ ] Monorepo with `api/`, `worker/`, `frontend/`, and `libs/` directories is created.
    - [ ] Python environment is managed with `uv` and a `pyproject.toml`.
    - [ ] Next.js frontend is initialized with TypeScript and Tailwind CSS.
    - [ ] Pre-commit hooks with `ruff` and `prettier` are configured.
    - [ ] A basic GitHub Actions CI workflow runs `pytest` and `npm test` on every pull request.
- **Testing**:
    ```bash
    # Verify local dev environments
    (cd frontend && npm run dev)
    (cd api && uvicorn main:app --reload)
    
    # Verify CI checks
    pre-commit run --all-files
    pytest && npm test
    ```
- **Definition of Done**: A developer can clone the repo, install dependencies, and run all services locally. The CI pipeline is green on the `main` branch.

---

### **Issue #2: AWS Infrastructure Bootstrap**
- **Epic**: Foundation
- **Labels**: `infra`, `aws`, `p0-critical`
- **Milestone**: Phase 1 - Foundation

- **Description**: Provision the core AWS resources using Infrastructure as Code (Terraform) to support the MVP.
- **Acceptance Criteria**:
    - [ ] An AWS App Runner service for the **API** is defined and deployable.
    - [ ] A second App Runner service for the **Worker** is defined.
    - [ ] An RDS Postgres instance with an **RDS Proxy** is provisioned.
    - [ ] An S3 bucket for artifacts is created.
    - [ ] Basic IAM roles for services are defined.
- **Testing**:
    - Manually trigger a deployment of a simple "hello world" container to both App Runner services to verify connectivity.
    - Connect to the RDS instance from a local machine using credentials from AWS Secrets Manager.
- **Definition of Done**: All core AWS resources are provisioned and accessible. Terraform state is managed remotely (e.g., in an S3 backend).

---

### **Issue #3: Basic Frontend Chat UI**
- **Epic**: Frontend
- **Labels**: `frontend`, `ui`, `p1-high`
- **Milestone**: Phase 1 - Foundation

- **Description**: Build a minimal, functional chat interface in Next.js that can send a user's message and display a response. This is the user's first point of interaction.
- **Acceptance Criteria**:
    - [ ] A single-page chat view is created using Shadcn UI components.
    - [ ] The UI includes a message input box, a send button, and a message display area.
    - [ ] The component can manage a local list of messages (user prompts and AI responses).
    - [ ] A loading indicator is shown while waiting for a response.
    - [ ] Basic error messages are displayed on API failure.
- **Testing**:
    - Component tests using Jest/RTL to verify message submission and display.
    - Manually test the UI in a browser to ensure it is responsive and functional.
- **Definition of Done**: The chat interface is functional when pointed at a mock API, providing a clean user experience for a single-turn conversation.

---

### **Issue #4: "Thin Slice" LangGraph Workflow**
- **Epic**: Backend
- **Labels**: `backend`, `langgraph`, `p0-critical`
- **Milestone**: Phase 1 - Foundation

- **Description**: Create the simplest possible LangGraph graph: a single node that takes user input, calls an LLM, and returns the result. This validates the core orchestration logic.
- **Acceptance Criteria**:
    - [ ] A FastAPI backend with a `/chat` endpoint is created.
    - [ ] A simple `MessagesState` LangGraph graph is defined.
    - [ ] The graph has one node, `call_llm`, which invokes the orchestration LLM (e.g., GPT-4o) with the user's message.
    - [ ] The graph is compiled and can be invoked by the `/chat` endpoint.
- **Testing**:
    ```python
    # FastAPI TestClient
    def test_thin_slice_workflow():
        response = client.post("/api/chat", json={"messages": [{"role": "user", "content": "Hello"}]})
        assert response.status_code == 200
        assert "messages" in response.json()
        assert response.json()["messages"][-1]["role"] == "assistant"
    ```
- **Definition of Done**: The `/chat` endpoint successfully runs the simple LangGraph graph and returns a valid LLM response.

---

### **Issue #5: End-to-End Deployment & Test**
- **Epic**: Integration
- **Labels**: `deployment`, `e2e`, `p0-critical`
- **Milestone**: Phase 1 - Foundation

- **Description**: Deploy the frontend and backend services to App Runner and verify that they can communicate, completing the "walking skeleton."
- **Acceptance Criteria**:
    - [ ] The `frontend` is deployed to its App Runner service.
    - [ ] The `api` is deployed to its App Runner service with the simple LangGraph graph.
    - [ ] The frontend is configured to call the production API URL.
    - [ ] A user can type a message in the deployed UI, send it, and receive a response from the LLM via the backend.
- **Testing**:
    - E2E test using Playwright that opens the deployed URL, sends a message, and asserts that a response appears.
    - Manually verify the flow in a browser.
- **Definition of Done**: The team has a live, working, end-to-end prototype, however simple.

---

## 2. Phase 2: Durable State & The Job System (Weeks 3-4)

**Goal**: Implement the robust persistence and asynchronous job processing layers. This makes the system resilient and prepares it for long-running, multi-step agentic workflows.

### **Issue #6: Base Data Models & Migrations**
- **Epic**: Persistence
- **Labels**: `database`, `backend`, `p0-critical`
- **Milestone**: Phase 2 - Persistence

- **Description**: Define the core SQL schemas and set up Alembic for database migrations.
- **Acceptance Criteria**:
    - [ ] SQLAlchemy models are created for `projects`, `decision_sets`, `events`, `artifacts`, `agent_runs`, and `jobs`.
    - [ ] The `decision_sets` table includes a `version` column for optimistic locking.
    - [ ] Alembic is configured, and an initial migration is created and successfully applied to the RDS instance.
- **Testing**:
    - Run `alembic upgrade head` to apply migrations.
    - Unit tests to ensure SQLAlchemy models correctly map to the schema.
- **Definition of Done**: The database schema is stable and managed via code.

---

### **Issue #7: LangGraph Checkpointing & Durable State**
- **Epic**: Persistence
- **Labels**: `langgraph`, `backend`, `p1-high`
- **Milestone**: Phase 2 - Persistence

- **Description**: Integrate `PostgresSaver` to make the graph's state persistent, enabling memory, resume, and time-travel capabilities.
- **Acceptance Criteria**:
    - [ ] The LangGraph graph is compiled with a `PostgresSaver` checkpointer.
    - [ ] API calls to `/chat` now require and use a `thread_id` (which will map to `decision_set_id`).
    - [ ] The state of the graph after each step is visible in the Postgres `checkpoints` table.
    - [ ] The graph can be resumed from a previous state using the same `thread_id`.
- **Testing**:
    - Integration test: Invoke the graph, stop the service, resume the graph with the same `thread_id`, and verify it continues from the correct state.
- **Definition of Done**: Conversations are now stateful and durable.

---

### **Issue #8: Asynchronous Job Queue & Worker**
- **Epic**: Jobs
- **Labels**: `worker`, `database`, `p0-critical`
- **Milestone**: Phase 2 - Persistence

- **Description**: Decouple the API from the agent execution. The API will now enqueue a job, and the worker service will execute it.
- **Acceptance Criteria**:
    - [ ] The `/chat` endpoint now writes a job to the `jobs` table with a `queued` status and returns immediately with a `decision_set_id`.
    - [ ] The **Worker** service now runs a loop that polls the `jobs` table.
    - [ ] The worker claims jobs using the `FOR UPDATE SKIP LOCKED` pattern to ensure exactly-once processing.
    - [ ] The worker executes the LangGraph graph for the claimed job.
- **Testing**:
    - Concurrency test: Enqueue 10 jobs and run 2 worker instances. Verify each job is processed exactly once.
    - Fault-injection test: Kill a worker mid-run and verify the job is eventually picked up by another worker after its lease expires.
- **Definition of Done**: The system is now asynchronous, with the API remaining responsive while the worker handles heavy computation.

---

## 3. Phase 3: The Full MLOps Workflow & HITL (Weeks 5-6)

**Goal**: Expand the simple graph into the full, deterministic sequence of MLOps planning agents and introduce the critical human-in-the-loop approval gate.

### **Issue #9: Implement Full Graph Topology**
- **Epic**: Graph
- **Labels**: `langgraph`, `backend`, `p0-critical`
- **Milestone**: Phase 3 - MLOps Workflow

- **Description**: Wire up the full, deterministic graph with all agent nodes as defined in the roadmap. The nodes can initially be stubs that return mock data.
- **Acceptance Criteria**:
    - [ ] The `StateGraph` is defined with the full `MLOpsProjectState`.
    - [ ] All nodes (`planner`, `critic_tech`, `critic_cost`, `policy_eval`, `gate_hitl`, `codegen`, etc.) are added to the graph.
    - [ ] Normal edges connect the nodes in a fixed, sequential order.
- **Testing**:
    - Run the graph with mock implementations for each node. Verify that the execution flows through every node in the correct sequence.
- **Definition of Done**: The complete graph structure is in place and executable.

---

### **Issue #10: Implement Planner, Critic & Policy Agents**
- **Epic**: Graph
- **Labels**: `langgraph`, `ai`, `p1-high`
- **Milestone**: Phase 3 - MLOps Workflow

- **Description**: Flesh out the core planning agents. Each agent is a LangGraph node that reads from the shared state, performs its task, and writes its output back to the state.
- **Acceptance Criteria**:
    - [ ] **Planner**: Composes MLOps "capability patterns" based on user constraints.
    *   **Critics (Tech & Cost)**: Analyze the plan and produce structured feedback and cost estimates.
    *   **Policy Engine**: A deterministic node that evaluates the plan against Python-based rules.
- **Testing**:
    - "Golden run" tests: For a fixed input, assert that the planner produces a plan with expected components and that the policy engine returns a `pass` status.
- **Definition of Done**: The system can now autonomously generate and critique a full MLOps plan.

---

### **Issue #11: Human-in-the-Loop (HITL) Gate**
- **Epic**: Review
- **Labels**: `langgraph`, `hitl`, `p0-critical`
- **Milestone**: Phase 3 - MLOps Workflow

- **Description**: Implement the crucial user approval step before code generation.
- **Acceptance Criteria**:
    - [ ] A node in the graph uses `langgraph.interrupt.interrupt_after` to pause execution.
    - [ ] The API has a new endpoint: `POST /decision-sets/{id}/approve`.
    - [ ] The frontend UI displays the plan and an "Approve" button when the stream indicates it's `gate-waiting`.
    - [ ] Clicking "Approve" calls the API, which resumes the graph by invoking it with `None` and the correct `thread_id`.
    - [ ] Approval comments are captured and added to the state for the `codegen` agent to use.
- **Testing**:
    - E2E test: Start a run, wait for the interruption, call the `/approve` endpoint, and verify that the graph continues to the next step.
- **Definition of Done**: The user has full control to approve or reject a plan before any code is generated.

---

## 4. Phase 4: Artifacts, Transparency & UX (Weeks 7-8)

**Goal**: Implement the final output generation (code), the transparency features (streaming, diffs), and the corresponding UI enhancements.

### **Issue #12: Code Generation & Validation**
- **Epic**: Codegen
- **Labels**: `codegen`, `claude`, `p0-critical`
- **Milestone**: Phase 4 - Artifacts

- **Description**: Integrate the Anthropic Code SDK to generate the MLOps repository. Run static validation checks on the output.
- **Acceptance Criteria**:
    - [ ] The `codegen` node calls the Claude Code SDK to generate files based on the approved plan.
    - [ ] The `validators` node runs `terraform validate`, `ruff`, and a secret scanner on the generated code in a secure sandbox.
    - [ ] The results are compiled into a `/reports` directory.
    - [ ] The entire repository is zipped and uploaded to S3 with a content-hashed key.
- **Testing**:
    - For a golden plan, assert that the generated artifact zip is created and contains the expected file structure and reports.
- **Definition of Done**: The system produces a complete, validated, and downloadable code artifact.

---

### **Issue #13: Streaming "Reason Cards" & SSE Resilience**
- **Epic**: UX Transparency
- **Labels**: `streaming`, `api`, `p1-high`
- **Milestone**: Phase 4 - Artifacts

- **Description**: Implement the real-time streaming of agent rationale to the user.
- **Acceptance Criteria**:
    - [ ] Each agent node is updated to accept the `StreamWriter` and emits a structured `ReasonCard` event.
    - [ ] The FastAPI backend has a `GET /streams/{decision_set_id}` SSE endpoint.
    - [ ] The endpoint sends periodic heartbeats to prevent connection drops.
    - [ ] The frontend consumes the SSE stream and displays Reason Cards in a timeline.
- **Testing**:
    - E2E test subscribes to the SSE stream and asserts that the expected sequence of `reason-card` and `run-complete` events is received.
- **Definition of Done**: The user can see a detailed, real-time log of the system's thinking process.

---

### **Issue #14: Diff-First UX**
- **Epic**: Diffs
- **Labels**: `git`, `api`, `p1-high`
- **Milestone**: Phase 4 - Artifacts

- **Description**: Implement the diffing feature that compares versions of a plan.
- **Acceptance Criteria**:
    - [ ] The `diff_and_persist` node uses `pygit2` to commit generated plan documents to a server-side Git repository for the project.
    - [ ] The API exposes an endpoint that computes both a state diff (using `deepdiff`) and a Git diff between two `decision_set` versions.
    - [ ] The frontend displays this composite "Change Summary."
- **Testing**:
    - Create a plan (v1), modify a constraint, and regenerate (v2). Call the diff API and assert that the returned diff accurately reflects the changes to the plan and cost.
- **Definition of Done**: Users can clearly see how their changes impact the proposed MLOps architecture and cost.

---

## 5. Phase 5: Production Readiness (Weeks 9-10)

**Goal**: Add the final layers of security, observability, and governance required for a production launch.

### **Issue #15: Authentication & Authorization**
- **Epic**: Security
- **Labels**: `security`, `auth`, `p0-critical`
- **Milestone**: Phase 5 - Production

- **Description**: Integrate OIDC for user authentication and implement project-scoped authorization.
- **Acceptance Criteria**:
    - [ ] Integrate Amazon Cognito or Auth0 for user login.
    - [ ] The API validates JWTs on every request.
    - [ ] All database queries and S3 access are strictly filtered by `project_id` to enforce multi-tenancy.
- **Testing**:
    - Security tests to ensure unauthorized requests are rejected and users cannot access data from other projects.
- **Definition of Done**: The application is secure and multi-tenant ready.

---

### **Issue #16: Full Observability**
- **Epic**: Ops
- **Labels**: `monitoring`, `langsmith`, `p1-high`
- **Milestone**: Phase 5 - Production

- **Description**: Enable LangSmith tracing and configure structured logging.
- **Acceptance Criteria**:
    - [ ] LangSmith environment variables are configured in App Runner.
    - [ ] All LangGraph runs appear as traces in the LangSmith project.
    - [ ] CloudWatch logs are structured and include `run_id` and `thread_id` for easy correlation.
- **Testing**:
    - Manually trigger a run and verify that the full trace is visible in LangSmith and that the corresponding logs appear in CloudWatch with matching IDs.
- **Definition of Done**: The system is fully observable, allowing for rapid debugging and performance analysis.