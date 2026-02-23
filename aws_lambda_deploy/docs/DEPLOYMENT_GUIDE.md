# MetaAds Serverless Deployment Guide

**Status:** Implementation complete through Phase 6. Ready for testing.

**Current State:**
- ✅ AWS credentials configured (`~/.aws/credentials` profile: `metads`)
- ✅ All tools installed (AWS CLI, Terraform, Node.js)
- ✅ Terraform code complete (never applied)
- ✅ Lambda handlers implemented (stubs exist in `lambda_stubs/`)
- ✅ S3 backend commented out (using local state for now)
- ❌ No AWS resources created yet
- ❌ Secrets not populated
- ❌ Real Lambda code not packaged

---

## Prerequisites Checklist

Before starting deployment, verify:

```bash
# AWS CLI configured
aws sts get-caller-identity --profile metads
# Should return: account ID and IAM user ARN

# Terraform installed
terraform version
# Should be: v1.5.0 or higher

# Node.js installed
node --version
npm --version
# Should be: Node 18+ and npm 9+

# Python 3.11
python3 --version
# Should be: 3.11.x
```

---

## Deployment Phases

### Phase A: One-Time Secrets Setup (~10 minutes)

**IMPORTANT:** Do this **AFTER** terraform apply, not before. Terraform creates the secret containers but cannot populate the values.

#### A.1: Get Your Credentials

**Meta API Token:**
1. Go to [Facebook Developers](https://developers.facebook.com/apps)
2. Create a new app (type: Business)
3. Add product: "Marketing API"
4. Go to Graph API Explorer
5. Generate a long-lived access token (60 days)
   - Permissions needed: `ads_read`, `pages_read_engagement`
6. Copy the token

**Clerk Keys:**
1. Go to [Clerk Dashboard](https://dashboard.clerk.com)
2. Select your application
3. Navigate to **API Keys**
4. Copy:
   - Publishable Key (starts with `pk_test_` or `pk_live_`)
   - Secret Key (starts with `sk_test_` or `sk_live_`)
5. Navigate to **Webhooks**
6. Copy the Signing Secret (starts with `whsec_`)

#### A.2: Populate Secrets (AFTER terraform apply)

**Option A: Use the helper script (recommended)**

The script reads `FB_ACCESS_TOKEN` from `.env` and prompts for Clerk keys:

```bash
cd aws_lambda_deploy
./scripts/populate-secrets.sh dev
```

**Option B: Manual**

```bash
# 1. Meta API token (get from .env file)
FB_TOKEN=$(grep FB_ACCESS_TOKEN .env | cut -d= -f2 | tr -d '"')

aws secretsmanager put-secret-value \
  --profile metads \
  --secret-id "metaads/dev/meta-api" \
  --secret-string "{\"access_token\":\"${FB_TOKEN}\"}"

# 2. Clerk keys
aws secretsmanager put-secret-value \
  --profile metads \
  --secret-id "metaads/dev/clerk" \
  --secret-string '{
    "publishable_key": "pk_test_...",
    "secret_key":      "sk_test_...",
    "webhook_secret":  "whsec_..."
  }'
```

**Verification:**

```bash
# Verify secrets exist
aws secretsmanager list-secrets --profile metads \
  --query 'SecretList[?starts_with(Name, `metaads/dev`)].Name'

# Should show:
# [
#   "metaads/dev/clerk",
#   "metaads/dev/meta-api"
# ]
```

---

### Phase B: Infrastructure Deployment (~8 minutes)

#### B.1: Initialize Terraform

```bash
cd aws_lambda_deploy/infra

# First-time init (downloads AWS provider)
terraform init
```

**Expected output:**
```
Terraform has been successfully initialized!
```

#### B.2: Preview Changes

```bash
# See what will be created (~30 resources)
terraform plan -var-file=dev.tfvars
```

**Expected resources:**
- 1 DynamoDB table (`metaads-dev`)
- 2 S3 buckets (frontend hosting + CloudFront logs)
- 1 CloudFront distribution
- 7 Lambda functions + 1 shared layer
- 1 API Gateway HTTP API
- ~10 IAM roles and policies
- 2 Secrets Manager secrets (containers only, no values yet)
- ~5 CloudWatch log groups

#### B.3: Apply Infrastructure

```bash
# Create everything in AWS
terraform apply -var-file=dev.tfvars

# Type "yes" when prompted
```

**Expected duration:** 3-5 minutes

**IMPORTANT:** Save the outputs! You'll need them for the next steps:

```bash
# View outputs
terraform output

# Should show:
# api_gateway_url          = "https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com"
# cloudfront_domain_name   = "d1xxxxxxxxx.cloudfront.net"
# frontend_bucket_name     = "metaads-dev-frontend-..."
# cloudfront_distribution_id = "E1XXXXXXXXXX"
# frontend_url             = "https://d1xxxxxxxxx.cloudfront.net"
```

**Copy these values** — you'll need them for CORS and frontend deployment.

---

### Phase C: Lock Down CORS (~2 minutes)

After apply, update `dev.tfvars` with the real CloudFront domain:

```bash
cd aws_lambda_deploy/infra

# Edit dev.tfvars
nano dev.tfvars
```

Add this line with your actual CloudFront domain from the outputs:

```hcl
cors_allow_origins = ["https://d1xxxxxxxxx.cloudfront.net"]
```

Then re-apply (only API Gateway updates, ~10 seconds):

```bash
terraform apply -var-file=dev.tfvars
```

---

### Phase D: Populate Secrets (~5 minutes)

**NOW run the Phase A commands** to populate the secrets with your actual credentials.

See [Phase A.2](#a2-populate-secrets-after-terraform-apply) above.

---

### Phase E: Deploy Real Lambda Handlers (~5 minutes)

Right now the Lambdas are running stub zips (return HTTP 501). Package and upload the real handlers:

#### E.1: Package All Lambdas

```bash
cd aws_lambda_deploy

# Run the packaging script
./scripts/package.sh
```

**Expected output:**
```
[1/8] Packaging shared layer...
  ✓ Shared layer: lambda_stubs/shared_layer.zip (15M)

[2/8] Packaging authorizer handler...
  ✓ authorizer.zip (2.1K)

[3/8] Packaging auth handler...
  ✓ auth.zip (2.3K)

[4/8] Packaging niches handler...
  ✓ niches.zip (3.5K)

[5/8] Packaging ads handler...
  ✓ ads.zip (4.1K)

[6/8] Packaging saved handler...
  ✓ saved.zip (2.5K)

[7/8] Packaging collect_trigger handler...
  ✓ collect_trigger.zip (2.8K)

[8/8] Packaging collect_worker handler...
  ✓ collect_worker.zip (3.2K)

Packaging complete!
```

#### E.2: Deploy to AWS

```bash
# Re-apply Terraform to upload the new ZIPs
cd infra
terraform apply -var-file=dev.tfvars
```

Terraform will detect the new ZIP files and update all Lambda functions.

**Expected duration:** 1-2 minutes

---

### Phase F: Deploy Frontend (~3 minutes)

#### F.1: Create Clerk Keys File

Create a file with your Clerk publishable key (one-time setup):

```bash
cd ../..  # Back to repo root

# Create the dev keys file
echo "VITE_CLERK_PUBLISHABLE_KEY=pk_test_YOUR_KEY_HERE" > frontend/.env.dev.keys
```

**Note:** This file is gitignored and never committed.

#### F.2: Build and Deploy

```bash
# Run the deployment script
./aws_lambda_deploy/scripts/deploy.sh dev
```

**What it does:**
1. Reads Terraform outputs (bucket name, CloudFront distribution ID, API URL)
2. Writes `frontend/.env.production` with the real API URL
3. Builds the Vue 3 app (`npm run build`)
4. Syncs `dist/` to S3
5. Invalidates the CloudFront cache

**Expected output:**
```
[1/5] Reading Terraform outputs...
  S3 bucket:            metaads-dev-frontend-...
  CloudFront dist ID:   E1XXXXXXXXXX
  API Gateway URL:      https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com
  Frontend URL:         https://d1xxxxxxxxx.cloudfront.net

[2/5] Writing frontend/.env.production...
  Clerk key: pk_test_abcd... (truncated)
  Written: frontend/.env.production

[3/5] Building frontend (npm run build)...
  Build complete: 42 files in dist/

[4/5] Uploading to S3...
  Upload complete.

[5/5] Invalidating CloudFront cache...
  Invalidation created: I1XXXXXXXXXX
  (Propagation takes ~30-60 seconds globally)

Deploy complete!
Frontend URL: https://d1xxxxxxxxx.cloudfront.net
```

---

### Phase G: Smoke Test (~10 minutes)

Open your frontend URL from the deploy output.

#### G.1: Basic Functionality

- [ ] **App loads:** https://d1xxxxxxxxx.cloudfront.net shows the Vue app
- [ ] **Clerk sign-in:** Click "Sign In" and authenticate
- [ ] **Create niche:** Add a new niche (e.g., "video editing ai")
  - POST `/api/niches` returns 200
  - Niche appears in the list

#### G.2: Collection Pipeline

- [ ] **Trigger collection:** Click "Collect Now" on a niche
  - POST `/api/niches/{slug}/collect` returns 202
  - Response contains `run_id`
- [ ] **Check status:** View collection runs
  - GET `/api/niches/{slug}/collection-runs` shows the run
  - Status changes from `pending` → `running` → `completed`
- [ ] **Verify ads:** After collection completes
  - Ads appear in the search view
  - Can filter by page, CTA, active status

#### G.3: Ad Management

- [ ] **Search ads:** GET `/api/niches/{slug}/ads/search` returns results
- [ ] **View details:** Click an ad to see full details
- [ ] **Save ad:** Click "Save" button
  - POST `/api/niches/{slug}/ads/{id}/save` returns 200
  - Ad appears in "Saved Ads" view
- [ ] **Unsave ad:** Click "Unsave" in saved list
  - Ad removed from saved list

#### G.4: Check CloudWatch Logs

```bash
# View Lambda logs
aws logs tail /aws/lambda/metaads-dev-niches --profile metads --follow
aws logs tail /aws/lambda/metaads-dev-collect-worker --profile metads --follow

# Check for errors
aws logs filter-pattern ERROR --profile metads \
  --log-group-name-prefix /aws/lambda/metaads-dev
```

---

## Troubleshooting

### Issue: Terraform apply fails with "InvalidParameterException"

**Cause:** Trying to reference secrets that don't exist yet.

**Solution:** Secrets Manager resources create the containers, but you must populate values manually (see Phase D).

---

### Issue: Lambda returns 501 "Not Implemented"

**Cause:** Still using stub ZIPs instead of real handlers.

**Solution:** Run `./scripts/package.sh` then `terraform apply` (Phase E).

---

### Issue: Frontend shows CORS errors

**Cause:** API Gateway is rejecting requests from the CloudFront domain.

**Solution:**
1. Verify `cors_allow_origins` in `dev.tfvars` matches your CloudFront domain
2. Re-run `terraform apply -var-file=dev.tfvars`

**Check:**
```bash
terraform output cloudfront_domain_name
# Should match the domain in cors_allow_origins
```

---

### Issue: Collection returns 500 "Internal Server Error"

**Possible causes:**

1. **Meta API token not set:**
   ```bash
   aws secretsmanager get-secret-value \
     --profile metads \
     --secret-id metaads/dev/meta-api
   ```
   Should return JSON with `access_token`.

2. **Invalid Meta API token:**
   Test the token directly:
   ```bash
   curl "https://graph.facebook.com/v18.0/ads_archive?access_token=YOUR_TOKEN&search_terms=test&ad_reached_countries=US&fields=id"
   ```
   Should return JSON, not an error.

3. **DynamoDB permissions:**
   Check Lambda execution role has `dynamodb:PutItem`, `dynamodb:Query`, etc.

---

### Issue: Clerk authentication fails

**Possible causes:**

1. **Wrong publishable key in frontend:**
   ```bash
   cat frontend/.env.production
   # Verify VITE_CLERK_PUBLISHABLE_KEY matches your Clerk dashboard
   ```

2. **Webhook secret mismatch:**
   ```bash
   aws secretsmanager get-secret-value \
     --profile metads \
     --secret-id metaads/dev/clerk \
     --query SecretString --output text | jq
   ```
   Verify `webhook_secret` matches Clerk dashboard.

3. **JWKS verification error:**
   Check Lambda authorizer logs:
   ```bash
   aws logs tail /aws/lambda/metaads-dev-authorizer --profile metads
   ```

---

## Cost Monitoring

After 1 week of testing, verify costs are within projections:

```bash
# Open AWS Cost Explorer
# https://console.aws.amazon.com/cost-management/home

# Filter by:
# - Service: Lambda, DynamoDB, API Gateway, S3, CloudFront
# - Time range: Last 7 days
```

**Expected costs (100 users):**
- Lambda: $0.00 (free tier)
- API Gateway: $0.00 (free tier for 12 months)
- DynamoDB: $0.06
- S3: $0.01
- CloudFront: $0.00 (free tier for 12 months)
- Secrets Manager: $0.80
- **Total: ~$0.87-$1.22/month**

**Alert if costs exceed $5/month** — indicates misconfiguration (e.g., runaway Lambda invocations).

---

## Next Steps After Smoke Test

Once smoke tests pass:

1. **Migrate production data:**
   ```bash
   python scripts/migrate_sqlite_to_dynamodb.py
   ```

2. **Set up monitoring alerts:**
   - Add email to `dev.tfvars`: `alarm_email = "your-email@example.com"`
   - Re-run `terraform apply`

3. **Enable S3 backend for Terraform state:**
   - Uncomment S3 backend in `infra/main.tf`
   - Run `terraform init -migrate-state`

4. **Set up CI/CD (Phase 9):**
   - GitHub Actions workflow
   - OIDC federation for AWS access
   - Automated deploy on push to `main`

5. **Security hardening (Phase 7):**
   - Implement Meta API global rate-limit counter (Step 7.5)
   - Implement Meta API token auto-renewal (Step 7.6)
   - Review IAM policies (remove `*` resources)

---

## Summary of Commands

**Initial Setup:**
```bash
# 1. Init Terraform
cd aws_lambda_deploy/infra
terraform init

# 2. Apply infrastructure
terraform apply -var-file=dev.tfvars

# 3. Populate secrets (AFTER apply)
aws secretsmanager put-secret-value --profile metads \
  --secret-id "metaads/dev/meta-api" \
  --secret-string '{"access_token":"YOUR_TOKEN"}'

aws secretsmanager put-secret-value --profile metads \
  --secret-id "metaads/dev/clerk" \
  --secret-string '{"publishable_key":"pk_test_...","secret_key":"sk_test_...","webhook_secret":"whsec_..."}'

# 4. Update CORS
# Edit dev.tfvars to add cors_allow_origins
terraform apply -var-file=dev.tfvars

# 5. Package Lambda code
cd ..
./scripts/package.sh

# 6. Deploy Lambda code
cd infra
terraform apply -var-file=dev.tfvars

# 7. Create Clerk keys file
cd ../..
echo "VITE_CLERK_PUBLISHABLE_KEY=pk_test_..." > frontend/.env.dev.keys

# 8. Deploy frontend
./aws_lambda_deploy/scripts/deploy.sh dev
```

**Regular Deployment (after initial setup):**
```bash
# Update Lambda code
cd aws_lambda_deploy
./scripts/package.sh
cd infra
terraform apply -var-file=dev.tfvars

# Update frontend
cd ../..
./aws_lambda_deploy/scripts/deploy.sh dev
```

---

## Support

If you encounter issues not covered in this guide:

1. **Check CloudWatch Logs:**
   ```bash
   aws logs tail /aws/lambda/metaads-dev-FUNCTION_NAME --profile metads --follow
   ```

2. **Check Terraform state:**
   ```bash
   cd aws_lambda_deploy/infra
   terraform show
   ```

3. **Verify AWS resources:**
   ```bash
   # List Lambda functions
   aws lambda list-functions --profile metads --query 'Functions[?starts_with(FunctionName, `metaads-dev`)].FunctionName'

   # Check DynamoDB table
   aws dynamodb describe-table --profile metads --table-name metaads-dev

   # Check API Gateway
   aws apigatewayv2 get-apis --profile metads
   ```

---

**Good luck with your deployment! 🚀**
