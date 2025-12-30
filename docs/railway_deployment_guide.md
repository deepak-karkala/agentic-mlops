# Railway Deployment Guide for Agentic MLOps Platform

This guide covers deploying the Agentic MLOps platform to Railway - a simpler alternative to AWS App Runner that's perfect for MVP demos.

## Why Railway?

✅ **Simpler than AWS** - No Terraform, no complex IAM, no VPC configuration
✅ **Cost-effective** - $5-30/month for MVP usage (vs $30-100 on AWS)
✅ **Fast deployment** - 10-15 minutes from start to finish
✅ **GitHub integration** - Automatic deployments on push
✅ **Managed Postgres** - Database included, auto-configured
✅ **Works with your architecture** - Supports long-running workflows (1-5 min), SSE streaming, background workers

## Prerequisites

1. **Railway account** - Sign up at [railway.app](https://railway.app) (free tier available)
2. **GitHub account** - For connecting your repository
3. **API keys** - OpenAI and Anthropic API keys for LLM agents
4. **(Optional) AWS credentials** - Only if using S3 for artifact storage

## Architecture on Railway

Railway will deploy **2 services**:

1. **API Service** (`api/`) - FastAPI backend with integrated worker
   - Runs on Railway-assigned port (e.g., 3456)
   - Includes background job processor
   - Connects to Railway Postgres database
   - Streams real-time events via SSE

2. **Frontend Service** (`frontend/`) - Next.js application
   - Runs on Railway-assigned port
   - Calls API service via internal URL
   - Displays chat interface and reason cards

## Step-by-Step Deployment

### Step 1: Install Railway CLI (Optional)

```bash
# macOS
brew install railway

# npm (cross-platform)
npm install -g @railway/cli

# Login to Railway
railway login
```

**Note**: You can also deploy via Railway's web dashboard without installing the CLI.

---

### Step 2: Create Railway Project

#### Option A: Using Railway CLI

```bash
# In your project directory
railway init

# Follow the prompts:
# - Project name: agentic-mlops
# - Environment: production
```

#### Option B: Using Railway Dashboard

1. Go to [railway.app/new](https://railway.app/new)
2. Click "Deploy from GitHub repo"
3. Authorize Railway to access your GitHub
4. Select your repository: `agentic-mlops`
5. Railway will automatically detect the project

---

### Step 3: Add PostgreSQL Database

Railway makes this incredibly easy:

```bash
# Using CLI
railway add --database postgres

# Or via dashboard:
# 1. Go to your project
# 2. Click "+ New"
# 3. Select "Database" → "PostgreSQL"
```

**What Railway does automatically:**
- Creates PostgreSQL 15 database
- Generates `DATABASE_URL` environment variable
- Injects URL into all services
- Handles connection pooling

**Your app will automatically use this** - no configuration needed! The database connection is handled by `libs/database.py`.

---

### Step 4: Create API Service

#### Using Railway CLI:

```bash
# Create API service
railway up --service api

# Railway will:
# 1. Detect api/Dockerfile
# 2. Build the container
# 3. Deploy to Railway's infrastructure
```

#### Using Railway Dashboard:

1. In your project, click "+ New" → "GitHub Repo"
2. Select your repository
3. Railway detects `railway.json` and `api/Dockerfile`
4. Click "Deploy"

---

### Step 5: Configure API Service Environment Variables

Set these environment variables for the **API service**:

| Variable | Value | Required | Description |
|----------|-------|----------|-------------|
| `ENVIRONMENT` | `production` | Yes | Enables production CORS settings |
| `OPENAI_API_KEY` | `sk-...` | Yes | OpenAI API key for LangGraph agents |
| `ANTHROPIC_API_KEY` | `sk-ant-...` | Yes | Anthropic API key for Claude Code generation |
| `LOG_LEVEL` | `INFO` | No | Logging verbosity (DEBUG, INFO, WARNING, ERROR) |
| `GRAPH_TYPE` | `full` | No | Enables full LangGraph with agent reasoning (default: `simple`) |
| `S3_BUCKET_NAME` | `your-bucket` | No | AWS S3 bucket for artifact storage (optional) |
| `AWS_ACCESS_KEY_ID` | `AKIA...` | No | AWS credentials (only if using S3) |
| `AWS_SECRET_ACCESS_KEY` | `...` | No | AWS credentials (only if using S3) |
| `AWS_REGION` | `us-east-1` | No | AWS region (only if using S3) |

#### Setting Variables via CLI:

```bash
# Set required variables
railway variables --set ENVIRONMENT=production
railway variables --set OPENAI_API_KEY=sk-your-key-here
railway variables --set ANTHROPIC_API_KEY=sk-ant-your-key-here

# Optional: Enable full LangGraph mode
railway variables --set GRAPH_TYPE=full
railway variables --set LOG_LEVEL=INFO

# Optional: S3 for artifact storage
railway variables --set S3_BUCKET_NAME=your-artifacts-bucket
railway variables --set AWS_ACCESS_KEY_ID=AKIA...
railway variables --set AWS_SECRET_ACCESS_KEY=...
railway variables --set AWS_REGION=us-east-1
```

#### Setting Variables via Dashboard:

1. Go to API service → "Variables" tab
2. Click "+ New Variable"
3. Add each variable from the table above
4. Click "Deploy" to apply changes

**Important**: `DATABASE_URL` is automatically injected by Railway when you add the Postgres database - you don't need to set it manually.

---

### Step 6: Create Frontend Service

The frontend needs to know the API service URL.

#### Using Railway CLI:

```bash
# In frontend/ directory
cd frontend
railway up --service frontend

# Set API URL (get this from API service first)
railway variables --set NEXT_PUBLIC_API_BASE_URL=https://your-api-service.up.railway.app
```

#### Using Railway Dashboard:

1. Click "+ New" → "GitHub Repo"
2. Select repository, set root directory to `frontend/`
3. Railway detects `frontend/Dockerfile`
4. Set environment variable:
   - `NEXT_PUBLIC_API_BASE_URL` = `https://[api-service-url].up.railway.app`

**How to get API service URL:**
```bash
# CLI
railway status --service api

# Or check Railway dashboard → API service → "Deployments" → "Domain"
```

---

### Step 7: Configure Custom Domains (Optional)

Railway provides temporary domains like `api-production-abc123.up.railway.app`. For production demos, add custom domains:

#### Via CLI:
```bash
# Add custom domain to frontend
railway domain --service frontend
# Enter: demo.yourdomain.com

# Add custom domain to API
railway domain --service api
# Enter: api.yourdomain.com
```

#### Via Dashboard:
1. Go to service → "Settings" → "Domains"
2. Click "Generate Domain" for Railway subdomain
3. Or click "Custom Domain" to add your own

**Update frontend environment:**
```bash
railway variables --set NEXT_PUBLIC_API_BASE_URL=https://api.yourdomain.com --service frontend
```

---

### Step 8: Verify Deployment

#### Check Service Status:

```bash
# View all services
railway status

# View logs
railway logs --service api
railway logs --service frontend
```

#### Test API Endpoint:

```bash
# Get API URL
API_URL=$(railway status --service api --json | jq -r '.domain')

# Health check
curl https://$API_URL/

# Expected output:
# {"message": "Agentic MLOps API"}
```

#### Test Frontend:

1. Get frontend URL from Railway dashboard
2. Open in browser: `https://your-frontend.up.railway.app`
3. Type a message: "Design an ML pipeline for customer churn prediction"
4. Watch real-time reason cards appear
5. Wait for workflow to complete (1-5 minutes)

---

### Step 9: Enable GitHub Auto-Deploy (Recommended)

Railway can automatically deploy when you push to GitHub:

#### Via Dashboard:
1. Go to service → "Settings" → "Source"
2. Enable "Trigger Deploys on Git Push"
3. Select branch: `main` or `production`
4. (Optional) Set "Watch Paths" to:
   - API service: `api/**`, `libs/**`, `api/Dockerfile`
   - Frontend service: `frontend/**`, `frontend/Dockerfile`

#### Via CLI:
```bash
# Link service to GitHub
railway service --link

# Enable auto-deploy
railway service --autodeploy
```

**Now every push to `main` automatically deploys!**

---

## Cost Breakdown

Railway pricing is straightforward:

### Free Tier (Hobby Plan)
- $5 credit/month
- Perfect for testing
- Sleeps after inactivity

### Developer Plan ($5/month)
- $5 included credit
- Pay only for usage beyond credit
- No sleep/idling

### Estimated Monthly Costs (MVP Demo Usage)

| Resource | Usage | Cost |
|----------|-------|------|
| **API Service** | ~10 hours/month active | $2-5 |
| **Frontend Service** | ~10 hours/month active | $1-3 |
| **PostgreSQL Database** | Always-on, 256MB | $1-2 |
| **Bandwidth** | ~1-5 GB | $0.10 |
| **Total** | Light demo usage | **$5-15/month** |

**For investor demos (< 10 hours/month):**
- Expected cost: **$5-10/month** (vs $30-100 on AWS)
- Can pause services between demos to save costs

### Cost Optimization Tips

1. **Use Railway's sleep feature** - Services sleep after 30 min inactivity (free tier)
2. **Delete database snapshots** - Only keep latest backup
3. **Monitor usage** - Railway dashboard shows real-time costs
4. **Pause services** - Manually pause when not demoing

---

## Environment Variables Reference

### API Service Variables

| Variable | Example | Required | Notes |
|----------|---------|----------|-------|
| `DATABASE_URL` | `postgresql://...` | Auto-set | Railway auto-injects from Postgres plugin |
| `ENVIRONMENT` | `production` | Yes | Enables production CORS |
| `OPENAI_API_KEY` | `sk-proj-...` | Yes | For LangGraph agents |
| `ANTHROPIC_API_KEY` | `sk-ant-...` | Yes | For Claude Code generation |
| `GRAPH_TYPE` | `full` | No | Use `full` for demos (shows reasoning), `simple` for basic |
| `LOG_LEVEL` | `INFO` | No | `DEBUG` for troubleshooting |
| `S3_BUCKET_NAME` | `artifacts-bucket` | No | Optional artifact storage |
| `FRONTEND_URL` | `https://...` | No | For CORS (Railway auto-detects) |
| `RAILWAY_ENVIRONMENT` | `production` | Auto-set | Railway sets automatically |

### Frontend Service Variables

| Variable | Example | Required | Notes |
|----------|---------|----------|-------|
| `NEXT_PUBLIC_API_BASE_URL` | `https://api-production-abc.up.railway.app` | Yes | API service URL |
| `NODE_ENV` | `production` | Auto-set | Railway sets automatically |

---

## Railway vs AWS Comparison

| Feature | Railway | AWS App Runner |
|---------|---------|----------------|
| **Setup Time** | 10-15 minutes | 1-2 hours |
| **Infrastructure Code** | None (UI/CLI) | Terraform required |
| **Database Setup** | 1 click | RDS + RDS Proxy + VPC |
| **Monthly Cost (MVP)** | $5-15 | $30-100 |
| **Long Workflows (1-5min)** | ✅ Supported | ✅ Supported |
| **SSE Streaming** | ✅ Full support | ✅ Full support |
| **Auto-scaling** | ✅ Automatic | ✅ Automatic |
| **GitHub Integration** | ✅ Built-in | ⚠️ Manual setup |
| **Custom Domains** | ✅ Free SSL | ✅ Free SSL |
| **Logs** | ✅ Real-time | ✅ CloudWatch |
| **Ease of Use** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

---

## Troubleshooting

### Issue: Build Fails with "Dockerfile not found"

**Solution**: Ensure `railway.json` points to correct Dockerfile path:

```json
{
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "api/Dockerfile"
  }
}
```

For frontend, create separate `frontend/railway.json`:

```json
{
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile"
  }
}
```

---

### Issue: API Returns CORS Error

**Symptoms**: Frontend can't connect to API, browser shows CORS error

**Solution**: Set `FRONTEND_URL` environment variable in API service:

```bash
railway variables --set FRONTEND_URL=https://your-frontend.up.railway.app --service api
```

Verify CORS configuration in logs:
```bash
railway logs --service api | grep CORS
```

---

### Issue: Database Connection Error

**Symptoms**: API crashes with "connection refused" or "database does not exist"

**Solution**:

1. Verify Postgres plugin is added:
   ```bash
   railway status
   # Should show "postgres" service
   ```

2. Check `DATABASE_URL` is injected:
   ```bash
   railway variables --service api | grep DATABASE_URL
   ```

3. Run database migrations (if needed):
   ```bash
   # SSH into running service
   railway run --service api bash

   # Inside container:
   uv run alembic upgrade head
   ```

---

### Issue: Frontend Shows "API Unreachable"

**Solution**:

1. Verify API is running:
   ```bash
   railway status --service api
   ```

2. Test API directly:
   ```bash
   curl https://your-api-url.up.railway.app/
   ```

3. Check frontend environment variable:
   ```bash
   railway variables --service frontend | grep NEXT_PUBLIC_API_BASE_URL
   ```

4. Ensure URL starts with `https://` (not `http://`)

---

### Issue: SSE Streaming Not Working

**Symptoms**: Reason cards don't appear in real-time

**Solution**:

1. Check browser Network tab for SSE connection:
   - Should see `api/streams/{id}` with type `eventsource`
   - Status should be `200` (pending)

2. Test SSE endpoint directly:
   ```bash
   curl -N https://your-api-url.up.railway.app/api/streams/test-123
   ```

3. Verify API logs show streaming events:
   ```bash
   railway logs --service api | grep -i stream
   ```

4. Check CORS allows SSE (should be automatic with Railway domains)

---

### Issue: Slow Cold Starts

**Symptoms**: First request after inactivity takes 10-30 seconds

**Solution**:

Railway services sleep after inactivity. Options:

1. **Upgrade to paid plan** - No sleep on Developer plan
2. **Keep-alive ping** - Use external monitor (UptimeRobot, etc.)
3. **Accept cold starts** - Normal for free tier, acceptable for demos

---

### Issue: API Key Errors (OpenAI/Anthropic)

**Symptoms**: Workflow fails with "Invalid API key" or "Authentication error"

**Solution**:

1. Verify keys are set:
   ```bash
   railway variables --service api | grep API_KEY
   ```

2. Check key format:
   - OpenAI: `sk-proj-...` (new format) or `sk-...`
   - Anthropic: `sk-ant-...`

3. Test keys locally first:
   ```bash
   export OPENAI_API_KEY=sk-...
   uv run python -c "from openai import OpenAI; OpenAI().models.list()"
   ```

4. Redeploy after setting:
   ```bash
   railway up --service api
   ```

---

## Advanced Configuration

### Running Database Migrations

Railway doesn't automatically run migrations. Options:

#### Option 1: Manual SSH

```bash
# SSH into running API service
railway run --service api bash

# Run migrations
uv run alembic upgrade head
```

#### Option 2: Add to Dockerfile

Edit `api/Dockerfile` to run migrations on startup:

```dockerfile
# Add before CMD
RUN echo '#!/bin/sh\nuv run alembic upgrade head\nexec "$@"' > /entrypoint.sh && chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["uv", "run", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "${PORT:-8000}"]
```

**Trade-off**: Slower startup, but automatic migrations.

---

### Using Railway Volumes for Artifact Storage

Alternative to AWS S3 for storing generated MLOps repositories:

1. **Add volume to API service**:
   ```bash
   railway volume add --service api --mount /app/artifacts
   ```

2. **Update code** to use local storage:
   Edit `libs/codegen_service.py` to save to `/app/artifacts` instead of S3.

3. **Download artifacts**:
   ```bash
   railway run --service api bash
   # Inside: tar czf /tmp/artifacts.tar.gz /app/artifacts
   # Download via Railway CLI
   ```

**Trade-off**: Simpler than S3, but limited to 1GB free tier (vs S3's pay-per-use).

---

### Monitoring and Alerts

Railway provides basic monitoring:

```bash
# View metrics
railway metrics --service api

# Watch logs in real-time
railway logs --service api --follow
```

For production, integrate with external monitoring:

1. **Sentry** - Error tracking
   ```bash
   railway variables --set SENTRY_DSN=https://...
   ```

2. **LogTail** - Log aggregation
   ```bash
   railway integrations add logtail
   ```

3. **UptimeRobot** - Health checks
   - Set up external monitor for `https://your-api.up.railway.app/`

---

## Cleanup / Pausing Services

### Pause Services (Keep Data)

```bash
# Pause API service
railway service pause --service api

# Pause frontend
railway service pause --service frontend

# Database keeps running (small cost)
```

### Delete Project (Remove Everything)

```bash
# Delete entire project
railway project delete

# Or via dashboard: Project Settings → Delete Project
```

**Warning**: Deleting project removes all data, including database. Export data first if needed.

### Export Database Before Deletion

```bash
# Create backup
railway run --service postgres pg_dump > backup.sql

# Or use Railway's backup feature
railway backup create --service postgres
```

---

## Success Criteria

Deployment is successful when:

1. ✅ API service shows "Deployed" in Railway dashboard
2. ✅ Frontend service shows "Deployed" in Railway dashboard
3. ✅ API health check returns `{"message": "Agentic MLOps API"}`
4. ✅ Frontend loads in browser
5. ✅ Test workflow completes end-to-end (1-5 minutes)
6. ✅ Real-time reason cards appear during processing
7. ✅ No CORS errors in browser console
8. ✅ Database connection working (check API logs)

---

## Next Steps After Deployment

1. **Test thoroughly** - Run multiple workflows to verify stability
2. **Set up monitoring** - Add Sentry for error tracking
3. **Configure custom domain** - Professional URL for demos
4. **Enable GitHub auto-deploy** - Streamline future updates
5. **Document environment variables** - Keep secure backup of API keys
6. **Create demo script** - Prepare talking points for investor demos
7. **Monitor costs** - Check Railway dashboard regularly

---

## Support Resources

- **Railway Documentation**: [docs.railway.app](https://docs.railway.app)
- **Railway Discord**: Community support and help
- **Railway Status**: [status.railway.app](https://status.railway.app)
- **Project Issues**: Check API/Frontend logs in Railway dashboard

---

## Comparison: Railway vs AWS App Runner Decision Matrix

| Criteria | Railway | AWS App Runner |
|----------|---------|----------------|
| **Best for** | MVP demos, rapid iteration | Production at scale |
| **Setup Complexity** | ⭐ Very simple | ⭐⭐⭐ Complex |
| **Time to Deploy** | 10-15 minutes | 1-2 hours |
| **Monthly Cost (demo)** | $5-15 | $30-100 |
| **Infrastructure Code** | None | Terraform required |
| **Database Setup** | 1-click Postgres | RDS + Proxy + VPC |
| **Scaling** | Automatic | Automatic |
| **GitHub Integration** | Built-in | Manual setup |
| **Supports Long Workflows** | ✅ Yes | ✅ Yes |
| **SSE Streaming** | ✅ Yes | ✅ Yes |
| **Custom Domains** | ✅ Free SSL | ✅ Free SSL |
| **Recommended for** | MVP, demos, small teams | Enterprise, compliance needs |

---

## Conclusion

Railway is the **perfect choice for MVP demos** because:

✅ **10x simpler** than AWS - No Terraform, no VPC, no IAM complexity
✅ **3x cheaper** for demo usage - $5-15/month vs $30-100
✅ **Supports your architecture** - Long workflows, SSE streaming, background workers all work perfectly
✅ **GitHub integration** - Auto-deploy on push
✅ **Production-ready** - Can scale when you need it

Your application is already Railway-compatible with the recent code changes. Just follow the steps above and you'll be demo-ready in 15 minutes!

**Total deployment time: 10-15 minutes**
**Estimated monthly cost: $5-15**
**Perfect for investor and recruiter demos** ✨
