# Agentic MLOps Platform

A collaborative multi-agent system that designs, critiques, and generates production-quality MLOps systems using AWS App Runner, LangGraph orchestration, and AI-powered code generation (Claude Code SDK or OpenAI API).

## Quick Start

### Prerequisites
- Python 3.11+ with [uv](https://docs.astral.sh/uv/) package manager
- Node.js 20+ with npm
- Git
- (Optional) AWS CLI for deployment

### Development Setup

1. **Clone and setup Python environment:**
   ```bash
   git clone <repository-url>
   cd agentic-mlops
   uv sync --extra dev
   ```

2. **Setup frontend dependencies:**
   ```bash
   npm install --prefix frontend
   ```

3. **Configure environment variables:**
   ```bash
   # Copy example env file and customize
   cp .env.example .env

   # REQUIRED: At least one API key
   export OPENAI_API_KEY="your-openai-api-key"       # Required for agents + can be used for codegen

   # OPTIONAL: Only needed if you want to use Claude Code SDK for generation
   export ANTHROPIC_API_KEY="your-anthropic-api-key" # Optional - for Claude Code SDK

   # Code generation provider (auto-detects by default)
   export CODEGEN_PROVIDER="auto"  # Options: auto (default), openai, claude
   ```

4. **Start development servers:**
   ```bash
   # Terminal 1: Start integrated API + Worker server
   PYTHONPATH=. uv run uvicorn api.main:app --reload --port 8000

   # Terminal 2: Start frontend development server
   cd frontend && npm run dev
   ```

5. **Access the application:**
   - Frontend: http://localhost:3000
   - API docs: http://localhost:8000/docs

## Development Commands

```bash
# Setup
uv sync --extra dev                         # Install Python dependencies
npm install --prefix frontend              # Install frontend dependencies

# Local development
PYTHONPATH=. uv run uvicorn api.main:app --reload --port 8000  # Integrated API + Worker
cd frontend && npm run dev                  # Frontend dev server (port 3000)

# Graph Configuration
export GRAPH_TYPE=full           # Default: full graph with all features
export HITL_MODE=interactive     # HITL mode: demo, interactive, disabled

# Testing & Quality
pre-commit run --all-files                 # Lint and format all files
uv run pytest -v                          # Run Python tests
uv run pytest -v -m "not slow"            # Run fast tests only
cd frontend && npm test                    # Frontend unit tests
cd frontend && npm run test:e2e            # Playwright E2E tests

# Build & Deploy
./scripts/1-deploy-infrastructure.sh       # Deploy AWS infrastructure
./scripts/2-build-and-push.sh              # Build and push containers
./scripts/3-deploy-app-runner.sh           # Deploy applications
./scripts/test-e2e-playwright.sh           # Playwright E2E testing (recommended)
./scripts/test-e2e.sh                      # Basic curl-based testing
```

## Project Structure

- `api/` - FastAPI backend with integrated worker and REST endpoints
- `frontend/` - Next.js React application with real-time streaming UI
- `libs/` - Shared Python libraries (LangGraph agents, streaming, database)
- `infra/terraform/` - AWS infrastructure as code (App Runner, RDS, S3)
- `tests/` - Test files (unit, integration, E2E with Playwright)
- `docs/` - Documentation and architecture guides
- `scripts/` - Deployment and testing automation scripts

### Key Components

- **API Server** (`api/main.py`): Integrated FastAPI + background worker with SSE streaming
- **Frontend** (`frontend/`): Next.js with real-time chat interface and streaming reason cards
- **Agents** (`libs/`): LangGraph-based multi-agent system for MLOps design
- **Streaming** (`libs/streaming_service.py`): Real-time SSE events for agent reasoning
- **Database** (`libs/database.py`): SQLite (dev) / PostgreSQL (prod) with checkpointing

## Code Style

- Python: Use `ruff` for formatting and linting
- TypeScript: Follow Next.js conventions with Tailwind CSS
- Commits: Use conventional commit format (`feat:`, `fix:`, `docs:`)
- Always run `pre-commit run --all-files` before committing

## Key Architecture Decisions

- **Orchestration**: LangGraph for deterministic agent workflows with checkpointing
- **Graph Type**: `build_full_graph()` is the default production graph with all features (HITL, streaming, complete workflow)
- **HITL Modes**: Configurable human-in-the-loop via HITL_MODE (demo/interactive/disabled)
- **Streaming**: Server-Sent Events (SSE) for real-time agent reasoning updates
- **Code Generation**: Anthropic Claude Code for repository generation
- **Deployment**: AWS App Runner + RDS Postgres + S3 for production
- **State Management**: PostgreSQL with LangGraph checkpointing for workflow persistence
- **Job Queue**: Database-backed with `FOR UPDATE SKIP LOCKED` pattern
- **UI Framework**: Next.js with Tailwind CSS and responsive design
- **Real-time Updates**: Integrated worker with SSE streaming for live agent reasoning
- **Legacy Graphs**: thin/hitl/hitl_enhanced/streaming_test maintained for backward compatibility

## Development Workflow

1. Create feature branch from `main`
2. Make changes following existing patterns
3. Run tests and quality checks
4. Create PR with descriptive title
5. All CI checks must pass before merge

## Environment Setup

### Required Environment Variables

**For Local Development:**
```bash
# LLM API Keys (at least OPENAI_API_KEY required)
OPENAI_API_KEY=your-openai-api-key              # For LangGraph agents + code generation
ANTHROPIC_API_KEY=your-anthropic-api-key        # Optional - only for Claude Code SDK

# Code Generation Provider (optional - auto-detects by default)
CODEGEN_PROVIDER=auto                            # auto (default), openai, claude

# Graph Configuration (recommended)
GRAPH_TYPE=full                                  # full (recommended), thin, hitl, hitl_enhanced, streaming_test
HITL_MODE=interactive                            # demo (3s), interactive (15s), disabled (0s)
HITL_DEFAULT_TIMEOUT=8                           # Timeout in seconds for auto-approval

# Database (optional - uses SQLite by default)
DATABASE_URL=sqlite:///./agentic_mlops.db       # Local development
# DATABASE_URL=postgresql://user:pass@host:5432/db  # Production

# Logging (optional)
LOG_LEVEL=INFO                                   # DEBUG, INFO, WARNING, ERROR
```

**For Production Deployment:**
```bash
# AWS Configuration
AWS_REGION=us-east-1                            # AWS region
S3_BUCKET_NAME=your-artifacts-bucket            # S3 bucket for artifacts
DATABASE_URL=postgresql://user:pass@rds-proxy:5432/mlops  # RDS Postgres

# API Keys (OPENAI_API_KEY required, ANTHROPIC_API_KEY optional)
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key        # Optional

# Code Generation Provider
CODEGEN_PROVIDER=auto                            # auto, openai, or claude

# Graph Configuration
GRAPH_TYPE=full                                  # Use full graph for production
HITL_MODE=interactive                            # Or 'disabled' for fully automated workflows

# Frontend Configuration
NEXT_PUBLIC_API_BASE_URL=https://your-api-domain.com  # API base URL for frontend
```

### Database Setup

**Local Development:**
- SQLite is used by default (no setup required)
- Database file: `./agentic_mlops.db`

**Production:**
- PostgreSQL via AWS RDS
- Configured via Terraform in `infra/terraform/`

### Code Generation Provider Options

The platform supports two LLM providers for code generation:

**OpenAI API (Recommended for Most Users):**
- ✅ Works with just `OPENAI_API_KEY` (no additional setup)
- ✅ Uses GPT-4/GPT-5 models for repository generation
- ✅ Same API key for both agents and code generation
- ✅ Easier payment options (especially for non-US users)
- ⚠️ Slightly different code generation approach than Claude Code SDK

**Claude Code SDK:**
- ✅ Native Claude Code SDK integration
- ✅ Optimized for code generation tasks
- ⚠️ Requires separate `ANTHROPIC_API_KEY`
- ⚠️ Payment issues for some regions (Indian cards, etc.)

**Configuration:**
```bash
# Option 1: Auto-detect (default) - uses Claude if available, falls back to OpenAI
CODEGEN_PROVIDER=auto

# Option 2: Explicitly use OpenAI (recommended if no Anthropic API access)
CODEGEN_PROVIDER=openai
OPENAI_API_KEY=your-openai-api-key

# Option 3: Explicitly use Claude Code SDK
CODEGEN_PROVIDER=claude
ANTHROPIC_API_KEY=your-anthropic-api-key
```

**Why OpenAI Option Was Added:**
- Solves payment issues for users in regions where Anthropic API payments are difficult
- Allows running the entire platform with a single API provider
- Reduces setup complexity for new users

## Features

### Real-time Streaming Interface

- **Live Agent Reasoning**: Watch agents think and make decisions in real-time
- **Reason Cards**: Expandable cards showing agent inputs, outputs, and decision rationale
- **Progress Tracking**: Visual workflow progress with step-by-step updates
- **Structured Data Display**: Collapsible JSON sections for extracted information and outputs
- **Responsive Design**: Optimized for both desktop and mobile viewing

### Enhanced User Experience

- **Chat Interface**: Natural language input for MLOps requirements
- **Real-time Updates**: Server-Sent Events (SSE) for instant feedback
- **Confidence Indicators**: Visual confidence scores and uncertainty warnings
- **Interactive Elements**: Expandable sections for detailed agent reasoning
- **Status Badges**: Clear job status indicators (pending, processing, completed, failed)

### Agent Capabilities

- **Multi-Agent Orchestration**: Planner, critics, policy engine, and code generation
- **Constraint Extraction**: Intelligent parsing of natural language requirements
- **Architecture Design**: Automated MLOps system design and validation
- **Code Generation**: Production-ready infrastructure and application code
- **Policy Compliance**: Automated compliance checking and recommendations

## Testing Strategy

- Unit tests for core logic
- Integration tests for database operations
- End-to-end tests for full workflows
- Golden runs for agent determinism
- Static validation for generated code

## Troubleshooting

### Common Development Issues

**Python/Backend Issues:**
- **ModuleNotFoundError: No module named 'langgraph'**: Use `PYTHONPATH=. uv run uvicorn api.main:app --reload` instead of `fastapi dev`
- **Database connection issues**: Check `DATABASE_URL` environment variable or use default SQLite
- **Job queue stuck**: Restart the API server - worker is integrated, no separate process needed
- **SSE streaming not working**: Check browser network tab for event-stream connection
- **LLM API errors**: Verify `OPENAI_API_KEY` is set (required). `ANTHROPIC_API_KEY` only needed if `CODEGEN_PROVIDER=claude`
- **Code generation fails**: If using Claude SDK and getting payment/API errors, switch to OpenAI: `CODEGEN_PROVIDER=openai`

**Frontend Issues:**
- **Frontend build errors**: Ensure Node.js 20+ and run `npm install --prefix frontend`
- **Real-time updates not showing**: Check browser console for SSE connection errors
- **API connection issues**: Verify `NEXT_PUBLIC_API_BASE_URL` points to running API server
- **Styling issues**: Clear Next.js cache with `rm -rf frontend/.next`

**Development Environment:**
- **Port conflicts**: API uses 8000, frontend uses 3000 - ensure ports are available
- **CORS issues**: Handled automatically in development, check production CORS settings
- **Hot reload not working**: Restart development servers

### Production Deployment Issues

- **AWS deployment failures**: Check AWS credentials and Terraform state
- **App Runner issues**: Check CloudWatch logs for application errors
- **Database connection**: Verify RDS Proxy configuration and security groups
- **S3 access**: Ensure IAM roles have proper S3 permissions

### Performance Issues

- **Slow agent responses**: Check OpenAI API rate limits and model selection
- **High memory usage**: Monitor LangGraph checkpointing and database connections
- **Frontend performance**: Use React DevTools Profiler to identify bottlenecks

### Debugging Tips

- **Enable debug logging**: Set `LOG_LEVEL=DEBUG` for verbose output
- **Monitor SSE events**: Use browser DevTools Network tab to inspect event-stream
- **Database inspection**: Use SQLite browser for local DB, pgAdmin for production
- **Agent tracing**: Enable LangGraph tracing for detailed workflow analysis