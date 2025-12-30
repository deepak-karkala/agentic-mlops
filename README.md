# Agentic MLOps Platform

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Node.js 20+](https://img.shields.io/badge/node-20+-green.svg)](https://nodejs.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Build Production MLOps Systems in Minutes, Not Months**

A collaborative multi-agent AI platform that automates MLOps system design from natural language requirements to production-ready code—complete with infrastructure, CI/CD pipelines, and monitoring.

---

![System Architecture](docs/assets/portfolio_images/2.png)
*Complete system architecture: From natural language input to production-ready MLOps infrastructure*

**📍 Quick Links:** [Live Demo](#) • [Documentation](docs/) • [GitHub](https://github.com/deepak-karkala/agentic-mlops)

---

## 🎯 Key Features

- **🤖 Multi-Agent Orchestration**: Coordinated AI agents using LangGraph for deterministic, observable workflows with built-in checkpointing
- **⚡ Natural Language to Production Code**: Transform requirements into complete MLOps systems with infrastructure, application code, CI/CD, and monitoring
- **🎯 Real-Time Transparency**: Watch agents think and make decisions through streaming reason cards with confidence scores
- **🏗️ Production-Ready Output**: Enterprise-grade infrastructure (Terraform), application code, automated testing, and deployment pipelines
- **🔄 Human-in-the-Loop with Auto-Approval**: Optional approval gates for critical decisions with intelligent timeout mechanisms
- **💾 State Persistence & Crash Recovery**: LangGraph checkpointing with PostgreSQL for workflow resilience and replay capabilities

---

## 💡 The Problem & Solution

### Traditional MLOps Design: Weeks of Manual Work

Designing and deploying production MLOps systems traditionally requires **8-12 weeks** of manual effort across multiple disciplines:

| Traditional Approach | Time Required | Challenges |
|---------------------|---------------|------------|
| Manual requirements analysis | Days | Ambiguity, missed edge cases |
| Architect designs system | Weeks | Requires deep expertise across ML, DevOps, cloud |
| Manual code generation | Weeks | Tedious, error-prone, hard to standardize |
| Manual compliance checking | Days | Hard to verify against multiple policies |
| Iterative debugging and fixes | Weeks | Trial and error, difficult to trace issues |

**Result**: High costs, extended timelines, and significant risk of errors or non-compliance.

### Agentic Solution: Automated, Intelligent Workflow

| Agentic MLOps Platform | Time Required | Benefits |
|------------------------|---------------|----------|
| AI-powered constraint extraction | **Minutes** | Structured parsing eliminates ambiguity |
| Multi-agent collaborative design | **Minutes** | Planner + 3 critics validate feasibility, policy, optimization |
| Automated code generation with AI | **Minutes** | Claude Code SDK generates complete repositories |
| Automated policy validation | **Seconds** | Built-in compliance checks with feedback loops |
| Built-in critics and validators | **Automatic** | Confidence scoring triggers human review when needed |

**Result**: Complete, production-ready MLOps systems generated in **3-5 minutes** instead of 8-12 weeks.

---

## 🚀 Product Demo: Real-Time Fraud Detection System

### Act 1: Natural Language Input

**You provide requirements in plain English:**

```
"Design an MLOps system for real-time fraud detection with sub-100ms latency,
PCI DSS compliance, and auto-scaling for 10,000 requests/second."
```

**Platform Response:**
- ✅ Constraint extraction initiated
- 🎯 Identified: Performance (latency, throughput), Security (PCI DSS), Scalability requirements

---

### Act 2: Real-Time Agent Collaboration

Watch agents think and collaborate in real-time through streaming reason cards:

**1. Planner Agent** (GPT-4):
```
🧠 Reasoning: "For sub-100ms latency, recommend Lambda@Edge with DynamoDB
Global Tables. PCI DSS requires encryption at rest/transit, audit logging."

✅ Confidence: 0.89
```

**2. Feasibility Critic**:
```
⚠️ Challenge: "Lambda@Edge has cold start issues for real-time fraud
detection. Recommend ECS Fargate with Aurora Serverless v2 instead."

📊 Confidence: 0.92
```

**3. Policy Agent**:
```
✅ PCI DSS Validation: Passed
✅ Cost Optimization: Within budget constraints
⚠️ Recommendation: Add AWS WAF for additional security layer
```

**4. Code Generator** (Claude Code SDK):
```
🔨 Generating:
- Terraform infrastructure (ECS, Aurora, S3, CloudWatch)
- FastAPI application with sub-100ms endpoint
- CI/CD pipeline (GitHub Actions)
- Monitoring dashboards (CloudWatch, Prometheus)
```

---

### Act 3: Production-Ready Output

**Download Complete Repository:**

```
fraud-detection-mlops/
├── infra/terraform/           # AWS infrastructure
│   ├── ecs.tf                # ECS Fargate cluster
│   ├── aurora.tf             # Aurora Serverless v2
│   └── waf.tf                # AWS WAF rules
├── src/api/                  # FastAPI application
│   ├── main.py               # Sub-100ms fraud detection endpoint
│   └── models/               # ML model serving
├── .github/workflows/        # CI/CD pipelines
│   └── deploy.yml            # Automated deployment
├── monitoring/               # Observability
│   └── cloudwatch-dashboard.json
└── docs/                     # Architecture & compliance docs
    └── PCI_DSS_compliance.md
```

**One-Click Deploy:**
```bash
cd fraud-detection-mlops
terraform init && terraform apply
# 🚀 System deployed in 8 minutes
```

---

## 🏛️ Three Pillars of Intelligent MLOps Design

![Three Pillars of Intelligent MLOps](docs/assets/portfolio_images/1.png)
*Multi-agent orchestration flow: From natural language input to production code through intelligent automation*

### Pillar 1: Intelligent Automation

**Multi-Agent Collaboration:**
- **Constraint Extractor**: Parses natural language requirements into structured constraints (performance, security, scalability)
- **Planner Agent**: Designs comprehensive MLOps architecture based on AWS best practices and extracted constraints
- **Critic Agents**:
  - *Feasibility Critic*: Validates technical viability and identifies potential bottlenecks
  - *Policy Critic*: Ensures compliance with security, governance, and cost policies
  - *Optimization Critic*: Recommends cost/performance improvements
- **Code Generator**: Produces complete repositories with infrastructure code, application logic, CI/CD, and monitoring

**Result**: Automated end-to-end workflow from requirements to deployable code with built-in validation.

### Pillar 2: Real-Time Transparency

**Watch AI Agents Think:**
- **Streaming Reasoning Cards**: Expandable cards showing agent inputs, reasoning process, and outputs in real-time
- **Confidence Scoring**: Visual indicators (🟢 High >0.85, 🟡 Medium 0.7-0.85, 🔴 Low <0.7) showing agent certainty
- **Human-in-the-Loop Gates**: Automated approval requests when confidence drops below thresholds, with configurable auto-approval timeouts (default: 5 minutes)
- **Server-Sent Events (SSE)**: Real-time streaming architecture with deduplication and resilient reconnection

**Result**: Build trust through transparency—see exactly how AI makes decisions and intervene when needed.

### Pillar 3: Production-Ready Output

**Complete Infrastructure:**
- **Terraform Modules**: Compute (ECS, Lambda, App Runner), Storage (RDS, S3), Networking (VPC, ALB), Security (IAM, KMS), Monitoring (CloudWatch)
- **Application Code**: FastAPI backends, Next.js frontends, ML model serving (TensorFlow/PyTorch), data pipelines
- **CI/CD Pipelines**: GitHub Actions with automated testing, security scanning, deployment, and rollback strategies
- **Monitoring & Observability**: CloudWatch dashboards, Prometheus metrics, distributed tracing (X-Ray), structured logging

**Result**: Deploy immediately with confidence—all code follows best practices and includes comprehensive testing.

---

## 🏗️ System Architecture

The platform consists of five integrated layers working in concert:

**Client Layer (Next.js 14):**
- Real-time streaming UI with expandable reason cards
- Server-Sent Events (SSE) client for live agent updates
- Responsive design with Tailwind CSS

**API Layer (FastAPI + Integrated Worker):**
- Async REST endpoints for job management
- SSE streaming server for real-time agent reasoning
- Background job processing integrated within API process

**Orchestration Layer (LangGraph):**
- Multi-agent workflow engine with deterministic state management
- Conditional routing based on confidence scores and validation results
- Human-in-the-Loop gates with auto-approval timeouts
- PostgreSQL checkpointing for crash recovery and workflow replay

**Agent Layer (GPT-4 + Claude):**
- OpenAI GPT-4/5 for constraint extraction, planning, and criticism
- Claude Code SDK or OpenAI for production code generation (configurable)
- Specialized prompts for each agent role with domain knowledge

**Data Layer (PostgreSQL + S3):**
- PostgreSQL for job queue, LangGraph checkpoints, and state persistence
- S3 for generated code artifacts (zipped repositories)
- RDS Proxy for connection pooling and auto-scaling

For detailed architecture diagrams and technical specifications, see [Architecture Deep Dive](docs/part3-architecture-deep-dive.md).

---

## 🔬 Technical Architecture Deep Dive

### Multi-Agent Decision Flow

![Multi-Agent Decision Flow](docs/assets/portfolio_images/4.png)
*Intelligent routing with conditional logic: Agents collaborate through feedback loops, HITL gates, and automated validation*

The platform uses sophisticated conditional routing to ensure quality:
- **Low confidence** (<0.75): Triggers human-in-the-loop approval gate
- **Feasibility issues**: Routes back to planner with critic feedback
- **Policy violations**: Automatically adds compliance components and re-validates
- **All critics pass**: Proceeds to code generation with validated plan

### Database Schema & State Management

![Database Schema](docs/assets/portfolio_images/5.png)
*LangGraph-optimized database design: Jobs, Checkpoints, and Writes tables enable deterministic workflow replay and crash recovery*

**Key Design Decisions:**
- **JSONB for constraints**: Flexible schema accommodates varying requirement types
- **LangGraph Checkpoints**: Full state snapshots at each agent step for time-travel debugging
- **Pending Writes**: Channel-based buffering ensures deterministic replay
- **UUID primary keys**: Distributed-system-ready with zero collision risk

### Streaming Architecture (SSE)

![SSE Streaming Architecture](docs/assets/portfolio_images/6.png)
*Real-time event streaming with two-layer deduplication: Backend event IDs + frontend Set cache prevent duplicate reason cards*

**Resilient Connection Handling:**
- **Monotonic Event IDs**: `{job_id}:{sequence}` format enables reconnection with missed event replay
- **Last-Event-ID Header**: Clients resume from last received event after network interruptions
- **Heartbeat Pings**: Keep-alive comments every 30 seconds prevent proxy timeouts
- **Deduplication**: Backend assigns unique IDs, frontend tracks seen events to prevent duplicate UI updates

### Job Queue Pattern (Race Condition Prevention)

![Job Queue Pattern](docs/assets/portfolio_images/7.png)
*PostgreSQL `FOR UPDATE SKIP LOCKED` pattern: Zero race conditions through database ACID guarantees*

**Why Database-Backed Queue?**
- **ACID Guarantees**: Impossible for two workers to claim the same job
- **No Extra Infrastructure**: Reuses existing PostgreSQL (vs Redis + Celery)
- **Integrated Checkpointing**: Job state and LangGraph state in same database
- **Automatic Recovery**: Stale job detection resets jobs stuck >10 minutes

### Complete Tech Stack

![Tech Stack Visualization](docs/assets/portfolio_images/8.png)
*Full technology stack across six layers: From presentation (Next.js) to infrastructure (AWS App Runner) with external LLM APIs*

**Technology Rationale:**
- **FastAPI**: Async/await for SSE streaming, automatic OpenAPI docs, 3x faster than Flask
- **LangGraph**: Deterministic workflows with checkpointing (better than LangChain for complex agents)
- **PostgreSQL**: Native LangGraph support, JSONB for semi-structured data, `FOR UPDATE SKIP LOCKED` for job queue
- **Server-Sent Events**: Simpler than WebSockets (no handshake), auto-reconnect, works with CDN/proxies
- **AWS App Runner**: Zero-config auto-scaling, managed SSL, simpler than ECS/EKS

---

## 🔧 Technical Challenges Solved

### Challenge 1: SSE Streaming Duplicate Events & Connection Resilience

**Problem**: Network interruptions caused duplicate reason cards in the UI during reconnection.

**Root Causes**:
- EventSource auto-reconnect re-sent all events from job start
- Load balancer failover to new instance lost event history
- No mechanism to replay only missed events

**Solution: Two-Layer Deduplication + Event Replay**

**Backend (FastAPI)**:
```python
# Assign monotonic event IDs for reconnection support
event_id = f"{job_id}:{sequence_number}"

# Replay missed events from Last-Event-ID header
last_event_id = request.headers.get("Last-Event-ID", "0")
start_seq = int(last_event_id.split(":")[-1]) + 1
missed_events = await get_events_since(job_id, start_seq)
```

**Frontend (React)**:
```typescript
const seenEventIds = new Set<string>();

eventSource.onmessage = (event) => {
  if (seenEventIds.has(event.lastEventId)) return; // Skip duplicate
  seenEventIds.add(event.lastEventId);
  handleEvent(event.data);
};
```

**Result**: Zero duplicate events through backend event IDs + frontend Set cache, resilient to network failures and load balancer changes.

---

### Challenge 2: Database Job Queue Race Conditions

**Problem**: Initial Redis + Celery setup had race conditions where multiple workers picked up the same job during high load.

**Failed Approach**:
```python
# BROKEN: Two workers can SELECT same job
job = await db.execute("SELECT * FROM jobs WHERE status = 'pending' LIMIT 1")
await db.execute("UPDATE jobs SET status = 'processing' WHERE id = :id", {"id": job.id})
```

**Solution: PostgreSQL `FOR UPDATE SKIP LOCKED`**

```python
async with db.begin():  # Transaction
    result = await db.execute("""
        SELECT * FROM jobs
        WHERE status = 'pending'
        ORDER BY created_at ASC
        LIMIT 1
        FOR UPDATE SKIP LOCKED  -- Key: Skip already-locked rows
    """)
    job = result.fetchone()

    if job:
        await db.execute("UPDATE jobs SET status = 'processing' WHERE id = :id", {"id": job.id})
        # COMMIT (lock released)
```

**Result**: Impossible for two workers to claim the same job through database ACID guarantees, no Redis needed.

---

### Challenge 3: LangGraph State Schema Consolidation

**Problem**: Early implementation used 15 separate `TypedDict` schemas for different agents, causing 500KB checkpoints and type casting errors.

**Solution: Single Consolidated `AgentState`**

```python
class AgentState(TypedDict):
    """Single source of truth for entire workflow."""

    # User input
    user_requirements: str

    # Constraint extraction
    extracted_constraints: dict[str, Any]
    constraint_confidence: float

    # Planning
    architecture_plan: str
    plan_confidence: float

    # Critics
    feasibility_feedback: list[dict]
    policy_feedback: list[dict]

    # Code generation
    generated_artifact_url: str | None

    # Workflow control
    workflow_status: Literal["running", "hitl_required", "completed", "failed"]
```

**Benefits**:
- **Type safety restored**: MyPy validates field access at type-check time
- **70% checkpoint size reduction**: 500KB → 150KB through single schema
- **Simplified routing**: Direct access to all fields without type conversions

---

### Challenge 4: HITL Auto-Approval Timeout

**Problem**: Workflows blocked indefinitely when users went offline after submitting jobs.

**Solution: Context-Aware Auto-Approval**

```python
async def monitor_hitl_timeouts():
    """Background worker auto-approves timed-out HITL gates."""
    while True:
        await asyncio.sleep(30)

        jobs = await db.execute("""
            SELECT id, thread_id, hitl_triggered_at, hitl_timeout_seconds
            FROM jobs WHERE workflow_status = 'hitl_required'
        """)

        for job in jobs:
            elapsed = (datetime.utcnow() - job.hitl_triggered_at).total_seconds()

            if elapsed >= job.hitl_timeout_seconds:
                # Auto-approve and resume workflow
                await send_command(thread_id=job.thread_id, command={"type": "resume"})
```

**Context-Aware Timeouts**:
- **Security/compliance**: 1 hour timeout
- **High-cost resources**: 30 minutes timeout
- **Minor optimizations**: 3 minutes timeout
- **Default**: 5 minutes timeout

**Result**: No stuck workflows—jobs complete through user approval or auto-approval, with audit trail tracking.

---

## 📊 Key Capabilities & Metrics

### Automation Benefits

Transform traditional multi-week MLOps design processes into automated workflows:

- **Requirements Analysis**: AI-powered constraint extraction processes natural language requirements in minutes instead of days of manual review
- **Architecture Design**: Multi-agent collaborative design replaces weeks of architect time with automated planning and validation
- **Code Generation**: Automated repository generation eliminates weeks of manual development
- **Compliance Validation**: Policy agents provide instant validation against PCI DSS, HIPAA, GDPR, SOC 2 rules

**Result**: Complete, production-ready MLOps systems generated in **under an hour** instead of **8-12 weeks** of traditional development.

---

### Code Generation Capabilities

**Infrastructure Generated:**
- ✅ Terraform modules (AWS: ECS, Lambda, RDS, S3, VPC, CloudWatch)
- ✅ Kubernetes manifests (Deployments, Services, Ingress, HPA)
- ✅ Docker configurations (multi-stage builds, security scanning)

**Application Code:**
- ✅ FastAPI backends (REST APIs, WebSocket, background tasks)
- ✅ Next.js frontends (App Router, Server Components, Tailwind)
- ✅ ML model serving (TensorFlow Serving, PyTorch Serve, custom inference)
- ✅ Data pipelines (Airflow DAGs, Prefect flows, dbt models)

**CI/CD Pipelines:**
- ✅ GitHub Actions workflows (test, build, deploy, security scans)
- ✅ GitLab CI pipelines (multi-stage, parallel jobs, artifacts)
- ✅ Deployment scripts (blue-green, canary, rollback strategies)

**Monitoring & Observability:**
- ✅ CloudWatch dashboards (custom metrics, alarms)
- ✅ Prometheus + Grafana (scrape configs, recording rules, alerts)
- ✅ Distributed tracing (Jaeger, Zipkin, OpenTelemetry)
- ✅ Structured logging (JSON format, correlation IDs)

---

### Performance Characteristics

**Typical Workflow Timeline:**
- **Constraint Extraction**: ~10 seconds
- **Architecture Planning**: ~30-45 seconds
- **Design Validation**: ~45 seconds (3 critic agents in parallel)
- **Code Generation**: ~90-120 seconds
- **End-to-End**: Typically completes in **3-5 minutes**

**Scalability:**
- Auto-scales from 1 to 25 instances based on load (AWS App Runner)
- Database connection pooling via RDS Proxy for consistent performance
- Asynchronous job processing with PostgreSQL-backed queue

---

### Cost Model

**Per-Workflow Costs (Estimated):**
- **LLM API Usage**: ~$2-3 per workflow
  - OpenAI GPT-4/5 for planning and critics
  - OpenAI or Claude for code generation (configurable via `CODEGEN_PROVIDER`)

**Infrastructure Costs (Monthly Fixed):**
- **AWS App Runner**: ~$50-100 (auto-scaling containers)
- **RDS PostgreSQL**: ~$100-150 (db.t3.medium + storage)
- **S3 + Data Transfer**: ~$20-30
- **Total**: ~$200-300/month for infrastructure

**Value Proposition**: Traditional MLOps system design requires weeks of architect and developer time. This platform automates the entire workflow, reducing both time and resource requirements significantly.

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+ with [uv](https://docs.astral.sh/uv/) package manager
- Node.js 20+ with npm
- Git
- (Optional) AWS CLI for production deployment

### Installation

**1. Clone the repository**
```bash
git clone https://github.com/deepak-karkala/agentic-mlops.git
cd agentic-mlops
```

**2. Install Python dependencies**
```bash
uv sync --extra dev
```

**3. Install frontend dependencies**
```bash
npm install --prefix frontend
```

**4. Configure environment variables**
```bash
cp .env.example .env
```

Edit `.env` and add your API keys:
```bash
# Required: OpenAI API key for agents and code generation
OPENAI_API_KEY=your-openai-api-key

# Optional: Only if you want Claude Code SDK for generation
ANTHROPIC_API_KEY=your-anthropic-api-key

# Optional: Choose code generation provider (auto-detects by default)
CODEGEN_PROVIDER=auto  # Options: auto (default), openai, claude
```

**5. Start the application**
```bash
# Terminal 1: Start API + integrated worker
PYTHONPATH=. uv run uvicorn api.main:app --reload --port 8000

# Terminal 2: Start frontend
cd frontend && npm run dev
```

**6. Access the application**
- **Frontend**: http://localhost:3000
- **API docs**: http://localhost:8000/docs

---

## 🛠️ Technologies Used

### Backend
- [FastAPI](https://fastapi.tiangolo.com/) - Async web framework with automatic OpenAPI docs
- [LangGraph](https://langchain-ai.github.io/langgraph/) - Multi-agent orchestration with checkpointing
- [SQLAlchemy](https://www.sqlalchemy.org/) - Async database ORM with PostgreSQL/SQLite support
- [Pydantic](https://docs.pydantic.dev/) - Data validation and settings management
- [OpenAI SDK](https://github.com/openai/openai-python) - GPT-4/5 API client for agents
- [Anthropic SDK](https://github.com/anthropics/anthropic-sdk-python) - Claude API client (optional)

### Frontend
- [Next.js 14](https://nextjs.org/) - React framework with App Router and Server Components
- [TypeScript](https://www.typescriptlang.org/) - Type safety for frontend code
- [Tailwind CSS](https://tailwindcss.com/) - Utility-first styling framework
- [EventSource API](https://developer.mozilla.org/en-US/docs/Web/API/EventSource) - SSE client for real-time streaming

### Infrastructure
- [AWS App Runner](https://aws.amazon.com/apprunner/) - Managed container platform with auto-scaling
- [AWS RDS](https://aws.amazon.com/rds/) - Managed PostgreSQL with RDS Proxy
- [AWS S3](https://aws.amazon.com/s3/) - Object storage for generated code artifacts
- [Terraform](https://www.terraform.io/) - Infrastructure as Code for AWS deployment

### DevOps
- [GitHub Actions](https://github.com/features/actions) - CI/CD pipelines
- [Playwright](https://playwright.dev/) - End-to-end browser testing
- [Pytest](https://docs.pytest.org/) - Python testing framework with async support
- [Ruff](https://docs.astral.sh/ruff/) - Fast Python linter and formatter
- [pre-commit](https://pre-commit.com/) - Git hooks for code quality

---

## 🚢 Deployment

### AWS Deployment (Production)

Deploy to AWS in 3 steps:

```bash
# Prerequisites: AWS CLI configured, Terraform installed

# 1. Deploy infrastructure (RDS, S3, App Runner)
cd infra/terraform
terraform init
terraform apply

# 2. Build and push Docker images
./scripts/build-and-push.sh

# 3. Deploy application
./scripts/deploy-app-runner.sh

# Your app is now live at:
# https://<app-runner-url>.us-east-1.awsapprunner.com
```

**Estimated Cost**: ~$200-300/month (includes RDS, App Runner, S3, excluding LLM API usage)

See [AWS Deployment Guide](docs/deployment_guide.md) for detailed instructions.

### Alternative: Railway.app

For a simpler deployment option with managed PostgreSQL and automatic HTTPS, see the [Railway Deployment Guide](docs/railway_deployment_guide.md).

---

## 📖 Documentation

Comprehensive technical documentation is available in the [`docs/`](docs/) folder:

- **[System Overview](docs/part1-system-overview.md)** - High-level architecture, technology stack, and design decisions
- **[Technical Specifications](docs/part2-technical-specifications.md)** - API contracts, data models, agent workflows, and system interfaces
- **[Architecture Deep Dive](docs/part3-architecture-deep-dive.md)** - Frontend/backend implementation, LangGraph orchestration, and SSE streaming
- **[Operations & Production](docs/part4-operations-production.md)** - Deployment guides, monitoring, security best practices, and operational procedures
- **[Streaming Architecture Guide](docs/streaming-architecture-guide.md)** - Real-time SSE implementation with deduplication and resilient connections

---

## 🤝 Call to Action

### Ready to Transform Your MLOps Workflow?

**Try it yourself:**
1. **[Live Demo](#)**: Submit your requirements and watch agents design your system in real-time *(coming soon)*
2. **[GitHub](https://github.com/deepak-karkala/agentic-mlops)**: Clone the repository, run locally, and customize for your use case
3. **[Documentation](docs/)**: Deep dive into architecture, technical challenges, and implementation details

### Connect with Me

**I'm looking for opportunities to collaborate in:**
- AI/ML Engineering (multi-agent systems, LLMs, production ML)

**Let's connect:**
- **Email**: dkarkala01@gmail.com
- **LinkedIn**: [linkedin.com/in/deepak-karkala](https://linkedin.com/in/deepak-karkala)
- **GitHub**: [@deepak-karkala](https://github.com/deepak-karkala)
- **Portfolio**: [deepakkarkala.com](https://deepakkarkala.com)

---

**Built with ❤️ using Claude Code, LangGraph, OpenAI, Next.js, and FastAPI**
