#!/bin/bash
# Verify if local Lambda code matches deployed version

set -e

AWS_PROFILE="${AWS_PROFILE:-metads}"
FUNCTION_NAME="${1:-metaads-dev-ads}"
LAYER_NAME="${2:-metaads-dev-shared-layer}"

echo "🔍 Checking Lambda deployment status..."
echo "   Using AWS profile: $AWS_PROFILE"
echo ""

# Check Lambda function hash
echo "1️⃣  Lambda Function: $FUNCTION_NAME"
LOCAL_FUNC_HASH=$(openssl dgst -sha256 -binary aws_lambda_deploy/lambda_stubs/ads.zip | openssl enc -base64)
AWS_FUNC_HASH=$(aws lambda get-function --profile "$AWS_PROFILE" --function-name "$FUNCTION_NAME" --query 'Configuration.CodeSha256' --output text)

echo "   Local hash:  $LOCAL_FUNC_HASH"
echo "   AWS hash:    $AWS_FUNC_HASH"

if [ "$LOCAL_FUNC_HASH" = "$AWS_FUNC_HASH" ]; then
    echo "   ✅ Function code matches!"
else
    echo "   ❌ Function code DIFFERS - needs deployment"
fi
echo ""

# Check Lambda layer hash
echo "2️⃣  Lambda Layer: $LAYER_NAME"
LOCAL_LAYER_HASH=$(openssl dgst -sha256 -binary aws_lambda_deploy/lambda_stubs/shared_layer.zip | openssl enc -base64)
LAYER_VERSION=$(aws lambda list-layer-versions --profile "$AWS_PROFILE" --layer-name "$LAYER_NAME" --query 'LayerVersions[0].Version' --output text)
AWS_LAYER_HASH=$(aws lambda get-layer-version --profile "$AWS_PROFILE" --layer-name "$LAYER_NAME" --version-number "$LAYER_VERSION" --query 'Content.CodeSha256' --output text)

echo "   Layer version: $LAYER_VERSION"
echo "   Local hash:  $LOCAL_LAYER_HASH"
echo "   AWS hash:    $AWS_LAYER_HASH"

if [ "$LOCAL_LAYER_HASH" = "$AWS_LAYER_HASH" ]; then
    echo "   ✅ Layer code matches!"
else
    echo "   ❌ Layer code DIFFERS - needs deployment"
fi
echo ""

# Check if function is using latest layer
FUNC_LAYER_VERSION=$(aws lambda get-function --profile "$AWS_PROFILE" --function-name "$FUNCTION_NAME" --query 'Configuration.Layers[0].Arn' --output text | grep -oE '[0-9]+$')
echo "3️⃣  Layer attachment:"
echo "   Function using layer version: $FUNC_LAYER_VERSION"
echo "   Latest layer version:         $LAYER_VERSION"

if [ "$FUNC_LAYER_VERSION" = "$LAYER_VERSION" ]; then
    echo "   ✅ Function using latest layer!"
else
    echo "   ❌ Function using OLD layer - needs update"
fi
echo ""

# Summary
echo "═══════════════════════════════════════════════════"
if [ "$LOCAL_FUNC_HASH" = "$AWS_FUNC_HASH" ] && [ "$LOCAL_LAYER_HASH" = "$AWS_LAYER_HASH" ] && [ "$FUNC_LAYER_VERSION" = "$LAYER_VERSION" ]; then
    echo "✅ ALL CHECKS PASSED - Deployment is up to date!"
else
    echo "❌ DEPLOYMENT OUT OF SYNC - Run terraform apply"
fi
echo "═══════════════════════════════════════════════════"
