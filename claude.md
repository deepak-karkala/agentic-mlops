# Agentic MLOps Platform

A collaborative multi-agent system that designs, critiques, and generates production-quality MLOps systems using AWS App Runner, LangGraph orchestration, and Claude Code generation.

## Development Commands

```bash
# Setup
uv sync --extra dev
npm install --prefix frontend

# Local development
uv run fastapi dev api/main.py     # API server
uv run python worker/main.py       # Worker service
npm run dev --prefix frontend      # Frontend dev server

# Testing & Quality
pre-commit run --all-files         # Lint and format
pytest                             # Python tests
npm test                           # Frontend tests

# Build & Deploy
./1-deploy-infrastructure.sh       # AWS infrastructure
./2-build-and-push.sh              # Build and push containers
./3-deploy-app-runner.sh           # Deploy applications
```

## Project Structure

- `api/` - FastAPI backend with REST endpoints
- `worker/` - Background job processor using LangGraph
- `frontend/` - Next.js React application with Tailwind CSS
- `infra/terraform/` - AWS infrastructure as code
- `libs/` - Shared Python libraries
- `tests/` - Test files

## Code Style

- Python: Use `ruff` for formatting and linting
- TypeScript: Follow Next.js conventions with Tailwind CSS
- Commits: Use conventional commit format (`feat:`, `fix:`, `docs:`)
- Always run `pre-commit run --all-files` before committing

## Key Architecture Decisions

- **Orchestration**: LangGraph for deterministic agent workflows
- **Code Generation**: Anthropic Claude Code for repository generation
- **Deployment**: AWS App Runner + RDS Postgres + S3
- **State Management**: PostgreSQL with checkpointing for workflow persistence
- **Job Queue**: Database-backed with `FOR UPDATE SKIP LOCKED` pattern

## Development Workflow

1. Create feature branch from `main`
2. Make changes following existing patterns
3. Run tests and quality checks
4. Create PR with descriptive title
5. All CI checks must pass before merge

## Environment Setup

Required environment variables:
- `DATABASE_URL` - RDS Proxy endpoint
- `S3_BUCKET_NAME` - Artifacts storage bucket
- `AWS_REGION` - AWS region (default: us-east-1)
- `ANTHROPIC_API_KEY` - For Claude Code generation
- `OPENAI_API_KEY` - For LangGraph orchestration

## Testing Strategy

- Unit tests for core logic
- Integration tests for database operations
- End-to-end tests for full workflows
- Golden runs for agent determinism
- Static validation for generated code

## Troubleshooting

- **Database connection issues**: Check RDS Proxy configuration
- **Job queue stuck**: Verify worker is running and claiming jobs
- **Frontend build errors**: Ensure Node.js 20+ and clean `npm install`
- **Deployment failures**: Check AWS credentials and Terraform state