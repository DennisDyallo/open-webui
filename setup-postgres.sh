#!/bin/bash

# Setup PostgreSQL for Open WebUI on GCP Cloud Run
# Run this after the Cloud SQL instance is created

set -e

PROJECT_ID="lb-openwebui"
INSTANCE_NAME="open-webui-db"
DB_NAME="openwebui"
DB_USER="openwebui"
DB_PASSWORD=$(openssl rand -base64 32)

echo "🔐 Setting postgres user password..."
gcloud sql users set-password postgres \
  --instance=${INSTANCE_NAME} \
  --password=$(openssl rand -base64 24) \
  --project=${PROJECT_ID}

echo "👤 Creating database user: ${DB_USER}..."
gcloud sql users create ${DB_USER} \
  --instance=${INSTANCE_NAME} \
  --password=${DB_PASSWORD} \
  --project=${PROJECT_ID}

echo "🗄️ Creating database: ${DB_NAME}..."
gcloud sql databases create ${DB_NAME} \
  --instance=${INSTANCE_NAME} \
  --project=${PROJECT_ID}

# Get connection name
CONNECTION_NAME=$(gcloud sql instances describe ${INSTANCE_NAME} \
  --project=${PROJECT_ID} \
  --format='value(connectionName)')

# Create DATABASE_URL
DATABASE_URL="postgresql://${DB_USER}:${DB_PASSWORD}@/${DB_NAME}?host=/cloudsql/${CONNECTION_NAME}"

echo "🔑 Creating DATABASE_URL secret..."
echo -n "${DATABASE_URL}" | gcloud secrets create lb-openwebui-database-url \
  --data-file=- \
  --project=${PROJECT_ID}

# Grant Cloud Run access to the secret
PROJECT_NUMBER="976415410962"
gcloud secrets add-iam-policy-binding lb-openwebui-database-url \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project=${PROJECT_ID}

echo ""
echo "✅ PostgreSQL setup complete!"
echo ""
echo "📋 Configuration:"
echo "  Instance: ${INSTANCE_NAME}"
echo "  Database: ${DB_NAME}"
echo "  User: ${DB_USER}"
echo "  Connection: ${CONNECTION_NAME}"
echo ""
echo "⚠️  IMPORTANT: Save this password securely:"
echo "  DB Password: ${DB_PASSWORD}"
echo ""
echo "🚀 Next step: Update the GitHub Actions workflow to:"
echo "  1. Add --add-cloudsql-instances=${CONNECTION_NAME}"
echo "  2. Add --set-secrets=DATABASE_URL=lb-openwebui-database-url:latest"
