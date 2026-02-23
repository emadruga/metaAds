#!/usr/bin/env bash
# =============================================================================
# deploy-all.sh — Complete MetaAds deployment in one command
# =============================================================================
#
# Usage:
#   ./scripts/deploy-all.sh [dev|prod]
#
# What it does:
#   1. Validates prerequisites (AWS CLI, Terraform, Node.js, Python)
#   2. Runs terraform init + apply
#   3. Prompts for secrets (Meta API token, Clerk keys)
#   4. Packages Lambda code
#   5. Deploys Lambda code
#   6. Prompts for CORS domain and updates
#   7. Deploys frontend
#   8. Runs smoke tests
#
# IMPORTANT: This is an interactive script. Have your credentials ready:
#   - Facebook App access token
#   - Clerk publishable key, secret key, webhook secret
#
# =============================================================================

set -euo pipefail

ENV="${1:-dev}"
AWS_PROFILE="metads"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY_ROOT="${SCRIPT_DIR}/.."
REPO_ROOT="${DEPLOY_ROOT}/.."
INFRA_DIR="${DEPLOY_ROOT}/infra"

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
echo "  MetaAds Serverless - Full Deployment"
echo "  Environment: ${ENV}"
echo "============================================="
echo ""

# ---------------------------------------------------------------------------
# Step 0: Validate prerequisites
# ---------------------------------------------------------------------------

info "Validating prerequisites..."

# AWS CLI
if ! command -v aws &> /dev/null; then
  error "AWS CLI not found. Install: https://aws.amazon.com/cli/"
fi

# Verify AWS credentials
if ! aws sts get-caller-identity --profile "${AWS_PROFILE}" &> /dev/null; then
  error "AWS credentials not configured for profile '${AWS_PROFILE}'"
fi

ACCOUNT_ID=$(aws sts get-caller-identity --profile "${AWS_PROFILE}" --query Account --output text)
success "AWS credentials valid (Account: ${ACCOUNT_ID})"

# Terraform
if ! command -v terraform &> /dev/null; then
  error "Terraform not found. Install: https://www.terraform.io/downloads"
fi

TERRAFORM_VERSION=$(terraform version -json | jq -r '.terraform_version')
success "Terraform ${TERRAFORM_VERSION}"

# Node.js
if ! command -v node &> /dev/null || ! command -v npm &> /dev/null; then
  error "Node.js/npm not found. Install: https://nodejs.org/"
fi

NODE_VERSION=$(node --version)
success "Node.js ${NODE_VERSION}"

# Python
if ! command -v python3 &> /dev/null; then
  error "Python 3 not found"
fi

PYTHON_VERSION=$(python3 --version)
success "Python ${PYTHON_VERSION}"

# jq (for JSON parsing)
if ! command -v jq &> /dev/null; then
  warn "jq not found (optional but recommended). Install: brew install jq"
fi

echo ""

# ---------------------------------------------------------------------------
# Step 1: Terraform init + apply
# ---------------------------------------------------------------------------

info "Step 1: Deploying infrastructure with Terraform..."
echo ""

cd "${INFRA_DIR}"

# Check if already initialized
if [ ! -d ".terraform" ]; then
  info "Initializing Terraform..."
  terraform init
else
  success "Terraform already initialized"
fi

# Plan
info "Planning infrastructure changes..."
terraform plan -var-file="${ENV}.tfvars" -out=tfplan

echo ""
read -p "Apply these changes? (yes/no): " CONFIRM

if [[ "${CONFIRM}" != "yes" ]]; then
  error "Deployment cancelled by user"
fi

# Apply
terraform apply tfplan
rm -f tfplan

success "Infrastructure deployed"
echo ""

# Save outputs
API_GATEWAY_URL=$(terraform output -raw api_gateway_url 2>/dev/null || echo "")
CLOUDFRONT_DOMAIN=$(terraform output -raw cloudfront_domain_name 2>/dev/null || echo "")
FRONTEND_BUCKET=$(terraform output -raw frontend_bucket_name 2>/dev/null || echo "")
FRONTEND_URL=$(terraform output -raw frontend_url 2>/dev/null || echo "")

echo "Outputs:"
echo "  API Gateway: ${API_GATEWAY_URL}"
echo "  CloudFront:  ${CLOUDFRONT_DOMAIN}"
echo "  Frontend:    ${FRONTEND_URL}"
echo ""

# ---------------------------------------------------------------------------
# Step 2: Populate secrets
# ---------------------------------------------------------------------------

info "Step 2: Populating Secrets Manager..."
echo ""

# Load FB_ACCESS_TOKEN from .env file
ENV_FILE="${REPO_ROOT}/.env"

if [ -f "${ENV_FILE}" ]; then
  # Source the .env file and extract FB_ACCESS_TOKEN
  # Using grep to avoid executing arbitrary code
  META_TOKEN=$(grep -E "^FB_ACCESS_TOKEN=" "${ENV_FILE}" | cut -d= -f2- | tr -d '"' | tr -d "'" | tr -d ' ')

  if [[ -n "${META_TOKEN}" ]]; then
    success "Loaded FB_ACCESS_TOKEN from .env (${#META_TOKEN} chars)"
  else
    warn "FB_ACCESS_TOKEN not found in .env file"
    META_TOKEN=""
  fi
else
  warn ".env file not found at ${ENV_FILE}"
  META_TOKEN=""
fi

# Check if secrets already have values
META_SECRET_EXISTS=$(aws secretsmanager get-secret-value \
  --profile "${AWS_PROFILE}" \
  --secret-id "metaads/${ENV}/meta-api" 2>/dev/null && echo "yes" || echo "no")

CLERK_SECRET_EXISTS=$(aws secretsmanager get-secret-value \
  --profile "${AWS_PROFILE}" \
  --secret-id "metaads/${ENV}/clerk" 2>/dev/null && echo "yes" || echo "no")

# Meta API token
if [[ "${META_SECRET_EXISTS}" == "yes" ]]; then
  warn "Meta API secret already exists"
  read -p "Update Meta API token from .env? (y/n): " UPDATE_META

  if [[ "${UPDATE_META}" == "y" ]]; then
    if [[ -z "${META_TOKEN}" ]]; then
      error "FB_ACCESS_TOKEN not found in .env file. Please add: FB_ACCESS_TOKEN=\"your_token_here\""
    fi

    aws secretsmanager put-secret-value \
      --profile "${AWS_PROFILE}" \
      --secret-id "metaads/${ENV}/meta-api" \
      --secret-string "{\"access_token\":\"${META_TOKEN}\"}"

    success "Meta API token updated from .env"
  else
    success "Meta API token unchanged"
  fi
else
  if [[ -z "${META_TOKEN}" ]]; then
    error "FB_ACCESS_TOKEN not found in .env file. Please add: FB_ACCESS_TOKEN=\"your_token_here\""
  fi

  info "Setting Meta API token from .env..."

  aws secretsmanager put-secret-value \
    --profile "${AWS_PROFILE}" \
    --secret-id "metaads/${ENV}/meta-api" \
    --secret-string "{\"access_token\":\"${META_TOKEN}\"}"

  success "Meta API token set from .env"
fi

# Clerk keys
# Load from frontend/.env and root .env
FRONTEND_ENV="${REPO_ROOT}/frontend/.env"
CLERK_PUB=""
CLERK_SECRET=""
CLERK_WEBHOOK=""

# 1. Try frontend/.env for publishable key
if [ -f "${FRONTEND_ENV}" ]; then
  CLERK_PUB=$(grep -E "^VITE_CLERK_PUBLISHABLE_KEY=" "${FRONTEND_ENV}" | cut -d= -f2- | tr -d '"' | tr -d "'" | tr -d ' ')
  if [[ -n "${CLERK_PUB}" ]]; then
    success "Loaded VITE_CLERK_PUBLISHABLE_KEY from frontend/.env"
  fi
fi

# 2. Try root .env for secret keys (optional)
if [ -f "${ENV_FILE}" ]; then
  CLERK_SECRET=$(grep -E "^CLERK_SECRET_KEY=" "${ENV_FILE}" | cut -d= -f2- | tr -d '"' | tr -d "'" | tr -d ' ')
  CLERK_WEBHOOK=$(grep -E "^CLERK_WEBHOOK_SECRET=" "${ENV_FILE}" | cut -d= -f2- | tr -d '"' | tr -d "'" | tr -d ' ')
fi

if [[ "${CLERK_SECRET_EXISTS}" == "yes" ]]; then
  warn "Clerk secret already exists"
  read -p "Update Clerk keys? (y/n): " UPDATE_CLERK

  if [[ "${UPDATE_CLERK}" == "y" ]]; then
    # Prompt for missing keys
    if [[ -z "${CLERK_PUB}" ]]; then
      read -p "Publishable key (pk_test_...): " CLERK_PUB
    fi
    if [[ -z "${CLERK_SECRET}" ]]; then
      read -sp "Secret key (sk_test_...): " CLERK_SECRET
      echo ""
    fi
    if [[ -z "${CLERK_WEBHOOK}" ]]; then
      read -sp "Webhook secret (whsec_...): " CLERK_WEBHOOK
      echo ""
    fi

    aws secretsmanager put-secret-value \
      --profile "${AWS_PROFILE}" \
      --secret-id "metaads/${ENV}/clerk" \
      --secret-string "{\"publishable_key\":\"${CLERK_PUB}\",\"secret_key\":\"${CLERK_SECRET}\",\"webhook_secret\":\"${CLERK_WEBHOOK}\"}"

    success "Clerk keys updated"
  else
    success "Clerk keys unchanged"
  fi
else
  # Prompt for missing keys
  if [[ -z "${CLERK_PUB}" ]]; then
    warn "Clerk publishable key not found in frontend/.env"
    read -p "Publishable key (pk_test_...): " CLERK_PUB
  fi
  if [[ -z "${CLERK_SECRET}" ]]; then
    warn "Clerk secret key not found in .env"
    echo "Get your secret key from: https://dashboard.clerk.com → API Keys"
    read -sp "Secret key (sk_test_...): " CLERK_SECRET
    echo ""
  fi
  if [[ -z "${CLERK_WEBHOOK}" ]]; then
    warn "Clerk webhook secret not found in .env"
    echo "Get your webhook secret from: https://dashboard.clerk.com → Webhooks"
    read -sp "Webhook secret (whsec_...): " CLERK_WEBHOOK
    echo ""
  fi

  aws secretsmanager put-secret-value \
    --profile "${AWS_PROFILE}" \
    --secret-id "metaads/${ENV}/clerk" \
    --secret-string "{\"publishable_key\":\"${CLERK_PUB}\",\"secret_key\":\"${CLERK_SECRET}\",\"webhook_secret\":\"${CLERK_WEBHOOK}\"}"

  success "Clerk keys set"
fi

echo ""

# ---------------------------------------------------------------------------
# Step 3: Update CORS
# ---------------------------------------------------------------------------

info "Step 3: Updating CORS configuration..."
echo ""

# Check if CORS is already set
CURRENT_CORS=$(grep -E "^cors_allow_origins" "${INFRA_DIR}/${ENV}.tfvars" || echo "")

if [[ -z "${CURRENT_CORS}" ]]; then
  warn "CORS not configured yet"
  echo "CloudFront domain: https://${CLOUDFRONT_DOMAIN}"
  echo ""
  read -p "Add this domain to CORS allowed origins? (y/n): " ADD_CORS

  if [[ "${ADD_CORS}" == "y" ]]; then
    echo "" >> "${INFRA_DIR}/${ENV}.tfvars"
    echo "# CORS - Auto-added by deploy-all.sh" >> "${INFRA_DIR}/${ENV}.tfvars"
    echo "cors_allow_origins = [\"https://${CLOUDFRONT_DOMAIN}\"]" >> "${INFRA_DIR}/${ENV}.tfvars"

    # Re-apply Terraform
    cd "${INFRA_DIR}"
    terraform apply -var-file="${ENV}.tfvars" -auto-approve

    success "CORS configured"
  else
    warn "CORS not configured - frontend may have issues"
  fi
else
  success "CORS already configured: ${CURRENT_CORS}"
fi

echo ""

# ---------------------------------------------------------------------------
# Step 4: Package Lambda code
# ---------------------------------------------------------------------------

info "Step 4: Packaging Lambda code..."
echo ""

cd "${DEPLOY_ROOT}"
./scripts/package.sh

success "Lambda code packaged"
echo ""

# ---------------------------------------------------------------------------
# Step 5: Deploy Lambda code
# ---------------------------------------------------------------------------

info "Step 5: Deploying Lambda code to AWS..."
echo ""

cd "${INFRA_DIR}"
terraform apply -var-file="${ENV}.tfvars" -auto-approve

success "Lambda code deployed"
echo ""

# ---------------------------------------------------------------------------
# Step 6: Deploy frontend
# ---------------------------------------------------------------------------

info "Step 6: Deploying frontend..."
echo ""

# Check if Clerk keys file exists
KEYS_FILE="${REPO_ROOT}/frontend/.env.${ENV}.keys"

if [ ! -f "${KEYS_FILE}" ]; then
  warn "Frontend Clerk keys file not found: ${KEYS_FILE}"

  # Use the publishable key we already got
  if [[ -n "${CLERK_PUB}" ]]; then
    echo "VITE_CLERK_PUBLISHABLE_KEY=${CLERK_PUB}" > "${KEYS_FILE}"
    success "Created ${KEYS_FILE}"
  else
    # Fetch from secrets manager
    CLERK_PUB=$(aws secretsmanager get-secret-value \
      --profile "${AWS_PROFILE}" \
      --secret-id "metaads/${ENV}/clerk" \
      --query SecretString \
      --output text | jq -r .publishable_key)

    echo "VITE_CLERK_PUBLISHABLE_KEY=${CLERK_PUB}" > "${KEYS_FILE}"
    success "Created ${KEYS_FILE}"
  fi
fi

cd "${REPO_ROOT}"
./aws_lambda_deploy/scripts/deploy.sh "${ENV}"

success "Frontend deployed"
echo ""

# ---------------------------------------------------------------------------
# Step 7: Run smoke tests
# ---------------------------------------------------------------------------

info "Step 7: Running smoke tests..."
echo ""

cd "${DEPLOY_ROOT}"
./scripts/test.sh "${ENV}"

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

echo ""
echo "============================================="
echo -e "${GREEN}Deployment complete!${NC}"
echo "============================================="
echo ""
echo "Frontend URL: ${FRONTEND_URL}"
echo "API Gateway:  ${API_GATEWAY_URL}"
echo ""
echo "Next steps:"
echo "  1. Open ${FRONTEND_URL}"
echo "  2. Sign in with Clerk"
echo "  3. Create a niche"
echo "  4. Trigger collection"
echo "  5. Search for ads"
echo ""
echo "Monitoring:"
echo "  - CloudWatch Logs: aws logs tail /aws/lambda/metaads-${ENV}-FUNCTION --profile ${AWS_PROFILE}"
echo "  - Cost Explorer: https://console.aws.amazon.com/cost-management/home"
echo ""
