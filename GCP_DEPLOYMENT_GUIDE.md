# 🚀 Open WebUI - GCP Cloud Run Deployment

**Project:** lb-openwebui  
**Project ID:** `lb-openwebui`  
**Project Number:** `976415410962`  
**Region:** `us-central1`

---

## ⚡ Quick Start

### 1. Run Setup Script

```bash
cd ~/Code/lb-openwebui
./setup-github-actions.sh
```

This will:
- ✅ Create service account `lb-openwebui-github-actions`
- ✅ Grant all required IAM permissions
- ✅ Enable GCP APIs
- ✅ Create Artifact Registry repository
- ✅ Generate service account key

### 2. Create GCP Secrets

```bash
# OpenAI API Key (required for AI functionality)
echo -n 'sk-your-openai-api-key-here' | gcloud secrets create lb-openwebui-openai-api-key \
  --data-file=- \
  --project=lb-openwebui

# WebUI Secret Key (for session management)
echo -n $(openssl rand -base64 32) | gcloud secrets create lb-openwebui-secret-key \
  --data-file=- \
  --project=lb-openwebui

# Grant Cloud Run access to secrets
PROJECT_NUMBER="976415410962"
for SECRET in lb-openwebui-openai-api-key lb-openwebui-secret-key; do
  gcloud secrets add-iam-policy-binding ${SECRET} \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor" \
    --project=lb-openwebui
done
```

### 3. Add GitHub Secrets

Go to: https://github.com/YOUR_USERNAME/lb-openwebui/settings/secrets/actions

Add these two secrets:

**LB_OPENWEBUI_GCP_SA_KEY**
```bash
cat lb-openwebui-github-actions-key.json
```
Copy the entire JSON output

**LB_OPENWEBUI_GCP_PROJECT_ID**
```
lb-openwebui
```

### 4. Delete Local Key

```bash
rm lb-openwebui-github-actions-key.json
```

### 5. Push to Deploy

```bash
git add .
git commit -m "Add GCP Cloud Run deployment"
git push origin main
```

---

## 🔧 Configuration

Open WebUI will be deployed with:

- **Min Instances:** 0 (scales to zero when not in use)
- **Max Instances:** 2
- **Memory:** 1GB
- **CPU:** 1
- **Authentication:** Public (allow-unauthenticated)
- **OpenAI Integration:** Enabled
- **Ollama:** Disabled (cloud deployment, using OpenAI instead)

### Environment Variables Set:
- `ENV=prod`
- `WEBUI_NAME="LightBringer AI"`
- `ENABLE_OLLAMA_API=false`
- `OPENAI_API_BASE_URL=https://api.openai.com/v1`

---

## 💰 Estimated Costs

- **Cloud Run:** ~$0-5/month (scales to zero, pay per use)
- **Artifact Registry:** ~$0.10/GB/month
- **Secret Manager:** ~$0.06/month

**Total:** ~$1-6/month (very low cost since it scales to zero)

---

## 🔍 Monitoring

**Deployment:**
- https://github.com/YOUR_USERNAME/lb-openwebui/actions

**Cloud Run Console:**
- https://console.cloud.google.com/run?project=lb-openwebui

**Logs:**
```bash
gcloud logs tail \
  --project=lb-openwebui \
  --filter='resource.type=cloud_run_revision AND resource.labels.service_name=open-webui'
```

**Get Service URL:**
```bash
gcloud run services describe open-webui \
  --project=lb-openwebui \
  --region=us-central1 \
  --format='value(status.url)'
```

---

## 🎯 Key Differences from Hyperbot

| Feature | Hyperbot | Open WebUI |
|---------|----------|------------|
| Min Instances | 1 (always on) | 0 (scales to zero) |
| Cost | ~$10-15/month | ~$1-6/month |
| Public Access | No | Yes |
| Purpose | Trading bot | AI chat interface |
| Secrets | 4 | 2 |

---

## 📚 Additional Resources

- [Open WebUI Documentation](https://docs.openwebui.com/)
- [Open WebUI GitHub](https://github.com/open-webui/open-webui)
- [GCP Cloud Run Docs](https://cloud.google.com/run/docs)

---

**Questions?** Check the [Open WebUI Discord](https://discord.gg/5rJgQTnV4s)
