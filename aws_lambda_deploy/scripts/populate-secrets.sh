#!/usr/bin/env bash
# =============================================================================
# populate-secrets.sh — Populate AWS Secrets Manager from .env file
# =============================================================================
#
# Usage:
#   ./scripts/populate-secrets.sh [dev|prod]
#
# What it does:
#   1. Reads FB_ACCESS_TOKEN from /Users/emadruga/proj/metaAds/.env
#   2. Prompts for Clerk keys (or reads from environment)
#   3. Populates AWS Secrets Manager with both secrets
#
# Prerequisites:
#   - .env file exists with FB_ACCESS_TOKEN
#   - AWS CLI configured (profile: metads)
#   - Terraform already applied (secrets containers exist)
#
# =============================================================================

set -euo pipefail

ENV="${1:-dev}"
AWS_PROFILE="metads"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${SCRIPT_DIR}/../.."
ENV_FILE="${REPO_ROOT}/.env"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info() {
  echo -e "${BLUE}➜${NC} $1"
}

success() {
  echo -e "${GREEN}✓${NC} $1"
}

error() {
  echo -e "${RED}✗${NC} $1"
  exit 1
}

warn() {
  echo -e "${YELLOW}⚠${NC} $1"
}

echo "============================================="
echo "  Populate AWS Secrets Manager"
echo "  Environment: ${ENV}"
echo "============================================="
echo ""

# ---------------------------------------------------------------------------
# Step 1: Load Meta API token from .env
# ---------------------------------------------------------------------------

info "Loading FB_ACCESS_TOKEN from .env..."

if [ ! -f "${ENV_FILE}" ]; then
  error ".env file not found at ${ENV_FILE}"
fi

# Extract FB_ACCESS_TOKEN (handle quoted and unquoted values)
META_TOKEN=$(grep -E "^FB_ACCESS_TOKEN=" "${ENV_FILE}" | cut -d= -f2- | tr -d '"' | tr -d "'" | tr -d ' ')

if [[ -z "${META_TOKEN}" ]]; then
  error "FB_ACCESS_TOKEN not found in .env file. Please add: FB_ACCESS_TOKEN=\"your_token_here\""
fi

success "Loaded FB_ACCESS_TOKEN (${#META_TOKEN} chars)"
info "Token preview: ${META_TOKEN:0:20}...${META_TOKEN: -10}"

# ---------------------------------------------------------------------------
# Step 2: Get Clerk keys
# ---------------------------------------------------------------------------

info "Loading Clerk keys..."
echo ""

FRONTEND_ENV="${REPO_ROOT}/frontend/.env"

# 1. Try to load publishable key from frontend/.env
if [ -f "${FRONTEND_ENV}" ]; then
  CLERK_PUB=$(grep -E "^VITE_CLERK_PUBLISHABLE_KEY=" "${FRONTEND_ENV}" | cut -d= -f2- | tr -d '"' | tr -d "'" | tr -d ' ')

  if [[ -n "${CLERK_PUB}" ]]; then
    success "Loaded VITE_CLERK_PUBLISHABLE_KEY from frontend/.env"
  fi
fi

# 2. Try to load secret keys from root .env (optional)
if [ -f "${ENV_FILE}" ]; then
  CLERK_SECRET=$(grep -E "^CLERK_SECRET_KEY=" "${ENV_FILE}" | cut -d= -f2- | tr -d '"' | tr -d "'" | tr -d ' ')
  CLERK_WEBHOOK=$(grep -E "^CLERK_WEBHOOK_SECRET=" "${ENV_FILE}" | cut -d= -f2- | tr -d '"' | tr -d "'" | tr -d ' ')
fi

# 3. Check environment variables (for CI/CD)
CLERK_PUB="${CLERK_PUB:-${CLERK_PUBLISHABLE_KEY:-}}"
CLERK_SECRET="${CLERK_SECRET:-${CLERK_SECRET_KEY:-}}"
CLERK_WEBHOOK="${CLERK_WEBHOOK:-${CLERK_WEBHOOK_SECRET:-}}"

# 4. Prompt for missing keys
if [[ -z "${CLERK_PUB}" ]]; then
  echo "Publishable key not found in frontend/.env"
  read -p "Publishable key (pk_test_...): " CLERK_PUB
fi

if [[ -z "${CLERK_SECRET}" ]]; then
  echo "Get your secret key from: https://dashboard.clerk.com → API Keys"
  read -sp "Secret key (sk_test_...): " CLERK_SECRET
  echo ""
fi

if [[ -z "${CLERK_WEBHOOK}" ]]; then
  echo "Get your webhook secret from: https://dashboard.clerk.com → Webhooks"
  read -sp "Webhook secret (whsec_...): " CLERK_WEBHOOK
  echo ""
fi

echo ""

# Validate Clerk keys format
if [[ ! "${CLERK_PUB}" =~ ^pk_(test|live)_ ]]; then
  error "Invalid Clerk publishable key format. Should start with 'pk_test_' or 'pk_live_'"
fi

if [[ ! "${CLERK_SECRET}" =~ ^sk_(test|live)_ ]]; then
  error "Invalid Clerk secret key format. Should start with 'sk_test_' or 'sk_live_'"
fi

if [[ ! "${CLERK_WEBHOOK}" =~ ^whsec_ ]]; then
  error "Invalid Clerk webhook secret format. Should start with 'whsec_'"
fi

success "Clerk keys validated"

# ---------------------------------------------------------------------------
# Step 3: Populate Meta API secret
# ---------------------------------------------------------------------------

info "Populating Meta API secret in AWS Secrets Manager..."

aws secretsmanager put-secret-value \
  --profile "${AWS_PROFILE}" \
  --secret-id "metaads/${ENV}/meta-api" \
  --secret-string "{\"access_token\":\"${META_TOKEN}\"}" \
  --output json > /dev/null

success "Meta API secret populated (metaads/${ENV}/meta-api)"

# ---------------------------------------------------------------------------
# Step 4: Populate Clerk secret
# ---------------------------------------------------------------------------

info "Populating Clerk secret in AWS Secrets Manager..."

CLERK_JSON=$(cat <<EOF
{
  "publishable_key": "${CLERK_PUB}",
  "secret_key": "${CLERK_SECRET}",
  "webhook_secret": "${CLERK_WEBHOOK}"
}
EOF
)

aws secretsmanager put-secret-value \
  --profile "${AWS_PROFILE}" \
  --secret-id "metaads/${ENV}/clerk" \
  --secret-string "${CLERK_JSON}" \
  --output json > /dev/null

success "Clerk secret populated (metaads/${ENV}/clerk)"

# ---------------------------------------------------------------------------
# Step 5: Verify secrets
# ---------------------------------------------------------------------------

info "Verifying secrets..."

# Check Meta API secret
META_CHECK=$(aws secretsmanager get-secret-value \
  --profile "${AWS_PROFILE}" \
  --secret-id "metaads/${ENV}/meta-api" \
  --query SecretString \
  --output text 2>/dev/null || echo "")

if echo "${META_CHECK}" | jq -e .access_token > /dev/null 2>&1; then
  success "Meta API secret verified"
else
  error "Meta API secret verification failed"
fi

# Check Clerk secret
CLERK_CHECK=$(aws secretsmanager get-secret-value \
  --profile "${AWS_PROFILE}" \
  --secret-id "metaads/${ENV}/clerk" \
  --query SecretString \
  --output text 2>/dev/null || echo "")

if echo "${CLERK_CHECK}" | jq -e '.publishable_key, .secret_key, .webhook_secret' > /dev/null 2>&1; then
  success "Clerk secret verified"
else
  error "Clerk secret verification failed"
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

echo ""
echo "============================================="
echo -e "${GREEN}Secrets populated successfully!${NC}"
echo "============================================="
echo ""
echo "Secrets in AWS Secrets Manager:"
echo "  1. metaads/${ENV}/meta-api"
echo "     - access_token: ${META_TOKEN:0:20}...${META_TOKEN: -10}"
echo ""
echo "  2. metaads/${ENV}/clerk"
echo "     - publishable_key: ${CLERK_PUB}"
echo "     - secret_key: ${CLERK_SECRET:0:20}...${CLERK_SECRET: -10}"
echo "     - webhook_secret: ${CLERK_WEBHOOK:0:20}...${CLERK_WEBHOOK: -10}"
echo ""
echo "Next steps:"
echo "  1. Update CORS in dev.tfvars"
echo "  2. Package Lambda code: ./scripts/package.sh"
echo "  3. Deploy Lambda code: cd infra && terraform apply -var-file=dev.tfvars"
echo "  4. Deploy frontend: ./scripts/deploy.sh dev"
echo ""
