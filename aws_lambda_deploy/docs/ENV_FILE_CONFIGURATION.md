# Environment File Configuration

This document explains how the deployment scripts read credentials from your `.env` files.

---

## Overview

The deployment scripts automatically read credentials from two `.env` files:

1. **Root `.env`** (`/Users/emadruga/proj/metaAds/.env`) - Backend secrets
2. **Frontend `.env`** (`/Users/emadruga/proj/metaAds/frontend/.env`) - Frontend config

This eliminates the need to manually enter credentials during deployment.

---

## File Locations and Purpose

### 1. Root `.env` (Backend Secrets)

**Location:** `/Users/emadruga/proj/metaAds/.env`

**Used for:**
- Meta API access token (required)
- Clerk secret key (optional - will prompt if missing)
- Clerk webhook secret (optional - will prompt if missing)

**Example:**
```bash
# Meta API (Required)
FB_ACCESS_TOKEN="EAABwz..."

# Clerk Backend Secrets (Optional)
CLERK_SECRET_KEY="sk_test_..."
CLERK_WEBHOOK_SECRET="whsec_..."
```

### 2. Frontend `.env` (Frontend Config)

**Location:** `/Users/emadruga/proj/metaAds/frontend/.env`

**Used for:**
- Clerk publishable key (public, safe to commit)
- API URL (for local development)

**Example:**
```bash
# API URL
VITE_API_URL=http://localhost:5001/api

# Clerk Authentication (Publishable Key - Public)
VITE_CLERK_PUBLISHABLE_KEY=pk_test_...
```

---

## How Scripts Read These Files

### Automated Deployment (`deploy-all.sh`)

When you run `./scripts/deploy-all.sh dev`, it:

1. **Reads `FB_ACCESS_TOKEN`** from root `.env`
   - If found → uses it automatically
   - If missing → shows error with instructions

2. **Reads `VITE_CLERK_PUBLISHABLE_KEY`** from `frontend/.env`
   - If found → uses it automatically
   - If missing → prompts for input

3. **Reads `CLERK_SECRET_KEY` and `CLERK_WEBHOOK_SECRET`** from root `.env`
   - If found → uses them automatically
   - If missing → prompts for input

### Manual Secret Population (`populate-secrets.sh`)

When you run `./scripts/populate-secrets.sh dev`, it does the same credential loading as above.

---

## Current Configuration

Based on your files:

✅ **Root `.env`** has:
- `FB_ACCESS_TOKEN` ✓

❌ **Root `.env`** missing (will prompt during deployment):
- `CLERK_SECRET_KEY`
- `CLERK_WEBHOOK_SECRET`

✅ **Frontend `.env`** has:
- `VITE_CLERK_PUBLISHABLE_KEY` ✓

---

## Option 1: Add Clerk Secrets to Root `.env` (Recommended)

To avoid prompts during deployment, add these lines to your root `.env`:

```bash
# Add to /Users/emadruga/proj/metaAds/.env

# Clerk Backend Secrets
CLERK_SECRET_KEY="sk_test_YOUR_SECRET_KEY_HERE"
CLERK_WEBHOOK_SECRET="whsec_YOUR_WEBHOOK_SECRET_HERE"
```

**Where to get these:**
1. Go to https://dashboard.clerk.com
2. Select your application
3. **API Keys** → Copy "Secret Key" (starts with `sk_test_`)
4. **Webhooks** → Copy "Signing Secret" (starts with `whsec_`)

Then during deployment, the script will load them automatically.

---

## Option 2: Manual Input During Deployment

If you don't add them to `.env`, the script will prompt you:

```bash
./scripts/deploy-all.sh dev

# Output:
# ➜ Step 2: Populating Secrets Manager...
# ✓ Loaded FB_ACCESS_TOKEN from .env (141 chars)
# ✓ Loaded VITE_CLERK_PUBLISHABLE_KEY from frontend/.env
# ⚠ Clerk secret key not found in .env
# Get your secret key from: https://dashboard.clerk.com → API Keys
# Secret key (sk_test_...): █
```

---

## Security Notes

### ✅ Safe to Add to `.env` (Gitignored)

These files are in `.gitignore` and **never committed**:
- `/Users/emadruga/proj/metaAds/.env`
- `/Users/emadruga/proj/metaAds/frontend/.env`

### ⚠️ Never Commit These Secrets

The `.gitignore` already protects:
```gitignore
.env
.env.*
!.env.example
!.env.template
```

### 🔒 Where Secrets Are Stored in AWS

After running the deployment scripts, secrets are stored in:
- **AWS Secrets Manager** (encrypted at rest with KMS)
- Lambda functions read from Secrets Manager at runtime
- Never stored in Lambda environment variables

---

## Verification

After populating secrets, verify they're in AWS:

```bash
# Check Meta API secret
aws secretsmanager get-secret-value \
  --profile metads \
  --secret-id metaads/dev/meta-api \
  --query SecretString \
  --output text | jq

# Expected output:
# {
#   "access_token": "EAABwz..."
# }

# Check Clerk secret
aws secretsmanager get-secret-value \
  --profile metads \
  --secret-id metaads/dev/clerk \
  --query SecretString \
  --output text | jq

# Expected output:
# {
#   "publishable_key": "pk_test_...",
#   "secret_key": "sk_test_...",
#   "webhook_secret": "whsec_..."
# }
```

---

## Troubleshooting

### Error: "FB_ACCESS_TOKEN not found in .env file"

**Cause:** Root `.env` doesn't have `FB_ACCESS_TOKEN`

**Solution:**
```bash
echo 'FB_ACCESS_TOKEN="YOUR_TOKEN_HERE"' >> .env
```

### Error: "VITE_CLERK_PUBLISHABLE_KEY not found"

**Cause:** Frontend `.env` doesn't have the Clerk publishable key

**Solution:**
```bash
echo 'VITE_CLERK_PUBLISHABLE_KEY="pk_test_..."' >> frontend/.env
```

### Script Prompts for Clerk Secrets

**Cause:** `CLERK_SECRET_KEY` and `CLERK_WEBHOOK_SECRET` not in root `.env`

**Solution:** Either:
1. Add them to root `.env` (see Option 1 above)
2. Enter them when prompted (they'll be saved to AWS Secrets Manager)

---

## Template Files

Use these as reference:

- **Root:** `/Users/emadruga/proj/metaAds/.env.template`
- **Frontend:** (already configured in `frontend/.env`)

Copy and fill in your values:

```bash
# Copy template to .env
cp .env.template .env

# Edit with your credentials
nano .env
```

---

## Summary

**Fully automated deployment** (no prompts):
1. Add `FB_ACCESS_TOKEN` to root `.env` ✅ (already done)
2. Add `CLERK_SECRET_KEY` to root `.env` (optional)
3. Add `CLERK_WEBHOOK_SECRET` to root `.env` (optional)
4. Keep `VITE_CLERK_PUBLISHABLE_KEY` in `frontend/.env` ✅ (already done)

Then run:
```bash
./aws_lambda_deploy/scripts/deploy-all.sh dev
```

The script will load all credentials automatically!
