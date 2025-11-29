# Copilot Instructions for Open WebUI GCP Deployment

## What This Repository Does

This repository deploys **Open WebUI** and **LiteLLM Proxy** to Google Cloud Platform (GCP) using Cloud Run. 

**Open WebUI** is a self-hosted AI chat interface that provides:
- Multi-model conversations (OpenAI, Anthropic, etc.)
- RAG (Retrieval Augmented Generation) with document upload
- User management and authentication
- Python function tools and plugins
- Chat history and persistence

**LiteLLM Proxy** provides unified API access to multiple LLM providers (OpenAI, Anthropic) with request logging and load balancing.

**Important**: We do NOT build the Open WebUI application locally. We use the official pre-built container images from `ghcr.io/open-webui/open-webui:main` and `ghcr.io/berriai/litellm:main-latest`.

---

## GCP Project Configuration

- **Project ID**: `lb-openwebui`
- **Project Number**: `976415410962`
- **Region**: `us-central1`
- **Services**: 
  - Cloud Run: `open-webui`, `litellm-proxy`
  - Cloud SQL: `open-webui-db` (PostgreSQL)
  - Artifact Registry: `openwebui` repository

---

## Key Files (All Dennis's Custom Work)

```
.github/workflows/
├── deploy-gcp.yml          # Deploys Open WebUI to Cloud Run
└── deploy-litellm-gcp.yml  # Deploys LiteLLM proxy to Cloud Run
setup-github-actions.sh     # One-time GCP setup for GitHub Actions
setup-postgres.sh           # One-time PostgreSQL database setup
litellm_config.yaml         # LiteLLM model routing config (OpenAI + Anthropic)
GCP_DEPLOYMENT_GUIDE.md     # Human-readable setup guide
```

**Never modify** upstream Open WebUI files (src/, backend/, etc.) - those are maintained by the upstream project

---

## Deployment Workflows

### 1. deploy-gcp.yml (Open WebUI)

**Trigger**: Push to `main` branch or manual workflow dispatch

**What it does**:
1. Pulls official Open WebUI image: `ghcr.io/open-webui/open-webui:main`
2. Tags and pushes to Artifact Registry: `us-docker.pkg.dev/lb-openwebui/openwebui/open-webui:latest`
3. Checks if LiteLLM proxy service exists and gets its URL
4. Deploys to Cloud Run service `open-webui` with these settings:
   - **Memory**: 1Gi
   - **CPU**: 1
   - **Min instances**: 0 (scales to zero)
   - **Max instances**: 2
   - **Public access**: Enabled (`--allow-unauthenticated`)
   - **Cloud SQL**: Connected to `lb-openwebui:us-central1:open-webui-db`

**Environment Variables**:
- `ENV=prod`
- `WEBUI_NAME="LightBringer AI"`
- `ENABLE_OLLAMA_API=false` (we use LiteLLM proxy instead)
- `OPENAI_API_BASE_URL=<LiteLLM proxy URL or OpenAI direct>`

**Secrets Used**:
- `DATABASE_URL`: PostgreSQL connection string (format: `postgresql://USER:PASS@/DB?host=/cloudsql/CONNECTION_NAME`)
- `OPENAI_API_KEY`: Set to `lb-litellm-master-key` (the LiteLLM master key)
- `WEBUI_SECRET_KEY`: Session encryption key

### 2. deploy-litellm-gcp.yml (LiteLLM Proxy)

**Trigger**: Push to `main` that modifies `litellm_config.yaml` or workflow file, or manual dispatch

**What it does**:
1. Pulls official LiteLLM image: `ghcr.io/berriai/litellm:main-latest`
2. Tags and pushes to Artifact Registry: `us-docker.pkg.dev/lb-openwebui/openwebui/litellm:latest`
3. Deploys to Cloud Run service `litellm-proxy` with these settings:
   - **Memory**: 512Mi
   - **CPU**: 1
   - **Min instances**: 0
   - **Max instances**: 2
   - **Public access**: Disabled (`--no-allow-unauthenticated`)
   - **Ingress**: Internal only (`--ingress internal-and-cloud-load-balancing`)
   - **Cloud SQL**: Connected to `lb-openwebui:us-central1:open-webui-db`
4. Grants Open WebUI service account permission to invoke LiteLLM
5. Uploads `litellm_config.yaml` to GCS bucket `lb-openwebui-litellm-config`

**Environment Variables**:
- `ENV=prod`
- `CONFIG_URL=gs://lb-openwebui-litellm-config/config.yaml`

**Secrets Used**:
- `LITELLM_MASTER_KEY`: API key for accessing LiteLLM proxy
- `DATABASE_URL`: PostgreSQL for request logging (separate from Open WebUI database)
- `OPENAI_API_KEY`: For OpenAI model access
- `ANTHROPIC_API_KEY`: For Claude model access

**Command Override**: 
```bash
litellm --config /app/config.yaml --port 8080 --detailed_debug
```

---

## Setup Scripts

### setup-github-actions.sh

**Purpose**: One-time setup to enable GitHub Actions to deploy to GCP

**What it does**:
1. Creates service account: `lb-openwebui-github-actions@lb-openwebui.iam.gserviceaccount.com`
2. Grants IAM roles:
   - `roles/run.admin` - Deploy Cloud Run services
   - `roles/storage.admin` - Manage GCS buckets
   - `roles/artifactregistry.writer` - Push Docker images
   - `roles/artifactregistry.repoAdmin` - Manage repositories
   - `roles/iam.serviceAccountUser` - Act as service accounts
   - `roles/secretmanager.secretAccessor` - Read secrets
3. Enables required GCP APIs:
   - `run.googleapis.com` (Cloud Run)
   - `artifactregistry.googleapis.com` (Docker registry)
   - `cloudbuild.googleapis.com` (Build triggers)
   - `secretmanager.googleapis.com` (Secrets)
4. Creates Artifact Registry repository: `openwebui` (Docker format, `us` region)
5. Generates service account key: `lb-openwebui-github-actions-key.json`

**Usage**:
```bash
bash setup-github-actions.sh
```

**After running**: 
1. Add `LB_OPENWEBUI_GCP_SA_KEY` to GitHub secrets (contents of key file)
2. Add `LB_OPENWEBUI_GCP_PROJECT_ID` to GitHub secrets (value: `lb-openwebui`)
3. Delete local key file: `rm lb-openwebui-github-actions-key.json`

### setup-postgres.sh

**Purpose**: One-time setup for PostgreSQL database on Cloud SQL

**Prerequisites**: Cloud SQL instance `open-webui-db` must exist

**What it does**:
1. Sets password for `postgres` superuser
2. Creates database user: `openwebui` with random password
3. Creates database: `openwebui`
4. Gets Cloud SQL connection name
5. Creates `DATABASE_URL` secret in Secret Manager:
   - Format: `postgresql://openwebui:PASSWORD@/openwebui?host=/cloudsql/lb-openwebui:us-central1:open-webui-db`
6. Grants Cloud Run default service account access to the secret

**Usage**:
```bash
bash setup-postgres.sh
```

**IMPORTANT**: Save the database password displayed at the end - you'll need it for direct database access if troubleshooting.

---

## LiteLLM Configuration (litellm_config.yaml)

This file defines which LLM models are available and how to route them:

```yaml
model_list:
  - model_name: gpt-4o
    litellm_params:
      model: openai/gpt-4o
      api_key: os.environ/OPENAI_API_KEY
  
  - model_name: claude-3-5-sonnet
    litellm_params:
      model: anthropic/claude-3-5-sonnet-20241022
      api_key: os.environ/ANTHROPIC_API_KEY

general_settings:
  master_key: os.environ/LITELLM_MASTER_KEY
  database_url: os.environ/DATABASE_URL
```

**To add a new model**:
1. Edit `litellm_config.yaml` and add new entry under `model_list`
2. Create corresponding GCP secret for API key (if needed)
3. Update `deploy-litellm-gcp.yml` to mount the new secret
4. Commit and push - deployment is automatic

---

## Required GCP Secrets

All secrets are in Secret Manager (`gcloud secrets list --project=lb-openwebui`):

**For Open WebUI** (`deploy-gcp.yml`):
- `lb-openwebui-database-url`: PostgreSQL connection string
- `lb-litellm-master-key`: LiteLLM API key (used as OPENAI_API_KEY)
- `lb-openwebui-secret-key`: Session encryption key (generate with `openssl rand -base64 32`)

**For LiteLLM Proxy** (`deploy-litellm-gcp.yml`):
- `lb-litellm-master-key`: Master API key for LiteLLM authentication
- `lb-litellm-database-url`: PostgreSQL for LiteLLM request logging
- `lb-openwebui-openai-api-key`: Your actual OpenAI API key
- `lb-litellm-anthropic-api-key`: Your actual Anthropic API key

**Creating a new secret**:
```bash
echo -n 'secret-value' | gcloud secrets create SECRET_NAME \
  --data-file=- \
  --project=lb-openwebui

# Grant Cloud Run access
gcloud secrets add-iam-policy-binding SECRET_NAME \
  --member="serviceAccount:976415410962-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project=lb-openwebui
```

---

## Common Tasks with gcloud CLI

### View deployed services
```bash
gcloud run services list --project=lb-openwebui --region=us-central1
```

### Get service URL
```bash
gcloud run services describe open-webui \
  --project=lb-openwebui \
  --region=us-central1 \
  --format='value(status.url)'
```

### View service logs
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=open-webui" \
  --project=lb-openwebui \
  --limit=50 \
  --format=json
```

### Manually trigger deployment
```bash
# Via GitHub UI: Actions tab → Select workflow → Run workflow
# Or push to main branch
```

### Update environment variable
```bash
gcloud run services update open-webui \
  --project=lb-openwebui \
  --region=us-central1 \
  --set-env-vars NEW_VAR=value
```

### View Cloud SQL instances
```bash
gcloud sql instances list --project=lb-openwebui
```

### Connect to Cloud SQL (requires Cloud SQL Proxy)
```bash
gcloud sql connect open-webui-db --user=openwebui --project=lb-openwebui
```

---

## Troubleshooting

### Open WebUI deployment fails
1. Check GitHub Actions logs in repository Actions tab
2. Verify all secrets exist: `gcloud secrets list --project=lb-openwebui`
3. Check Cloud Run logs: `gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=open-webui" --limit=50`
4. Verify Cloud SQL connection: Service should have `--add-cloudsql-instances=lb-openwebui:us-central1:open-webui-db`

### LiteLLM proxy not accessible from Open WebUI
1. Verify LiteLLM service deployed: `gcloud run services describe litellm-proxy --region=us-central1`
2. Check IAM permissions: Open WebUI service account needs `roles/run.invoker` on LiteLLM service
3. Verify ingress setting: `--ingress internal-and-cloud-load-balancing` allows internal GCP access
4. Check LiteLLM logs for errors

### Database connection errors
1. Verify `DATABASE_URL` secret format: `postgresql://USER:PASS@/DB?host=/cloudsql/CONNECTION_NAME`
2. Check Cloud SQL instance status: `gcloud sql instances describe open-webui-db`
3. Verify Cloud SQL connection in Cloud Run service config
4. Check database exists: `gcloud sql databases list --instance=open-webui-db`

### LiteLLM model not available
1. Verify API key secret exists and is mounted correctly
2. Check `litellm_config.yaml` syntax
3. Verify config uploaded to GCS: `gsutil cat gs://lb-openwebui-litellm-config/config.yaml`
4. Check LiteLLM logs: `gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=litellm-proxy" --limit=50`

### GitHub Actions authentication fails
1. Verify `LB_OPENWEBUI_GCP_SA_KEY` secret in GitHub settings
2. Verify service account has required roles: `gcloud projects get-iam-policy lb-openwebui`
3. Check service account is enabled: `gcloud iam service-accounts describe lb-openwebui-github-actions@lb-openwebui.iam.gserviceaccount.com`

---

## Instructions for Coding Agents

**TRUST THESE INSTRUCTIONS**: This document is comprehensive and validated. Only search for additional information if these instructions are incorrect or incomplete.

**What you can help with**:
1. **Modifying deployment configurations**: Edit workflow YAML files to change Cloud Run settings
2. **Adding LLM providers**: Update `litellm_config.yaml` and deployment workflow to add new models
3. **Creating/updating GCP secrets**: Use `gcloud secrets` commands
4. **Troubleshooting deployments**: Check logs, verify configurations
5. **Updating setup scripts**: Modify `setup-github-actions.sh` or `setup-postgres.sh`

**What NOT to do**:
1. **DO NOT** modify upstream Open WebUI source code (src/, backend/, etc.)
2. **DO NOT** attempt to build Open WebUI locally - we use pre-built images
3. **DO NOT** change the Docker image sources (`ghcr.io/open-webui/open-webui:main` and `ghcr.io/berriai/litellm:main-latest`)

**Before making changes**:
1. Understand which workflow file to modify (Open WebUI vs LiteLLM)
2. Check if secrets need to be created/updated in GCP Secret Manager
3. Consider if changes require GitHub secrets to be updated
4. Test workflow changes won't break deployments (validate YAML syntax)

**Deployment happens automatically**: Any push to `main` branch triggers deployment. LiteLLM only redeploys if `litellm_config.yaml` or its workflow changes.
