# Deployment Session - February 22, 2026

## Summary

This document tracks the issues encountered during the initial AWS Lambda deployment and the fixes applied. The deployment progressed from infrastructure setup through to addressing runtime errors in the Lambda functions.

---

## Issues Fixed

### 1. ✅ CloudFront Access Denied (Empty S3 Bucket)

**Error:**
```xml
<Error>
  <Code>AccessDenied</Code>
  <Message>Access Denied</Message>
</Error>
```

**Root Cause:**
- Terraform infrastructure was deployed successfully
- Frontend files were never uploaded to S3
- CloudFront returned Access Denied when trying to serve non-existent files

**Fix Applied:**
```bash
cd aws_lambda_deploy
./scripts/deploy.sh dev
```

**Result:** Frontend successfully built and uploaded 24 files to S3, CloudFront cache invalidated.

---

### 2. ✅ Terraform Output Flag Error in deploy.sh

**Error:**
```
flag provided but not defined: -var-file
```

**Root Cause:**
- `deploy.sh` was calling `terraform output` with `-var-file` flag
- The `terraform output` command doesn't accept this flag (only `terraform plan` and `terraform apply` do)

**Fix Applied:**
Edited `deploy.sh` to remove `-var-file` from all `terraform output` commands:

```bash
# BEFORE (broken):
FRONTEND_BUCKET=$(terraform output -var-file="${TFVARS_FILE}" -raw frontend_bucket_name)

# AFTER (fixed):
FRONTEND_BUCKET=$(terraform output -raw frontend_bucket_name)
```

**Files Modified:**
- `aws_lambda_deploy/scripts/deploy.sh`

---

### 3. ✅ Lambda Functions Using Stub Code

**Error:**
```
Request failed with status code 500
```

**Root Cause:**
- Lambda functions were deployed with 311-byte stub files
- Real handler code (2-3KB) was never packaged or deployed
- Functions returned 501 "Not Implemented" responses

**Fix Applied:**
```bash
# Package real Lambda code
cd aws_lambda_deploy
./scripts/package.sh

# Deploy to AWS
cd infra
terraform apply -var-file=dev.tfvars -auto-approve
```

**Result:** All 7 Lambda functions updated with real handler code.

---

### 4. ✅ Secrets Manager Had Placeholder Values

**Error:**
- Meta API secret: `{"access_token": "placeholder"}`
- Clerk secret: Missing proper values

**Root Cause:**
- Terraform created secret containers but didn't populate actual values
- Secrets need to be populated after Terraform apply

**Fix Applied:**
Manual population using AWS CLI:

```bash
# Meta API Token
aws secretsmanager put-secret-value \
  --profile metads \
  --secret-id metaads/dev/meta-api \
  --secret-string '{"access_token":"EAFuK2ebbHb4BQ..."}'

# Clerk Keys
aws secretsmanager put-secret-value \
  --profile metads \
  --secret-id metaads/dev/clerk \
  --secret-string '{
    "publishable_key": "pk_test_...",
    "secret_key": "sk_test_...",
    "webhook_secret": "whsec_placeholder_get_from_clerk_dashboard"
  }'
```

**Values Used:**
- Meta API token: Read from `/Users/emadruga/proj/metaAds/.env`
- Clerk publishable key: Read from `/Users/emadruga/proj/metaAds/frontend/.env`
- Clerk secret key: Read from `/Users/emadruga/proj/metaAds/.env`
- Clerk webhook secret: Placeholder (needs real value from Clerk dashboard)

---

### 5. ✅ Lambda Layer Not Attached to Functions

**Error:**
```
[ERROR] Runtime.ImportModuleError: Unable to import module 'handler': No module named 'jwt'
```

**Root Cause:**
- The shared Lambda layer containing PyJWT and other dependencies was packaged
- However, Terraform configuration was missing:
  - `aws_lambda_layer_version` resource to deploy the layer
  - `layers` parameter on Lambda function resources

**Fix Applied:**

**Added Lambda Layer Resource** in `lambda.tf`:
```hcl
resource "aws_lambda_layer_version" "shared" {
  layer_name          = "${local.name_prefix}-shared-layer"
  description         = "Shared Python dependencies for all Lambda functions"
  filename            = "${local.stubs_path}/shared_layer.zip"
  source_code_hash    = filebase64sha256("${local.stubs_path}/shared_layer.zip")
  compatible_runtimes = [var.lambda_runtime]

  lifecycle {
    create_before_destroy = true
  }
}
```

**Attached Layer to All Functions:**
```hcl
resource "aws_lambda_function" "authorizer" {
  # ... existing config ...
  layers = [aws_lambda_layer_version.shared.arn]
  # ... rest of config ...
}
# Repeated for all 7 Lambda functions
```

**Result:** Layer deployed successfully with ARN `arn:aws:lambda:us-east-1:645069181643:layer:metaads-dev-shared-layer:1`

**Files Modified:**
- `aws_lambda_deploy/infra/lambda.tf`

---

### 6. ✅ Invalid ELF Header (Platform Architecture Mismatch)

**Error:**
```
[ERROR] Runtime.ImportModuleError: Unable to import module 'handler':
/opt/python/cryptography/hazmat/bindings/_rust.abi3.so: invalid ELF header
```

**Root Cause:**
- Lambda layer was built on macOS (Darwin)
- Lambda runs on Linux x86_64
- The `cryptography` package contains compiled `.so` binaries
- macOS binaries are incompatible with Linux

**Fix Applied:**

Updated `package.sh` to force Linux platform when installing Python packages:

```bash
# BEFORE (installs for current platform - macOS):
pip install -r requirements.txt -t "${LAYER_BUILD_DIR}/python/" --quiet --no-cache-dir

# AFTER (installs for Linux):
pip install -r "${REQUIREMENTS_FILE}" -t "${LAYER_BUILD_DIR}/python/" \
  --platform manylinux2014_x86_64 \
  --implementation cp \
  --python-version 3.11 \
  --only-binary=:all: \
  --upgrade \
  --quiet --no-cache-dir
```

**Rebuild and Deploy:**
```bash
# Rebuild layer with Linux binaries
./scripts/package.sh

# Deploy new layer version
cd infra
terraform apply -var-file=dev.tfvars -auto-approve
```

**Result:**
- New layer version 2 created with Linux-compatible binaries
- Layer size: 27MB (optimized Linux binaries vs 29MB macOS binaries)
- All 7 Lambda functions updated to use layer version 2

**Files Modified:**
- `aws_lambda_deploy/scripts/package.sh`

---

### 7. ✅ Missing CLERK_JWKS_URL in Secrets

**Error:**
```
[ERROR] Authorizer error: CLERK_JWKS_URL not configured
RuntimeError: CLERK_JWKS_URL not configured
```

**Root Cause:**
- Authorizer Lambda needs the JWKS URL to verify JWT tokens
- The Clerk secret was missing the `jwks_url` field
- Code checks environment variable first, then falls back to Secrets Manager

**Fix Applied:**

Decoded Clerk publishable key to extract domain:
```bash
# pk_test_ZW5nYWdpbmctc2Vhc25haWwtNzIuY2xlcmsuYWNjb3VudHMuZGV2JA decodes to:
# engaging-seasnail-72.clerk.accounts.dev
```

Updated Clerk secret with JWKS URL:
```bash
aws secretsmanager put-secret-value \
  --profile metads \
  --secret-id metaads/dev/clerk \
  --secret-string '{
    "publishable_key": "pk_test_ZW5nYWdpbmctc2Vhc25haWwtNzIuY2xlcmsuYWNjb3VudHMuZGV2JA",
    "secret_key": "sk_test_1by7q9FCPsvML4yGKZZbRJBRi2hZDcJ5SFAUwOCniW",
    "webhook_secret": "whsec_placeholder_get_from_clerk_dashboard",
    "jwks_url": "https://engaging-seasnail-72.clerk.accounts.dev/.well-known/jwks.json"
  }'
```

**Result:** Authorizer can now fetch JWKS for JWT verification.

---

## Current Status

### ✅ Infrastructure Deployed
- API Gateway HTTP API
- 7 Lambda functions (authorizer, auth, niches, ads, saved, collect_trigger, collect_worker)
- Lambda layer version 2 (Linux binaries)
- DynamoDB table
- S3 buckets (frontend + Lambda packages)
- CloudFront distribution
- Secrets Manager (Meta API + Clerk)
- IAM roles and policies
- CloudWatch Log Groups
- SQS Dead Letter Queue

### ✅ Frontend Deployed
- Vue 3 app built and uploaded to S3
- 24 files deployed
- CloudFront cache invalidated
- Accessible at: https://d3ba787xl1d882.cloudfront.net/

### ✅ Authentication Working
- Clerk authentication integrated
- Users can sign in successfully
- JWT token generation working

### ⚠️ API Still Has Issues
- User can login but receives "Error Loading Niches" with 500 status
- Authorizer Lambda configured and should be working
- Need to investigate niches Lambda logs

---

## Remaining Issues / TODO

### 1. 🔴 HIGH PRIORITY: API 500 Error on GET /api/niches

**Symptoms:**
- User can login with Clerk successfully
- Frontend shows "Error Loading Niches"
- Request to GET `/api/niches` returns 500 status

**Next Steps:**
1. Check authorizer Lambda logs to verify JWT validation is working
2. Check niches Lambda logs for actual error
3. Verify DynamoDB permissions and table access
4. Test authorizer with a manual JWT token

**Commands to Debug:**
```bash
# Check authorizer logs
aws logs tail /aws/lambda/metaads-dev-authorizer --profile metads --since 5m --follow

# Check niches Lambda logs
aws logs tail /aws/lambda/metaads-dev-niches --profile metads --since 5m --follow

# Check API Gateway logs
aws logs tail /aws/apigateway/metaads-dev-api --profile metads --since 5m --follow

# Test API directly
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  https://f4k5jdd47a.execute-api.us-east-1.amazonaws.com/api/niches
```

---

### 2. 🟡 MEDIUM PRIORITY: Get Real Clerk Webhook Secret

**Current State:**
- Webhook secret is placeholder: `whsec_placeholder_get_from_clerk_dashboard`
- Auth webhook handler at `POST /api/auth/webhook` won't work without real secret

**Action Required:**
1. Go to https://dashboard.clerk.com
2. Navigate to your application
3. Go to Webhooks section
4. Create/copy webhook signing secret (starts with `whsec_`)
5. Update secret in AWS:

```bash
aws secretsmanager put-secret-value \
  --profile metads \
  --secret-id metaads/dev/clerk \
  --secret-string '{
    "publishable_key": "pk_test_ZW5nYWdpbmctc2Vhc25haWwtNzIuY2xlcmsuYWNjb3VudHMuZGV2JA",
    "secret_key": "sk_test_1by7q9FCPsvML4yGKZZbRJBRi2hZDcJ5SFAUwOCniW",
    "webhook_secret": "whsec_REAL_SECRET_HERE",
    "jwks_url": "https://engaging-seasnail-72.clerk.accounts.dev/.well-known/jwks.json"
  }'
```

---

### 3. 🟡 MEDIUM PRIORITY: Configure Clerk Webhook Endpoint

**Current State:**
- Auth Lambda has webhook handler implemented
- Clerk dashboard doesn't know about our endpoint yet

**Action Required:**
1. Go to https://dashboard.clerk.com → Webhooks
2. Add endpoint: `https://f4k5jdd47a.execute-api.us-east-1.amazonaws.com/api/auth/webhook`
3. Select events to subscribe to (e.g., `user.created`, `user.updated`, `user.deleted`)
4. Copy the signing secret and update AWS Secrets Manager (see TODO #2)

**Why It Matters:**
- Webhook syncs Clerk user events to DynamoDB
- Creates/updates user records in your database
- Required for full user management

---

### 4. 🟢 LOW PRIORITY: Update Scripts to Auto-Add JWKS URL

**Current State:**
- `populate-secrets.sh` and `deploy-all.sh` don't add `jwks_url` automatically
- Had to manually add it after deployment

**Improvement:**
Update scripts to derive JWKS URL from Clerk publishable key:

```bash
# In populate-secrets.sh, after loading CLERK_PUB:
if [[ -n "${CLERK_PUB}" ]]; then
  # Decode publishable key to get domain
  CLERK_DOMAIN=$(echo "${CLERK_PUB}" | base64 -d 2>/dev/null | grep -oE '[a-z0-9-]+\.clerk\.accounts\.[a-z]+')
  JWKS_URL="https://${CLERK_DOMAIN}/.well-known/jwks.json"
fi

# Then include in secret JSON:
--secret-string "{
  \"publishable_key\":\"${CLERK_PUB}\",
  \"secret_key\":\"${CLERK_SECRET}\",
  \"webhook_secret\":\"${CLERK_WEBHOOK}\",
  \"jwks_url\":\"${JWKS_URL}\"
}"
```

**Files to Update:**
- `aws_lambda_deploy/scripts/populate-secrets.sh`
- `aws_lambda_deploy/scripts/deploy-all.sh`

---

### 5. 🟢 LOW PRIORITY: End-to-End Smoke Tests

**Current State:**
- `test.sh` exists but hasn't been run successfully
- Manual testing in progress

**Action Required:**
Once API is working, run automated tests:

```bash
cd aws_lambda_deploy
./scripts/test.sh dev
```

**Tests Should Cover:**
- ✅ DynamoDB table exists and is accessible
- ✅ Secrets Manager contains valid secrets
- ✅ Lambda functions are deployed and invocable
- ✅ S3 frontend bucket has files
- ✅ CloudFront distribution is enabled
- ✅ API Gateway endpoints respond
- 🔄 JWT authentication flow
- 🔄 CRUD operations on niches
- 🔄 Ad collection workflow

---

### 6. 🟢 LOW PRIORITY: CORS Configuration

**Current State:**
- CORS may not be configured for CloudFront domain
- Could cause issues with API calls from frontend

**Action Required:**
Check if CORS needs updating in `dev.tfvars`:

```bash
# Check current CORS setting
grep cors_allow_origins aws_lambda_deploy/infra/dev.tfvars

# If not set, add:
cors_allow_origins = ["https://d3ba787xl1d882.cloudfront.net"]

# Re-apply Terraform
cd infra
terraform apply -var-file=dev.tfvars
```

---

## Deployment Resources

### URLs
- **Frontend:** https://d3ba787xl1d882.cloudfront.net/
- **API Gateway:** https://f4k5jdd47a.execute-api.us-east-1.amazonaws.com/
- **Clerk Dashboard:** https://dashboard.clerk.com

### AWS Resources
- **Account ID:** 645069181643
- **Region:** us-east-1
- **Profile:** metads

### Key ARNs
- **DynamoDB Table:** `arn:aws:dynamodb:us-east-1:645069181643:table/metaads-dev-table`
- **Meta API Secret:** `arn:aws:secretsmanager:us-east-1:645069181643:secret:metaads/dev/meta-api-HVxma7`
- **Clerk Secret:** `arn:aws:secretsmanager:us-east-1:645069181643:secret:metaads/dev/clerk-P1Uvg9`
- **Lambda Layer:** `arn:aws:lambda:us-east-1:645069181643:layer:metaads-dev-shared-layer:2`
- **CloudFront Distribution:** E9Q8645UTHPJD

---

## Quick Commands Reference

### Check Lambda Logs
```bash
# Authorizer
aws logs tail /aws/lambda/metaads-dev-authorizer --profile metads --follow

# Niches
aws logs tail /aws/lambda/metaads-dev-niches --profile metads --follow

# Any Lambda
aws logs tail /aws/lambda/metaads-dev-<function-name> --profile metads --since 5m
```

### Update Secrets
```bash
# View current secret
aws secretsmanager get-secret-value \
  --profile metads \
  --secret-id metaads/dev/clerk \
  --query SecretString \
  --output text | jq

# Update secret
aws secretsmanager put-secret-value \
  --profile metads \
  --secret-id metaads/dev/clerk \
  --secret-string '{"key":"value"}'
```

### Redeploy Lambda Code
```bash
cd aws_lambda_deploy
./scripts/package.sh
cd infra
terraform apply -var-file=dev.tfvars -auto-approve
```

### Redeploy Frontend
```bash
cd aws_lambda_deploy
./scripts/deploy.sh dev
```

### Check Lambda Function Details
```bash
aws lambda get-function-configuration \
  --profile metads \
  --function-name metaads-dev-niches \
  | jq
```

---

## Lessons Learned

1. **Platform Architecture Matters**: Always build Lambda layers for the target platform (Linux x86_64), not your development machine (macOS). Use `--platform manylinux2014_x86_64` with pip.

2. **Layer Configuration Is Required**: Creating a layer zip file isn't enough - Terraform needs both the `aws_lambda_layer_version` resource AND the `layers` parameter on each function.

3. **Secrets Need Manual Population**: Terraform creates secret containers but doesn't populate values. Always run `populate-secrets.sh` after `terraform apply`.

4. **JWKS URL Is Required for Clerk**: JWT verification needs the JWKS endpoint. Derive it from the publishable key domain: `https://{domain}/.well-known/jwks.json`

5. **Frontend Deployment Is Separate**: `terraform apply` doesn't deploy frontend files. Always run `deploy.sh` after infrastructure changes.

6. **Test Incrementally**: Deploy in stages and test each layer (infrastructure → secrets → Lambda code → frontend) before moving to the next.

---

## Next Session Checklist

Before starting the next debugging session:

1. ☐ Clear browser cache / hard refresh to ensure latest frontend code
2. ☐ Check all Lambda function logs for recent errors
3. ☐ Verify DynamoDB table is empty/ready for testing
4. ☐ Confirm all secrets are populated with real values (not placeholders)
5. ☐ Test authentication flow independently
6. ☐ Test API endpoints with curl/Postman before browser testing
7. ☐ Review API Gateway authorizer configuration
8. ☐ Check CloudWatch Logs for all services

---

**Session Date:** February 22, 2026
**Duration:** ~3 hours
**Status:** Infrastructure deployed, frontend working, API authentication configured, but API endpoints returning 500 errors
**Next Priority:** Debug niches Lambda 500 error
