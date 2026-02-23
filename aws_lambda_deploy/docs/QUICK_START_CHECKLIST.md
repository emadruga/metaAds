# MetaAds Serverless - Quick Start Checklist

**Current State:** All code implemented. No AWS resources created yet. Ready to deploy.

---

## Pre-Deployment Checklist

- [ ] AWS credentials configured (`aws sts get-caller-identity --profile metads` works)
- [ ] Terraform installed (v1.5+)
- [ ] Node.js 18+ and npm installed
- [ ] Python 3.11 installed
- [ ] Have Facebook App access token ready
- [ ] Have Clerk API keys ready (publishable, secret, webhook secret)

---

## Deployment Steps (First Time)

### 1. Initialize Terraform (2 min)

```bash
cd aws_lambda_deploy/infra
terraform init
terraform plan -var-file=dev.tfvars  # Preview ~30 resources
```

- [ ] `terraform init` succeeds
- [ ] `terraform plan` shows ~30 resources to create

### 2. Deploy Infrastructure (5 min)

```bash
terraform apply -var-file=dev.tfvars
# Type "yes" when prompted
```

- [ ] Apply completes successfully
- [ ] Save outputs (API Gateway URL, CloudFront domain, S3 bucket name)

### 3. Populate Secrets (3 min)

**IMPORTANT:** Run these AFTER terraform apply, not before.

The script will read `FB_ACCESS_TOKEN` from your `.env` file and prompt for Clerk keys:

```bash
cd aws_lambda_deploy

# Option A: Use the helper script (recommended)
./scripts/populate-secrets.sh dev

# Option B: Manual (if you prefer)
aws secretsmanager put-secret-value \
  --profile metads \
  --secret-id "metaads/dev/meta-api" \
  --secret-string '{"access_token":"YOUR_FB_ACCESS_TOKEN_FROM_ENV"}'

aws secretsmanager put-secret-value \
  --profile metads \
  --secret-id "metaads/dev/clerk" \
  --secret-string '{
    "publishable_key": "pk_test_...",
    "secret_key":      "sk_test_...",
    "webhook_secret":  "whsec_..."
  }'
```

- [ ] FB_ACCESS_TOKEN exists in `.env` file
- [ ] Meta API secret populated
- [ ] Clerk secret populated
- [ ] Verification: `aws secretsmanager list-secrets --profile metads` shows both secrets

### 4. Lock Down CORS (2 min)

```bash
cd aws_lambda_deploy/infra

# Edit dev.tfvars
nano dev.tfvars
```

Add this line with your CloudFront domain from step 2 outputs:

```hcl
cors_allow_origins = ["https://d1xxxxxxxxx.cloudfront.net"]
```

```bash
terraform apply -var-file=dev.tfvars
```

- [ ] `cors_allow_origins` updated in dev.tfvars
- [ ] Terraform re-applied successfully

### 5. Package and Deploy Lambda Code (5 min)

```bash
cd aws_lambda_deploy

# Package all handlers
./scripts/package.sh
```

- [ ] Script completes successfully
- [ ] 8 ZIP files created in `lambda_stubs/`

```bash
# Upload to AWS
cd infra
terraform apply -var-file=dev.tfvars
```

- [ ] Terraform detects ZIP changes and updates Lambdas
- [ ] All 7 Lambda functions updated

### 6. Create Clerk Keys File (1 min)

```bash
cd ../..  # Back to repo root

echo "VITE_CLERK_PUBLISHABLE_KEY=pk_test_YOUR_KEY_HERE" > frontend/.env.dev.keys
```

- [ ] File created: `frontend/.env.dev.keys`
- [ ] Contains correct Clerk publishable key

### 7. Deploy Frontend (3 min)

```bash
./aws_lambda_deploy/scripts/deploy.sh dev
```

- [ ] Build completes successfully
- [ ] Files uploaded to S3
- [ ] CloudFront cache invalidated
- [ ] Frontend URL displayed

---

## Smoke Test Checklist

Open the frontend URL from step 7 output.

### Basic Functionality

- [ ] App loads (Vue app appears)
- [ ] Clerk sign-in works
- [ ] Can create a niche
- [ ] Niche appears in list

### Collection Pipeline

- [ ] Click "Collect Now" on a niche
- [ ] Returns 202 with `run_id`
- [ ] Collection status shows in UI
- [ ] After ~30-60 seconds, status changes to `completed`
- [ ] Ads appear in search view

### Ad Management

- [ ] Search returns ads
- [ ] Can filter by page/CTA/status
- [ ] Can view ad details
- [ ] Can save an ad
- [ ] Saved ad appears in "Saved Ads" view
- [ ] Can unsave an ad

### Backend Verification

```bash
# Check Lambda logs (no errors)
aws logs tail /aws/lambda/metaads-dev-collect-worker --profile metads --follow

# Check DynamoDB (has data)
aws dynamodb scan --profile metads --table-name metaads-dev --max-items 5
```

- [ ] No Lambda errors in CloudWatch
- [ ] DynamoDB contains ads/niches/users
- [ ] API Gateway logs show 200 responses

---

## Quick Troubleshooting

### Frontend shows CORS error

**Fix:**
```bash
cd aws_lambda_deploy/infra
# Edit dev.tfvars: cors_allow_origins = ["https://YOUR_CLOUDFRONT_DOMAIN"]
terraform apply -var-file=dev.tfvars
```

### Lambda returns 501 "Not Implemented"

**Fix:**
```bash
cd aws_lambda_deploy
./scripts/package.sh
cd infra
terraform apply -var-file=dev.tfvars
```

### Collection fails with 500 error

**Check Meta API token:**
```bash
aws secretsmanager get-secret-value --profile metads --secret-id metaads/dev/meta-api
# Should return JSON with access_token

# Test token
curl "https://graph.facebook.com/v18.0/ads_archive?access_token=YOUR_TOKEN&search_terms=test&ad_reached_countries=US&fields=id"
# Should return JSON, not error
```

### Clerk authentication fails

**Check keys:**
```bash
cat frontend/.env.production
# Verify VITE_CLERK_PUBLISHABLE_KEY is correct

aws secretsmanager get-secret-value --profile metads --secret-id metaads/dev/clerk
# Verify webhook_secret matches Clerk dashboard
```

---

## Post-Deployment Tasks

After smoke tests pass:

- [ ] Add alarm email to `dev.tfvars`
- [ ] Re-apply Terraform
- [ ] Set up S3 backend for Terraform state
- [ ] Implement Meta API rate-limit counter (Phase 7.5)
- [ ] Implement Meta API token auto-renewal (Phase 7.6)
- [ ] Monitor costs in AWS Cost Explorer (should be <$2/month)

---

## Regular Deployment (After First Time)

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

## Emergency Rollback

### Lambda Code

```bash
# Terraform stores previous versions
cd aws_lambda_deploy/infra
terraform state list  # Find Lambda resource names
terraform taint aws_lambda_function.FUNCTION_NAME
terraform apply -var-file=dev.tfvars
```

### Frontend

```bash
# S3 versioning enabled - restore previous version
aws s3api list-object-versions \
  --profile metads \
  --bucket BUCKET_NAME \
  --prefix index.html

# Restore specific version
aws s3api copy-object \
  --profile metads \
  --bucket BUCKET_NAME \
  --copy-source BUCKET_NAME/index.html?versionId=VERSION_ID \
  --key index.html
```

### DynamoDB

```bash
# Point-in-time recovery enabled
aws dynamodb restore-table-to-point-in-time \
  --profile metads \
  --source-table-name metaads-dev \
  --target-table-name metaads-dev-restored \
  --restore-date-time $(date -u -v-1H +%Y-%m-%dT%H:%M:%SZ)
```

---

## Resources

- **Full Guide:** [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)
- **Architecture Plan:** [PLAN_MIGRATE_TO_SERVERLESS.md](./PLAN_MIGRATE_TO_SERVERLESS.md)
- **AWS Console:** https://console.aws.amazon.com
- **Clerk Dashboard:** https://dashboard.clerk.com
- **Meta Developers:** https://developers.facebook.com

---

**Ready to deploy? Start with Step 1!**
