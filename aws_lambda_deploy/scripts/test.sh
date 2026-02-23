#!/usr/bin/env bash
# =============================================================================
# test.sh — Automated smoke tests for MetaAds serverless deployment
# =============================================================================
#
# Usage:
#   ./scripts/test.sh [dev|prod]
#
# What it tests:
#   1. AWS resources exist and are accessible
#   2. API Gateway endpoints respond
#   3. Lambda functions execute without errors
#   4. DynamoDB tables are operational
#   5. Secrets are populated
#
# Prerequisites:
#   - AWS CLI configured (profile: metads)
#   - Terraform already applied
#   - jq installed (for JSON parsing)
#
# =============================================================================

set -euo pipefail

ENV="${1:-dev}"
AWS_PROFILE="metads"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="${SCRIPT_DIR}/../infra"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

pass() {
  echo -e "${GREEN}✓${NC} $1"
}

fail() {
  echo -e "${RED}✗${NC} $1"
  FAILED_TESTS=$((FAILED_TESTS + 1))
}

warn() {
  echo -e "${YELLOW}⚠${NC} $1"
}

info() {
  echo "  $1"
}

FAILED_TESTS=0

echo "============================================="
echo "  MetaAds Serverless Smoke Tests"
echo "  Environment: ${ENV}"
echo "============================================="
echo ""

# ---------------------------------------------------------------------------
# Test 1: Terraform outputs are available
# ---------------------------------------------------------------------------

echo "[1/10] Checking Terraform outputs..."

cd "${INFRA_DIR}"

API_GATEWAY_URL=$(terraform output -var-file="${ENV}.tfvars" -raw api_gateway_url 2>/dev/null || echo "")
FRONTEND_BUCKET=$(terraform output -var-file="${ENV}.tfvars" -raw frontend_bucket_name 2>/dev/null || echo "")
CF_DISTRIBUTION_ID=$(terraform output -var-file="${ENV}.tfvars" -raw cloudfront_distribution_id 2>/dev/null || echo "")
DYNAMODB_TABLE=$(terraform output -var-file="${ENV}.tfvars" -raw dynamodb_table_name 2>/dev/null || echo "")

if [[ -n "${API_GATEWAY_URL}" && -n "${FRONTEND_BUCKET}" && -n "${DYNAMODB_TABLE}" ]]; then
  pass "Terraform outputs available"
  info "API Gateway: ${API_GATEWAY_URL}"
  info "Frontend bucket: ${FRONTEND_BUCKET}"
  info "DynamoDB table: ${DYNAMODB_TABLE}"
else
  fail "Terraform outputs missing. Have you run 'terraform apply'?"
  exit 1
fi

# ---------------------------------------------------------------------------
# Test 2: AWS credentials work
# ---------------------------------------------------------------------------

echo ""
echo "[2/10] Verifying AWS credentials..."

ACCOUNT_ID=$(aws sts get-caller-identity --profile "${AWS_PROFILE}" --query Account --output text 2>/dev/null || echo "")

if [[ -n "${ACCOUNT_ID}" ]]; then
  pass "AWS credentials valid (Account: ${ACCOUNT_ID})"
else
  fail "AWS credentials not configured or invalid"
  exit 1
fi

# ---------------------------------------------------------------------------
# Test 3: DynamoDB table exists and is active
# ---------------------------------------------------------------------------

echo ""
echo "[3/10] Checking DynamoDB table..."

TABLE_STATUS=$(aws dynamodb describe-table \
  --profile "${AWS_PROFILE}" \
  --table-name "${DYNAMODB_TABLE}" \
  --query 'Table.TableStatus' \
  --output text 2>/dev/null || echo "")

if [[ "${TABLE_STATUS}" == "ACTIVE" ]]; then
  pass "DynamoDB table is ACTIVE"

  # Check item count (optional)
  ITEM_COUNT=$(aws dynamodb scan \
    --profile "${AWS_PROFILE}" \
    --table-name "${DYNAMODB_TABLE}" \
    --select "COUNT" \
    --query 'Count' \
    --output text 2>/dev/null || echo "0")

  info "Table contains ${ITEM_COUNT} items"
else
  fail "DynamoDB table not found or not ACTIVE (status: ${TABLE_STATUS})"
fi

# ---------------------------------------------------------------------------
# Test 4: Secrets exist and are populated
# ---------------------------------------------------------------------------

echo ""
echo "[4/10] Checking Secrets Manager..."

# Meta API secret
META_SECRET=$(aws secretsmanager get-secret-value \
  --profile "${AWS_PROFILE}" \
  --secret-id "metaads/${ENV}/meta-api" \
  --query SecretString \
  --output text 2>/dev/null || echo "")

if [[ -n "${META_SECRET}" ]] && echo "${META_SECRET}" | jq -e .access_token > /dev/null 2>&1; then
  pass "Meta API secret populated"
else
  warn "Meta API secret not populated or invalid JSON"
  info "Run: aws secretsmanager put-secret-value --profile metads --secret-id metaads/${ENV}/meta-api --secret-string '{\"access_token\":\"YOUR_TOKEN\"}'"
fi

# Clerk secret
CLERK_SECRET=$(aws secretsmanager get-secret-value \
  --profile "${AWS_PROFILE}" \
  --secret-id "metaads/${ENV}/clerk" \
  --query SecretString \
  --output text 2>/dev/null || echo "")

if [[ -n "${CLERK_SECRET}" ]] && echo "${CLERK_SECRET}" | jq -e '.publishable_key, .secret_key, .webhook_secret' > /dev/null 2>&1; then
  pass "Clerk secret populated"
else
  warn "Clerk secret not populated or missing required keys"
  info "Run: aws secretsmanager put-secret-value --profile metads --secret-id metaads/${ENV}/clerk --secret-string '{...}'"
fi

# ---------------------------------------------------------------------------
# Test 5: Lambda functions exist
# ---------------------------------------------------------------------------

echo ""
echo "[5/10] Checking Lambda functions..."

EXPECTED_LAMBDAS=(
  "metaads-${ENV}-authorizer"
  "metaads-${ENV}-auth"
  "metaads-${ENV}-niches"
  "metaads-${ENV}-ads"
  "metaads-${ENV}-saved"
  "metaads-${ENV}-collect-trigger"
  "metaads-${ENV}-collect-worker"
)

LAMBDA_COUNT=0

for LAMBDA in "${EXPECTED_LAMBDAS[@]}"; do
  STATUS=$(aws lambda get-function \
    --profile "${AWS_PROFILE}" \
    --function-name "${LAMBDA}" \
    --query 'Configuration.State' \
    --output text 2>/dev/null || echo "")

  if [[ "${STATUS}" == "Active" ]]; then
    ((LAMBDA_COUNT++))
  fi
done

if [[ ${LAMBDA_COUNT} -eq ${#EXPECTED_LAMBDAS[@]} ]]; then
  pass "All ${#EXPECTED_LAMBDAS[@]} Lambda functions active"
else
  fail "Only ${LAMBDA_COUNT}/${#EXPECTED_LAMBDAS[@]} Lambda functions found"
fi

# ---------------------------------------------------------------------------
# Test 6: S3 frontend bucket exists
# ---------------------------------------------------------------------------

echo ""
echo "[6/10] Checking S3 frontend bucket..."

BUCKET_EXISTS=$(aws s3api head-bucket \
  --profile "${AWS_PROFILE}" \
  --bucket "${FRONTEND_BUCKET}" 2>&1 || echo "error")

if [[ "${BUCKET_EXISTS}" != *"error"* ]]; then
  pass "S3 frontend bucket exists"

  # Check if files are deployed
  FILE_COUNT=$(aws s3 ls "s3://${FRONTEND_BUCKET}/" --profile "${AWS_PROFILE}" --recursive | wc -l | tr -d ' ')

  if [[ ${FILE_COUNT} -gt 0 ]]; then
    info "Bucket contains ${FILE_COUNT} files"
  else
    warn "Bucket is empty. Run: ./scripts/deploy.sh ${ENV}"
  fi
else
  fail "S3 frontend bucket not found"
fi

# ---------------------------------------------------------------------------
# Test 7: CloudFront distribution is deployed
# ---------------------------------------------------------------------------

echo ""
echo "[7/10] Checking CloudFront distribution..."

CF_STATUS=$(aws cloudfront get-distribution \
  --profile "${AWS_PROFILE}" \
  --id "${CF_DISTRIBUTION_ID}" \
  --query 'Distribution.Status' \
  --output text 2>/dev/null || echo "")

if [[ "${CF_STATUS}" == "Deployed" ]]; then
  pass "CloudFront distribution is Deployed"
else
  warn "CloudFront distribution status: ${CF_STATUS} (may still be deploying)"
fi

# ---------------------------------------------------------------------------
# Test 8: API Gateway health endpoint responds
# ---------------------------------------------------------------------------

echo ""
echo "[8/10] Testing API Gateway health endpoint..."

HEALTH_URL="${API_GATEWAY_URL}/api/health"
HEALTH_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "${HEALTH_URL}" 2>/dev/null || echo "000")

if [[ "${HEALTH_RESPONSE}" == "200" ]]; then
  pass "API Gateway health endpoint returns 200"
else
  fail "API Gateway health endpoint returns ${HEALTH_RESPONSE}"
  info "URL: ${HEALTH_URL}"
fi

# ---------------------------------------------------------------------------
# Test 9: Lambda logs are accessible
# ---------------------------------------------------------------------------

echo ""
echo "[9/10] Checking CloudWatch Logs..."

LOG_GROUPS=$(aws logs describe-log-groups \
  --profile "${AWS_PROFILE}" \
  --log-group-name-prefix "/aws/lambda/metaads-${ENV}" \
  --query 'logGroups[*].logGroupName' \
  --output text 2>/dev/null || echo "")

if [[ -n "${LOG_GROUPS}" ]]; then
  LOG_GROUP_COUNT=$(echo "${LOG_GROUPS}" | wc -w | tr -d ' ')
  pass "CloudWatch log groups exist (${LOG_GROUP_COUNT} groups)"
else
  warn "No CloudWatch log groups found (Lambdas may not have been invoked yet)"
fi

# ---------------------------------------------------------------------------
# Test 10: Check for recent Lambda errors
# ---------------------------------------------------------------------------

echo ""
echo "[10/10] Checking for recent Lambda errors..."

ERROR_COUNT=0

for LAMBDA in "${EXPECTED_LAMBDAS[@]}"; do
  ERRORS=$(aws logs filter-log-events \
    --profile "${AWS_PROFILE}" \
    --log-group-name "/aws/lambda/${LAMBDA}" \
    --filter-pattern "ERROR" \
    --start-time $(($(date +%s) - 3600))000 \
    --query 'events[*].message' \
    --output text 2>/dev/null || echo "")

  if [[ -n "${ERRORS}" ]]; then
    ((ERROR_COUNT++))
  fi
done

if [[ ${ERROR_COUNT} -eq 0 ]]; then
  pass "No Lambda errors in the last hour"
else
  warn "${ERROR_COUNT} Lambda functions have errors in the last hour"
  info "Check logs: aws logs tail /aws/lambda/metaads-${ENV}-FUNCTION_NAME --profile metads"
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

echo ""
echo "============================================="
if [[ ${FAILED_TESTS} -eq 0 ]]; then
  echo -e "${GREEN}All tests passed!${NC}"
  echo "============================================="
  echo ""
  echo "Next steps:"
  echo "  1. Open frontend URL and test UI"
  echo "  2. Sign in with Clerk"
  echo "  3. Create a niche and trigger collection"
  echo "  4. Verify ads appear in search"
else
  echo -e "${RED}${FAILED_TESTS} test(s) failed${NC}"
  echo "============================================="
  echo ""
  echo "Review the failures above and check:"
  echo "  - Terraform apply completed successfully"
  echo "  - Secrets are populated (Phase D)"
  echo "  - Lambda code is packaged and deployed (Phase E)"
  exit 1
fi

echo ""
echo "Frontend URL: $(terraform output -var-file="${ENV}.tfvars" -raw frontend_url 2>/dev/null)"
echo "API Gateway URL: ${API_GATEWAY_URL}"
echo ""
