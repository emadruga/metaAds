#!/usr/bin/env bash
# =============================================================================
# build_scraper_image.sh
#
# Builds the competitors_scraper container image and pushes it to ECR.
# Run this BEFORE `terraform apply` on first deploy, and whenever the
# Playwright handler or Dockerfile changes.
#
# Usage:
#   bash aws_lambda_deploy/scripts/build_scraper_image.sh           # tag: latest
#   bash aws_lambda_deploy/scripts/build_scraper_image.sh v1.2.3    # custom tag
#
# Prerequisites:
#   - Docker running locally (docker buildx for multi-arch)
#   - AWS CLI configured with metads profile
#   - Sufficient ECR permissions (ecr:GetAuthorizationToken, ecr:BatchCheckLayerAvailability, etc.)
# =============================================================================

set -euo pipefail

PROFILE="${AWS_PROFILE:-metads}"
REGION="${AWS_DEFAULT_REGION:-us-east-1}"
IMAGE_TAG="${1:-latest}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
CONTEXT_DIR="${PROJECT_ROOT}/aws_lambda_deploy/lambda_src/competitors_scraper"

# Resolve AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity \
  --profile "$PROFILE" \
  --query Account \
  --output text)

REPO_NAME="metaads-dev-competitors-scraper"
REGISTRY="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"
IMAGE_URI="${REGISTRY}/${REPO_NAME}:${IMAGE_TAG}"

echo "========================================"
echo "Competitors Scraper — ECR Build & Push"
echo "========================================"
echo "  Profile    : ${PROFILE}"
echo "  Region     : ${REGION}"
echo "  Account    : ${ACCOUNT_ID}"
echo "  Image URI  : ${IMAGE_URI}"
echo "  Context    : ${CONTEXT_DIR}"
echo "========================================"

# --------------------------------------------------------------------------
# 1. Authenticate Docker to ECR
# --------------------------------------------------------------------------
echo ""
echo "[1/4] Authenticating Docker to ECR..."
aws ecr get-login-password \
  --profile "$PROFILE" \
  --region "$REGION" \
  | docker login \
    --username AWS \
    --password-stdin "${REGISTRY}"

# --------------------------------------------------------------------------
# 2. Ensure the ECR repository exists
# --------------------------------------------------------------------------
echo ""
echo "[2/4] Ensuring ECR repository exists..."
aws ecr describe-repositories \
  --profile "$PROFILE" \
  --region "$REGION" \
  --repository-names "$REPO_NAME" \
  > /dev/null 2>&1 \
|| aws ecr create-repository \
    --profile "$PROFILE" \
    --region "$REGION" \
    --repository-name "$REPO_NAME" \
    --image-tag-mutability MUTABLE \
    > /dev/null

echo "  Repository: ${REGISTRY}/${REPO_NAME}"

# --------------------------------------------------------------------------
# 3. Build for linux/amd64 (Lambda runtime architecture)
# --------------------------------------------------------------------------
echo ""
echo "[3/4] Building image (platform: linux/amd64)..."
docker build \
  --platform linux/amd64 \
  --tag "${IMAGE_URI}" \
  "${CONTEXT_DIR}"

echo "  Built: ${IMAGE_URI}"

# --------------------------------------------------------------------------
# 4. Push to ECR
# --------------------------------------------------------------------------
echo ""
echo "[4/4] Pushing image to ECR..."
docker push "${IMAGE_URI}"

echo ""
echo "========================================"
echo "SUCCESS"
echo "========================================"
echo "  Image pushed: ${IMAGE_URI}"
echo ""
echo "Next steps:"
echo "  a) If this is the first push, run Terraform to create the Lambda:"
echo "     cd aws_lambda_deploy/infra && terraform apply -var-file=dev.tfvars -auto-approve"
echo ""
echo "  b) If the Lambda already exists, update the image in place:"
echo "     aws lambda update-function-code \\"
echo "       --profile ${PROFILE} --region ${REGION} \\"
echo "       --function-name metaads-dev-competitors-scraper \\"
echo "       --image-uri ${IMAGE_URI}"
echo ""
echo "  c) To set COMPETITORS_SCRAPER_ARN on the competitors Lambda, run terraform apply."
