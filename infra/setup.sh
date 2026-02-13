#!/usr/bin/env bash
# ============================================================================
# EzMsg — One-time GCP project setup
# ============================================================================
# Enables APIs, creates Artifact Registry, Cloud SQL, and Secret Manager
# resources. Safe to re-run (idempotent — checks before creating).
#
# Prerequisites:
#   - gcloud CLI installed and authenticated (`gcloud auth login`)
#   - A GCP project already created with billing enabled
#
# Usage:
#   chmod +x infra/setup.sh
#   ./infra/setup.sh
# ============================================================================
set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration — edit these values for your environment
# ---------------------------------------------------------------------------
GCP_PROJECT="${GCP_PROJECT:-ezmsg-platform}"
REGION="${REGION:-us-central1}"
ZONE="${ZONE:-us-central1-a}"

# Artifact Registry
AR_REPO="ezmsg"
AR_FORMAT="docker"

# Cloud SQL
SQL_INSTANCE="ezmsg-db"
SQL_TIER="db-f1-micro"           # ~$7/month — shared vCPU, 256 MB RAM
SQL_VERSION="POSTGRES_16"
SQL_DB_NAME="ezmsg"

# Secrets to create in Secret Manager (empty placeholder values)
SECRETS=(
  JWT_SECRET
  DATABASE_URL
  REDIS_URL
  PROTOCOL_API_KEY
  TWILIO_ACCOUNT_SID
  TWILIO_AUTH_TOKEN
  TWILIO_PHONE_NUMBER
  FIREBASE_CREDENTIALS_JSON
  ADMIN_EMAIL
  ADMIN_PASSWORD
  SENTRY_DSN
  ENCRYPTION_KEY
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
info()  { printf "\033[1;34m[INFO]\033[0m  %s\n" "$*"; }
ok()    { printf "\033[1;32m[OK]\033[0m    %s\n" "$*"; }
warn()  { printf "\033[1;33m[WARN]\033[0m  %s\n" "$*"; }
error() { printf "\033[1;31m[ERROR]\033[0m %s\n" "$*"; exit 1; }

# ---------------------------------------------------------------------------
# Pre-flight
# ---------------------------------------------------------------------------
info "Setting active project to ${GCP_PROJECT}"
gcloud config set project "${GCP_PROJECT}" --quiet

info "Setting default region to ${REGION}"
gcloud config set compute/region "${REGION}" --quiet
gcloud config set run/region "${REGION}" --quiet

# ---------------------------------------------------------------------------
# 1. Enable required APIs
# ---------------------------------------------------------------------------
APIS=(
  run.googleapis.com
  sqladmin.googleapis.com
  cloudbuild.googleapis.com
  artifactregistry.googleapis.com
  secretmanager.googleapis.com
)

info "Enabling GCP APIs..."
for api in "${APIS[@]}"; do
  if gcloud services list --enabled --filter="name:${api}" --format="value(name)" 2>/dev/null | grep -q "${api}"; then
    ok "API already enabled: ${api}"
  else
    info "Enabling ${api}..."
    gcloud services enable "${api}" --quiet
    ok "Enabled ${api}"
  fi
done

# ---------------------------------------------------------------------------
# 2. Artifact Registry repository
# ---------------------------------------------------------------------------
info "Checking Artifact Registry repo '${AR_REPO}'..."
if gcloud artifacts repositories describe "${AR_REPO}" \
     --location="${REGION}" --format="value(name)" 2>/dev/null; then
  ok "Artifact Registry repo '${AR_REPO}' already exists"
else
  info "Creating Artifact Registry repo '${AR_REPO}'..."
  gcloud artifacts repositories create "${AR_REPO}" \
    --repository-format="${AR_FORMAT}" \
    --location="${REGION}" \
    --description="EzMsg Docker images" \
    --quiet
  ok "Created Artifact Registry repo '${AR_REPO}'"
fi

# ---------------------------------------------------------------------------
# 3. Cloud SQL PostgreSQL instance
# ---------------------------------------------------------------------------
info "Checking Cloud SQL instance '${SQL_INSTANCE}'..."
if gcloud sql instances describe "${SQL_INSTANCE}" --format="value(name)" 2>/dev/null; then
  ok "Cloud SQL instance '${SQL_INSTANCE}' already exists"
else
  info "Creating Cloud SQL instance '${SQL_INSTANCE}' (this takes 3-5 minutes)..."
  gcloud sql instances create "${SQL_INSTANCE}" \
    --database-version="${SQL_VERSION}" \
    --tier="${SQL_TIER}" \
    --region="${REGION}" \
    --storage-type=HDD \
    --storage-size=10GB \
    --no-assign-ip \
    --network=default \
    --quiet
  ok "Created Cloud SQL instance '${SQL_INSTANCE}'"

  info "Setting postgres user password..."
  POSTGRES_PW=$(openssl rand -base64 24)
  gcloud sql users set-password postgres \
    --instance="${SQL_INSTANCE}" \
    --password="${POSTGRES_PW}" \
    --quiet
  warn "Postgres password: ${POSTGRES_PW}"
  warn "Save this password — it will not be shown again."
fi

# ---------------------------------------------------------------------------
# 4. Cloud SQL database
# ---------------------------------------------------------------------------
info "Checking database '${SQL_DB_NAME}' on instance '${SQL_INSTANCE}'..."
if gcloud sql databases describe "${SQL_DB_NAME}" \
     --instance="${SQL_INSTANCE}" --format="value(name)" 2>/dev/null; then
  ok "Database '${SQL_DB_NAME}' already exists"
else
  info "Creating database '${SQL_DB_NAME}'..."
  gcloud sql databases create "${SQL_DB_NAME}" \
    --instance="${SQL_INSTANCE}" \
    --charset=UTF8 \
    --collation=en_US.UTF8 \
    --quiet
  ok "Created database '${SQL_DB_NAME}'"
fi

# ---------------------------------------------------------------------------
# 5. Secret Manager secrets
# ---------------------------------------------------------------------------
info "Creating Secret Manager secrets..."
for secret_name in "${SECRETS[@]}"; do
  if gcloud secrets describe "${secret_name}" --format="value(name)" 2>/dev/null; then
    ok "Secret '${secret_name}' already exists"
  else
    info "Creating secret '${secret_name}'..."
    # Create the secret with an empty initial version.
    # Populate real values afterwards:
    #   echo -n "my-value" | gcloud secrets versions add SECRET_NAME --data-file=-
    printf "PLACEHOLDER" | gcloud secrets create "${secret_name}" \
      --data-file=- \
      --replication-policy="automatic" \
      --quiet
    ok "Created secret '${secret_name}'"
  fi
done

# ---------------------------------------------------------------------------
# 6. Grant Cloud Run service account access to secrets
# ---------------------------------------------------------------------------
PROJECT_NUMBER=$(gcloud projects describe "${GCP_PROJECT}" --format="value(projectNumber)")
CR_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

info "Granting Secret Manager access to Cloud Run SA (${CR_SA})..."
for secret_name in "${SECRETS[@]}"; do
  gcloud secrets add-iam-policy-binding "${secret_name}" \
    --member="serviceAccount:${CR_SA}" \
    --role="roles/secretmanager.secretAccessor" \
    --quiet >/dev/null 2>&1
done
ok "Secret Manager IAM bindings configured"

# ---------------------------------------------------------------------------
# 7. Grant Cloud Build access to deploy to Cloud Run
# ---------------------------------------------------------------------------
CB_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"

info "Granting Cloud Build SA (${CB_SA}) Cloud Run Admin role..."
gcloud projects add-iam-policy-binding "${GCP_PROJECT}" \
  --member="serviceAccount:${CB_SA}" \
  --role="roles/run.admin" \
  --quiet >/dev/null 2>&1

gcloud projects add-iam-policy-binding "${GCP_PROJECT}" \
  --member="serviceAccount:${CB_SA}" \
  --role="roles/iam.serviceAccountUser" \
  --quiet >/dev/null 2>&1
ok "Cloud Build IAM bindings configured"

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo ""
info "=============================================="
info "  GCP setup complete for project: ${GCP_PROJECT}"
info "=============================================="
echo ""
info "Next steps:"
info "  1. Populate secrets with real values:"
info "     echo -n 'real-value' | gcloud secrets versions add SECRET_NAME --data-file=-"
info ""
info "  2. Build the DATABASE_URL and store it as a secret:"
info "     Format: postgresql+asyncpg://postgres:PASSWORD@/ezmsg?host=/cloudsql/PROJECT:REGION:${SQL_INSTANCE}"
info ""
info "  3. Set up Cloud Build trigger:"
info "     gcloud builds triggers create github \\"
info "       --repo-name=ezmsg --repo-owner=YOUR_ORG \\"
info "       --branch-pattern='^main$' \\"
info "       --build-config=infra/cloudbuild.yaml"
info ""
info "  4. Deploy services:"
info "     gcloud builds submit --config=infra/cloudbuild.yaml"
echo ""
