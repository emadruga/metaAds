# MetaAds Serverless AWS Deployment

Complete serverless infrastructure for the MetaAds competitive intelligence application, deployed on AWS using Terraform.

## Current Status

**Implementation:** ✅ Complete through Phase 6 (Frontend Deployment)

**Deployment Status:** ❌ Not deployed yet

**What exists:**
- ✅ All Terraform infrastructure code
- ✅ All 7 Lambda function handlers
- ✅ DynamoDB repository layer
- ✅ Shared Lambda layer with dependencies
- ✅ Deployment scripts (package, deploy, test)
- ✅ Comprehensive documentation

**What's needed to start:**
- Your Facebook App access token (Meta API)
- Your Clerk API keys (authentication)
- Run the deployment commands (see Quick Start below)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                             │
│  Vue 3 + Clerk → S3 + CloudFront (HTTPS)                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    API Gateway HTTP API                      │
│  CORS + Throttling + Lambda Authorizer (Clerk JWT)          │
└──────────────────────┬──────────────────────────────────────┘
                       │
         ┌─────────────┴─────────────┐
         ▼                           ▼
┌──────────────────┐        ┌──────────────────┐
│  API Lambdas     │        │ Collection       │
│  (7 functions)   │        │ Pipeline         │
│                  │        │                  │
│ • Authorizer     │        │ • Trigger        │
│ • Auth           │        │ • Worker (async) │
│ • Niches         │        │   - Meta API     │
│ • Ads            │        │   - DynamoDB     │
│ • Saved          │        └──────────────────┘
└──────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                    DynamoDB Single Table                     │
│  Users, Niches, Ads, Pages, Collection Runs, Rate Limits    │
│  PAY_PER_REQUEST + PITR + 2 GSIs                            │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Secrets Manager                           │
│  • Meta API access token                                    │
│  • Clerk keys (publishable, secret, webhook)                │
└─────────────────────────────────────────────────────────────┘
```

**Key Features:**
- **Fully serverless:** No EC2 instances, no containers to manage
- **Pay-per-use:** ~$0.87-$1.22/month for 100 users (mostly Secrets Manager cost)
- **Auto-scaling:** Lambda + DynamoDB scale automatically
- **Secure:** IAM least-privilege, HTTPS everywhere, encrypted at rest
- **Observable:** CloudWatch logs + alarms, cost monitoring

---

## Quick Start

**Time to deploy:** ~30 minutes (first time)

### Prerequisites

Ensure you have:
- AWS CLI configured with profile `metads`
- Terraform v1.5+
- Node.js 18+
- Python 3.11
- Facebook App access token
- Clerk API keys

### 1. Deploy Infrastructure

```bash
cd aws_lambda_deploy/infra
terraform init
terraform apply -var-file=dev.tfvars
# Type "yes" when prompted
```

**Save the outputs!** You'll need them for the next steps.

### 2. Populate Secrets

**IMPORTANT:** Run these AFTER `terraform apply`.

The helper script reads `FB_ACCESS_TOKEN` from `.env` and prompts for Clerk keys:

```bash
cd aws_lambda_deploy
./scripts/populate-secrets.sh dev
```

Or manually:

```bash
# Meta API token (reads from .env)
FB_TOKEN=$(grep FB_ACCESS_TOKEN .env | cut -d= -f2 | tr -d '"')
aws secretsmanager put-secret-value \
  --profile metads \
  --secret-id "metaads/dev/meta-api" \
  --secret-string "{\"access_token\":\"${FB_TOKEN}\"}"

# Clerk keys
aws secretsmanager put-secret-value \
  --profile metads \
  --secret-id "metaads/dev/clerk" \
  --secret-string '{
    "publishable_key": "pk_test_...",
    "secret_key":      "sk_test_...",
    "webhook_secret":  "whsec_..."
  }'
```

### 3. Update CORS

Edit `infra/dev.tfvars` and add:

```hcl
cors_allow_origins = ["https://YOUR_CLOUDFRONT_DOMAIN"]
```

Then re-apply:

```bash
terraform apply -var-file=dev.tfvars
```

### 4. Package and Deploy Lambda Code

```bash
cd ..  # Back to aws_lambda_deploy/
./scripts/package.sh
cd infra
terraform apply -var-file=dev.tfvars
```

### 5. Deploy Frontend

```bash
cd ../..  # Back to repo root

# Create Clerk keys file
echo "VITE_CLERK_PUBLISHABLE_KEY=pk_test_..." > frontend/.env.dev.keys

# Deploy
./aws_lambda_deploy/scripts/deploy.sh dev
```

### 6. Test

```bash
# Automated tests
./aws_lambda_deploy/scripts/test.sh dev

# Manual smoke test
# Open the frontend URL from the deploy output
# Sign in, create a niche, trigger collection, search ads
```

---

## Documentation

### For Deployment

- **[Quick Start Checklist](docs/QUICK_START_CHECKLIST.md)** — Step-by-step deployment checklist
- **[Deployment Guide](docs/DEPLOYMENT_GUIDE.md)** — Comprehensive deployment instructions with troubleshooting
- **[Migration Plan](docs/PLAN_MIGRATE_TO_SERVERLESS.md)** — Full architecture and implementation details

### For Understanding

- **[DynamoDB Performance Management](docs/DYNAMODB_PERFORMANCE_MANAGEMENT.md)** — How to optimize DynamoDB queries
- **Terraform Modules:**
  - `infra/main.tf` — Infrastructure overview
  - `infra/dynamodb.tf` — DynamoDB table configuration
  - `infra/lambda.tf` — Lambda functions and layers
  - `infra/api_gateway.tf` — API Gateway HTTP API
  - `infra/s3_cloudfront.tf` — Frontend hosting

### For Development

- **Lambda Handlers:**
  - `lambda_src/authorizer/` — Clerk JWT verification
  - `lambda_src/auth/` — Authentication endpoints
  - `lambda_src/niches/` — Niche CRUD
  - `lambda_src/ads/` — Ad search and filtering
  - `lambda_src/saved/` — Saved ads management
  - `lambda_src/collect_trigger/` — Collection initiation
  - `lambda_src/collect_worker/` — Async Meta API collection

- **Shared Code:**
  - `lambda_layers/shared/python/` — DynamoDB repos, utilities, Meta API client

---

## Project Structure

```
aws_lambda_deploy/
├── docs/                               # Documentation
│   ├── QUICK_START_CHECKLIST.md        # ⭐ Start here
│   ├── DEPLOYMENT_GUIDE.md             # Full deployment instructions
│   ├── PLAN_MIGRATE_TO_SERVERLESS.md   # Architecture design
│   └── DYNAMODB_PERFORMANCE_MANAGEMENT.md
│
├── infra/                              # Terraform infrastructure
│   ├── main.tf                         # Provider and backend config
│   ├── variables.tf                    # Input variables
│   ├── outputs.tf                      # Output values
│   ├── dev.tfvars                      # Dev environment config
│   ├── dynamodb.tf                     # DynamoDB table
│   ├── lambda.tf                       # Lambda functions + layer
│   ├── api_gateway.tf                  # API Gateway HTTP API
│   ├── s3_cloudfront.tf                # Frontend hosting
│   ├── iam.tf                          # IAM roles and policies
│   ├── secrets.tf                      # Secrets Manager
│   └── monitoring.tf                   # CloudWatch alarms
│
├── lambda_src/                         # Lambda handler code
│   ├── authorizer/handler.py           # Clerk JWT authorizer
│   ├── auth/handler.py                 # Auth endpoints
│   ├── niches/handler.py               # Niche CRUD
│   ├── ads/handler.py                  # Ad search/filter
│   ├── saved/handler.py                # Saved ads
│   ├── collect_trigger/handler.py      # Collection trigger
│   └── collect_worker/handler.py       # Async collector
│
├── lambda_layers/                      # Shared Lambda layer
│   └── shared/
│       ├── requirements.txt            # Python dependencies
│       └── python/                     # Shared code
│           ├── app/dynamodb/           # DynamoDB repos
│           ├── app/utils/              # Utility functions
│           ├── meta_api_collector.py   # Meta API client
│           └── ad_parser.py            # Ad parsing logic
│
├── lambda_stubs/                       # Packaged Lambda ZIPs
│   ├── shared_layer.zip                # (generated by package.sh)
│   ├── authorizer.zip
│   ├── auth.zip
│   ├── niches.zip
│   ├── ads.zip
│   ├── saved.zip
│   ├── collect_trigger.zip
│   └── collect_worker.zip
│
└── scripts/                            # Automation scripts
    ├── package.sh                      # Package Lambda code
    ├── deploy.sh                       # Deploy frontend
    └── test.sh                         # Smoke tests
```

---

## Cost Breakdown (100 Users)

| Service | Monthly Usage | Cost | Notes |
|---------|--------------|------|-------|
| Lambda | ~31K invocations, ~50K GB-s | $0.00 | Within free tier |
| API Gateway (HTTP) | ~30K requests | $0.00-$0.35 | 1M free (12 months) |
| DynamoDB (On-Demand) | 25K writes, 100K reads | $0.06 | Within always-free tier |
| S3 | ~50MB storage, 10K requests | $0.01 | |
| CloudFront | ~1GB transfer | $0.00 | Within free tier (12 months) |
| Secrets Manager | 2 secrets | $0.80 | $0.40/secret/month |
| CloudWatch Logs | <1GB | $0.00 | Within free tier |
| **TOTAL** | | **$0.87-$1.22/mo** | **$1.50-$2.50 after free tier expiry** |

**Cost protection:**
- Lambda concurrency limits (prevent runaway costs)
- API Gateway throttling (100 burst / 50 sustained)
- DynamoDB on-demand pricing (no provisioned capacity)

---

## Security

**Encryption:**
- ✅ DynamoDB encrypted at rest (AWS KMS)
- ✅ Secrets Manager encrypted at rest
- ✅ S3 encrypted at rest (AES-256)
- ✅ TLS 1.2+ for all data in transit

**Access Control:**
- ✅ IAM least-privilege roles (no `*` resources)
- ✅ Lambda authorizer validates Clerk JWTs with JWKS
- ✅ API Gateway CORS restricted to frontend domain
- ✅ S3 buckets block all public access (CloudFront OAC only)

**Monitoring:**
- ✅ CloudWatch alarms on Lambda errors, DynamoDB throttling, API 5xx
- ✅ CloudWatch Logs with 7-day retention
- ✅ Cost anomaly detection in AWS Cost Explorer

**Compliance:**
- ✅ Point-in-time recovery enabled on DynamoDB
- ✅ S3 versioning enabled
- ✅ CloudTrail logs all API calls (Secrets Manager)

---

## Common Tasks

### Update Lambda Code

```bash
cd aws_lambda_deploy
./scripts/package.sh
cd infra
terraform apply -var-file=dev.tfvars
```

### Update Frontend

```bash
./aws_lambda_deploy/scripts/deploy.sh dev
```

### View Lambda Logs

```bash
# Real-time logs
aws logs tail /aws/lambda/metaads-dev-collect-worker --profile metads --follow

# Search for errors
aws logs filter-log-events \
  --profile metads \
  --log-group-name /aws/lambda/metaads-dev-niches \
  --filter-pattern ERROR \
  --start-time $(date -u -d '1 hour ago' +%s)000
```

### Check DynamoDB Data

```bash
# Scan table (first 10 items)
aws dynamodb scan \
  --profile metads \
  --table-name metaads-dev \
  --max-items 10

# Query user's niches
aws dynamodb query \
  --profile metads \
  --table-name metaads-dev \
  --key-condition-expression "PK = :pk AND begins_with(SK, :sk)" \
  --expression-attribute-values '{
    ":pk": {"S": "USER#user-123"},
    ":sk": {"S": "NICHE#"}
  }'
```

### Rotate Meta API Token

```bash
# Update the secret
aws secretsmanager put-secret-value \
  --profile metads \
  --secret-id metaads/dev/meta-api \
  --secret-string '{"access_token":"NEW_TOKEN_HERE"}'

# Lambdas automatically pick up the new value on next invocation
```

### Monitor Costs

```bash
# Open AWS Cost Explorer
# https://console.aws.amazon.com/cost-management/home

# Filter by service: Lambda, DynamoDB, API Gateway, S3, CloudFront
# Time range: Last 7 days
```

---

## Troubleshooting

See [DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md#troubleshooting) for detailed troubleshooting steps.

**Quick fixes:**

**CORS errors:**
```bash
# Update dev.tfvars with CloudFront domain
# Then: terraform apply -var-file=dev.tfvars
```

**Lambda returns 501:**
```bash
./scripts/package.sh
cd infra && terraform apply -var-file=dev.tfvars
```

**Collection fails:**
```bash
# Check Meta API secret is populated
aws secretsmanager get-secret-value --profile metads --secret-id metaads/dev/meta-api
```

---

## Next Steps After Deployment

1. **Monitor for 1 week:**
   - Check AWS Cost Explorer (should be <$2/month)
   - Review CloudWatch logs for errors
   - Test all user flows (create niche, collect, search, save)

2. **Security hardening (Phase 7):**
   - [ ] Implement Meta API global rate-limit counter (Step 7.5)
   - [ ] Implement Meta API token auto-renewal (Step 7.6)
   - [ ] Review IAM policies (remove any overly broad permissions)
   - [ ] Set up CloudWatch alarms for email notifications

3. **Production readiness:**
   - [ ] Set up S3 backend for Terraform state
   - [ ] Implement CI/CD with GitHub Actions (Phase 9)
   - [ ] Create `prod` environment (new tfvars)
   - [ ] Set up domain name with Route 53 + ACM certificate

4. **Scale considerations:**
   - [ ] Token management strategy (see migration plan for options 2-3)
   - [ ] DynamoDB performance optimization (add GSIs if needed)
   - [ ] CloudFront custom domain and cache optimization

---

## Support

**Issues?**
1. Check [DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md#troubleshooting)
2. Review CloudWatch logs for errors
3. Run `./scripts/test.sh dev` for automated diagnostics

**Questions?**
- Architecture details: [PLAN_MIGRATE_TO_SERVERLESS.md](docs/PLAN_MIGRATE_TO_SERVERLESS.md)
- DynamoDB queries: [DYNAMODB_PERFORMANCE_MANAGEMENT.md](docs/DYNAMODB_PERFORMANCE_MANAGEMENT.md)

---

**Ready to deploy? See [Quick Start Checklist](docs/QUICK_START_CHECKLIST.md)!**
