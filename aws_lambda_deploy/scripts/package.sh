#!/usr/bin/env bash
# =============================================================================
# package.sh — Package Lambda handlers + shared layer for deployment
# =============================================================================
#
# Usage:
#   ./scripts/package.sh
#
# What it does:
#   1. Creates the shared layer with dependencies (boto3, PyJWT, svix, requests)
#   2. Packages each of the 7 Lambda handlers with their real handler.py
#   3. Outputs ZIP files to lambda_stubs/ for Terraform to upload
#
# Prerequisites:
#   - Python 3.11 installed
#   - pip available
#
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY_ROOT="${SCRIPT_DIR}/.."
LAMBDA_SRC="${DEPLOY_ROOT}/lambda_src"
LAMBDA_LAYERS="${DEPLOY_ROOT}/lambda_layers"
OUTPUT_DIR="${DEPLOY_ROOT}/lambda_stubs"

echo "============================================="
echo "  Lambda Packaging Script"
echo "============================================="
echo ""

# ---------------------------------------------------------------------------
# Step 1: Package the shared layer
# ---------------------------------------------------------------------------

echo "[1/8] Packaging shared layer..."

SHARED_LAYER_DIR="${LAMBDA_LAYERS}/shared"
LAYER_BUILD_DIR="${SHARED_LAYER_DIR}/build"

# Clean previous build
rm -rf "${LAYER_BUILD_DIR}"
mkdir -p "${LAYER_BUILD_DIR}/python"

# Copy the Python modules from shared/python/ to build/python/
if [ -d "${SHARED_LAYER_DIR}/python" ]; then
  cp -r "${SHARED_LAYER_DIR}/python/"* "${LAYER_BUILD_DIR}/python/"
  echo "  Copied shared Python modules"
fi

# Install dependencies if requirements.txt exists
REQUIREMENTS_FILE="${SHARED_LAYER_DIR}/requirements.txt"

if [ -f "${REQUIREMENTS_FILE}" ]; then
  echo "  Installing dependencies from requirements.txt..."
  pip install -r "${REQUIREMENTS_FILE}" -t "${LAYER_BUILD_DIR}/python/" \
    --platform manylinux2014_x86_64 \
    --implementation cp \
    --python-version 3.11 \
    --only-binary=:all: \
    --upgrade \
    --quiet --no-cache-dir
else
  echo "  ⚠️  No requirements.txt found at ${REQUIREMENTS_FILE}"
  echo "  Installing default dependencies (boto3, PyJWT, svix, requests)..."
  pip install boto3 PyJWT svix requests -t "${LAYER_BUILD_DIR}/python/" \
    --platform manylinux2014_x86_64 \
    --implementation cp \
    --python-version 3.11 \
    --only-binary=:all: \
    --upgrade \
    --quiet --no-cache-dir
fi

# Create the layer ZIP
cd "${LAYER_BUILD_DIR}"
LAYER_ZIP="${OUTPUT_DIR}/shared_layer.zip"
rm -f "${LAYER_ZIP}"
zip -r "${LAYER_ZIP}" python/ -q

LAYER_SIZE=$(du -sh "${LAYER_ZIP}" | cut -f1)
echo "  ✓ Shared layer: ${LAYER_ZIP} (${LAYER_SIZE})"

# Clean up build dir
cd "${DEPLOY_ROOT}"
rm -rf "${LAYER_BUILD_DIR}"

# ---------------------------------------------------------------------------
# Step 2: Package each Lambda handler
# ---------------------------------------------------------------------------

HANDLERS=(
  "authorizer"
  "auth"
  "niches"
  "ads"
  "saved"
  "collect_trigger"
  "collect_worker"
)

STEP=2
for HANDLER in "${HANDLERS[@]}"; do
  echo ""
  echo "[${STEP}/8] Packaging ${HANDLER} handler..."

  HANDLER_DIR="${LAMBDA_SRC}/${HANDLER}"
  HANDLER_ZIP="${OUTPUT_DIR}/${HANDLER}.zip"

  if [ ! -f "${HANDLER_DIR}/handler.py" ]; then
    echo "  ✗ ERROR: ${HANDLER_DIR}/handler.py not found!"
    exit 1
  fi

  # Create ZIP with just the handler.py (dependencies come from the layer)
  cd "${HANDLER_DIR}"
  rm -f "${HANDLER_ZIP}"
  zip -j "${HANDLER_ZIP}" handler.py -q

  HANDLER_SIZE=$(du -sh "${HANDLER_ZIP}" | cut -f1)
  echo "  ✓ ${HANDLER}.zip (${HANDLER_SIZE})"

  ((STEP++))
done

cd "${DEPLOY_ROOT}"

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

echo ""
echo "============================================="
echo "  Packaging complete!"
echo "============================================="
echo ""
echo "Output files in ${OUTPUT_DIR}:"
ls -lh "${OUTPUT_DIR}"/*.zip | awk '{print "  " $9, "(" $5 ")"}'
echo ""
echo "Next steps:"
echo "  1. cd infra"
echo "  2. terraform apply -var-file=dev.tfvars"
echo "  (Terraform will upload the new ZIPs to Lambda)"
echo ""
