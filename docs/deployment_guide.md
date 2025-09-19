# Complete AWS Deployment Guide for Agentic MLOps Platform

This guide covers the complete end-to-end deployment process for the 2-service architecture: Frontend (Next.js) and API (FastAPI with integrated worker).

## Prerequisites

Install the following tools if needed:

```bash
# Install Terraform
brew install terraform

# Install AWS CLI  
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
sudo installer -pkg AWSCLIV2.pkg -target /

# Install Docker Desktop
# Download from: https://www.docker.com/products/docker-desktop

# Install GitHub CLI (for optional PR management)
brew install gh
```

## Step-by-Step Deployment Process

### Step 1: Configure AWS Credentials

```bash
aws configure
```
Enter your AWS Access Key ID, Secret Access Key, region (`us-east-1`), and output format (`json`)

### Step 2: Deploy Infrastructure Foundation

```bash
./scripts/1-deploy-infrastructure.sh
```

**What this does:**
- Creates S3 bucket for Terraform state management
- Gets default VPC and subnet information
- Deploys core infrastructure:
  - ECR repositories (API, Frontend)
  - RDS Postgres database with RDS Proxy
  - S3 bucket for artifacts storage
  - Security groups and IAM roles
  - VPC connector for App Runner services

**Important:** This step does NOT deploy the App Runner services yet - only the foundation.

### Step 3: Build and Push Container Images

```bash
./scripts/2-build-and-push.sh
```

**What this does:**
- Builds Docker images for both services:
  - `api/Dockerfile` - FastAPI backend with integrated worker and uv package manager
  - `frontend/Dockerfile` - Next.js with standalone output (multi-stage build)
- Pushes all images to their respective ECR repositories
- Saves image URIs to `deployment-config.env` for next phase

### Step 4: Deploy App Runner Services

```bash
./scripts/3-deploy-app-runner.sh
```

**What this does:**
- Deploys both App Runner services simultaneously:
  - **API Service**: FastAPI backend with integrated worker, database connectivity, and background job processing
  - **Frontend Service**: Next.js app configured to call the API
- Configures environment variables and service communication
- Sets up auto-scaling and health checks

## Understanding Service Dependencies

### Deployment Order Logic

The services are deployed in a specific order to handle dependencies:

1. **Infrastructure First** (`1-deploy-infrastructure.sh`)
   - No service dependencies
   - Creates foundation resources

2. **Container Images** (`2-build-and-push.sh`)
   - No runtime dependencies
   - Just builds and stores images

3. **Services Together** (`3-deploy-app-runner.sh`)
   - API (with integrated worker) and Frontend deployed simultaneously
   - Frontend gets API URL via environment variable
   - **No circular dependency** because:
     - API doesn't need to know Frontend URL at startup
     - Frontend gets API URL from Terraform output
     - CORS uses wildcard pattern for AWS domains

### Service Communication Flow

```
Frontend (Next.js)
    ↓ HTTP Requests + SSE Streaming
API (FastAPI + Integrated Worker)
    ↓ Database Queries + Job Processing
RDS Postgres (with background asyncio tasks)
```

**Key Architecture Changes:**
- **Integrated Worker**: LangGraph worker runs as background asyncio task within the API server
- **Direct Streaming**: SSE events flow directly from worker to API to frontend (no HTTP bridge)
- **Simplified Deployment**: Single server process reduces complexity while maintaining job persistence

## What Gets Created

### AWS Resources

- **ECR Repositories**: 2 repositories for container images (API, Frontend)
- **RDS Postgres**: Database with RDS Proxy for connection pooling
- **S3 Bucket**: Storage for generated artifacts and Terraform state
- **App Runner Services**: 2 managed container services (API with integrated worker, Frontend)
- **VPC Connector**: Enables App Runner to access RDS in VPC
- **Security Groups**: Network security between services
- **IAM Roles**: Proper permissions for all services

### Environment Configuration

Each service gets appropriate environment variables:

**API Service (with Integrated Worker):**
```bash
DATABASE_URL=postgresql://postgres:password@proxy.region.rds.amazonaws.com:5432/postgres
S3_BUCKET_NAME=project-artifacts-bucket
AWS_REGION=us-east-1
ENVIRONMENT=production  # Enables restricted CORS
GRAPH_TYPE=full         # Enables full LangGraph with agent reasoning
```

**Frontend Service:**
```bash
NEXT_PUBLIC_API_BASE_URL=https://api-service-url.amazonaws.com
```

## Post-Deployment Verification

### Step 5: Run End-to-End Tests

You can run E2E tests using either approach:

#### Option A: Playwright E2E Tests (Recommended)
```bash
./scripts/test-e2e-playwright.sh
```

**What this tests:**
- Complete user workflow: typing message, sending, receiving response
- Frontend-to-API integration with real backend calls
- Real-time SSE streaming of agent reasoning (reason cards)
- UI responsiveness across different screen sizes
- Error handling and graceful degradation
- Keyboard navigation and accessibility
- Browser automation with Chromium/Firefox/Safari

#### Option B: Basic curl-based Tests
```bash
./scripts/test-e2e.sh
```

**What this tests:**
- API health endpoint (`/`)
- API chat endpoint (`/api/chat`) with real requests
- SSE streaming endpoint (`/api/streams/{id}`) for real-time events
- Frontend availability and content
- Basic service-to-service communication

### Get Service URLs

```bash
cd infra/terraform

# Get all service URLs
terraform output frontend_service_url
terraform output api_service_url  # Includes integrated worker functionality

# Get infrastructure details
terraform output db_proxy_endpoint
terraform output artifact_bucket_name
```

## Real-Time Streaming Features

### Server-Sent Events (SSE)
The integrated architecture supports real-time streaming of agent reasoning:

- **Reason Cards**: Live agent decision-making processes with confidence scores
- **Node Events**: Start/completion notifications for workflow steps
- **Progress Updates**: Real-time workflow progress with percentage completion
- **Error Handling**: Immediate error notification with retry logic

### Frontend Integration
The React frontend connects to SSE streams automatically:

```javascript
// SSE endpoint: https://api-service-url.amazonaws.com/api/streams/{decision_set_id}
const { reasonCards, workflowProgress, isConnected } = useStreamingEvents({
  decisionSetId: 'workflow-123',
  autoConnect: true
});
```

### Event Deduplication
Both backend and frontend implement comprehensive deduplication:
- **Backend**: Prevents duplicate agent reason cards during processing
- **Frontend**: Client-side deduplication with memory-efficient maps
- **Robust Reconnection**: Automatic reconnection with exponential backoff

## Troubleshooting Common Issues

### 1. ECR Permission Errors
```bash
# Re-authenticate with ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com
```

### 2. App Runner Service Failed to Start
- Check CloudWatch logs: AWS Console → App Runner → Service → Logs
- Verify environment variables are set correctly
- Ensure container exposes the correct port (3000 for frontend, 8000 for API)

### 3. Frontend Can't Connect to API
- Verify CORS configuration allows AWS App Runner domains
- Check `NEXT_PUBLIC_API_BASE_URL` environment variable
- Test API endpoint directly with curl

### 4. Database Connection Issues
- Verify RDS Proxy configuration
- Check security group allows connections from App Runner
- Ensure VPC connector is properly configured

### 5. SSE Streaming Issues
- Check browser developer tools for SSE connection errors
- Verify `NEXT_PUBLIC_API_BASE_URL` is correctly set in frontend
- Test SSE endpoint directly: `curl -N https://api-url/api/streams/test-id`
- Check CloudWatch logs for streaming service errors

### 6. Worker Integration Issues
- Verify background worker is starting in API server logs
- Check `GRAPH_TYPE` environment variable is set correctly
- Monitor job processing in database: `SELECT * FROM jobs WHERE status = 'processing';`
- Ensure OpenAI/Anthropic API keys are configured for LLM agents

## Security Considerations

### CORS Configuration
- **Production**: Restricted to AWS App Runner domains only
- **Development**: Allows localhost for local testing
- Environment-based configuration prevents security issues

### Network Security
- RDS database only accessible via RDS Proxy
- App Runner services use VPC connector for secure database access
- Security groups restrict traffic to necessary ports only

### Container Security
- Multi-stage Docker builds minimize image size
- Images scanned automatically in ECR
- Lifecycle policies prevent old image accumulation

## Cost Optimization

### App Runner Pricing
- **Reduced from 3 to 2 services**: ~33% cost reduction in compute resources
- Pay per vCPU and memory used
- Automatic scaling reduces costs during low traffic
- No idle charges when services are not processing requests

### Architecture Benefits
- **Single Server Process**: Eliminates worker service costs while maintaining functionality
- **Shared Memory**: Direct event sharing reduces memory overhead vs HTTP bridges
- **Simplified Networking**: Fewer service-to-service connections reduce data transfer costs

### RDS Proxy Benefits
- Connection pooling reduces database connection overhead
- Better resource utilization with integrated worker
- Improved application performance

## Cleanup

To tear down all resources:

```bash
cd infra/terraform
terraform destroy
```

**Warning**: This will delete all data and resources. Make sure to backup any important data first.

## Next Steps After Deployment

1. **Set up monitoring**: Configure CloudWatch alarms for service health
2. **Configure custom domains**: Add your own domain names to App Runner services  
3. **Set up CI/CD**: Use GitHub Actions to automate deployments
4. **Add SSL certificates**: Configure HTTPS with custom domains
5. **Configure backups**: Set up automated RDS snapshots

## Support

- Check CloudWatch logs for detailed error information
- Use AWS Support for infrastructure issues
- Review Terraform state for configuration debugging
- Run `./scripts/test-e2e.sh` to validate service connectivity