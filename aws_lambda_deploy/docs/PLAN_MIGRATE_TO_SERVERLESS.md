# MetaAds Serverless AWS Migration Plan

## Table of Contents

- [Context](#context)
- [The Limit of API Calls per Hour: Need for Token Pool Management](#the-limit-of-api-calls-per-hour-need-for-token-pool-management)
  - [Understanding the 200 Calls/Hour Limit](#understanding-the-200-callshour-limit)
  - [Three Token Management Strategies](#three-token-management-strategies)
  - [Recommended Migration Path](#recommended-migration-path)
  - [Implementation Checklist](#implementation-checklist)
  - [Cost Comparison](#cost-comparison)
- [DynamoDB Performance Management: What You Actually Do](#dynamodb-performance-management-what-you-actually-do)
  - [Understanding GSI (Global Secondary Index)](#understanding-gsi-global-secondary-index)
  - [Deep-Dive Reference → DYNAMODB_PERFORMANCE_MANAGEMENT.md](./DYNAMODB_PERFORMANCE_MANAGEMENT.md)
- [Phase 0: AWS Credential Setup (Prerequisite)](#phase-0-aws-credential-setup-prerequisite)
- [Phase 1: Foundation & Infrastructure (Terraform)](#phase-1-foundation--infrastructure-terraform)
- [Phase 2: DynamoDB Data Layer](#phase-2-dynamodb-data-layer)
  - [Step 2.1: Single-Table Design](#step-21-single-table-design)
  - [Step 2.2: DynamoDB Repository Layer](#step-22-dynamodb-repository-layer)
  - [Step 2.3: Data Migration Script](#step-23-data-migration-script)
- [Phase 3: Lambda Functions](#phase-3-lambda-functions)
  - [Step 3.1: Lambda Layer for Shared Code](#step-31-lambda-layer-for-shared-code)
  - [Step 3.2: Lambda Handler Structure](#step-32-lambda-handler-structure)
  - [Step 3.3: Implement Each Handler Group](#step-33-implement-each-handler-group)
  - [Step 3.4: API Gateway HTTP API](#step-34-api-gateway-http-api)
- [Phase 4: Authentication (Clerk JWT in Lambda)](#phase-4-authentication-clerk-jwt-in-lambda)
- [Phase 5: Collection Pipeline (Async)](#phase-5-collection-pipeline-async)
- [Phase 6: Frontend Deployment](#phase-6-frontend-deployment)
- [Phase 7: Security Hardening](#phase-7-security-hardening)
  - [Step 7.5: Meta API Global Rate-Limit Counter](#step-75--meta-api-global-rate-limit-counter)
  - [Step 7.6: Meta API Token Auto-Renewal](#step-76--meta-api-token-auto-renewal)
- [Phase 8: Testing & Validation](#phase-8-testing--validation)
- [Phase 9: CI/CD Pipeline](#phase-9-cicd-pipeline)
- [Cost Projection (100 Users)](#cost-projection-100-users)
- [Security Architecture Summary](#security-architecture-summary)
- [Implementation Timeline](#implementation-timeline)
- [Verification Plan](#verification-plan)

---

## Context

The MetaAds competitive intelligence app currently runs locally: Flask + SQLAlchemy/SQLite backend, Vue 3 + Clerk frontend. AWS feasibility testing (2026-02-21) confirmed all core functionality works on AWS with no blockers. The goal is to migrate `./backend` and `./frontend` into a fully serverless architecture on AWS, targeting **~$2/month for 100 users**, with strong security posture.

The codebase was designed with this migration in mind -- UUIDs for all IDs, ISO8601 string timestamps, DynamoDB access pattern comments already in each model, and `app/utils/ids.py` already has `generate_sort_key()` helpers.

---

## The Limit of API Calls per Hour: Need for Token Pool Management

**CRITICAL CONSTRAINT:** Before diving into AWS architecture, you must understand the Meta Ad Library API rate limit, as it fundamentally shapes how the application scales and determines your token management strategy.

### Understanding the 200 Calls/Hour Limit

**The Hard Limit:**
- **200 API calls per hour per Facebook App access token**
- This is a **hard limit enforced by Meta**, not configurable
- Rate limit is **per Facebook App**, not global
- Each collection query may trigger **2-5 API calls** due to pagination
- Exceeding the limit results in API errors and failed collections

**Why This Matters for MetaAds:**

Let's examine the Agency tier (50 niches × 8 collections/day = 400 collections/day):

```
Scenario 1: All collections run simultaneously (worst case)
- 50 niches × 3 API calls (avg) = 150 API calls in ~5 minutes
- Result: ✅ Within 200/hour limit, but no headroom

Scenario 2: User adds/edits niches during collection window
- 50 scheduled + 10 on-demand = 180 API calls in 10 minutes
- Result: ⚠️ Approaching limit, may fail

Scenario 3: Multiple Agency users on shared token
- 6 Agency users × 50 niches = 300 collections
- If simultaneous: 900 API calls needed
- Result: ❌ Exceeds 200/hour limit by 4.5x
```

**The Solution: Staggered Collections**
```
Instead of bursting all collections at once:
- Distribute 400 daily collections over 24 hours
- Rate: 400 calls / 24 hours = 16.7 calls/hour average
- Peak: Even if 10 niches run simultaneously = 30 calls in 5 min
- Result: ✅ Comfortably within 200/hour limit
```

### Three Token Management Strategies

The strategy you choose depends on your growth stage and scale requirements:

---

#### **Option 1: Shared Access Token (MVP - 0 to 50 users)**

**How It Works:**
- Create **one Facebook App** owned by the platform
- Generate **one access token** (renews every 60 days)
- **All users share the same token** for API calls
- DynamoDB tracks usage across all users to enforce 200/hour global limit

**Scale Limits:**
```
Max users with this approach:
- Agency tier (50 niches, 8×/day): 6 users max
  → 6 users × 50 niches × 8/day × 3 calls = 7,200 calls/day
  → 7,200 / 24 hours = 300 calls/hour peak (exceeds limit if not staggered)
  → With staggering: ✅ 6 Agency users feasible

- Professional tier (10 niches, 4×/day): 117 users max
  → 117 × 10 × 4 × 3 = 14,040 calls/day
  → With staggering: ✅ 117 Professional users feasible

- Starter tier (3 niches, 2×/day): 778 users max
- Free tier (1 niche, 1×/day): 4,680 users max
```

**Pros:**
- ✅ Simplest implementation (just store token in Lambda env var)
- ✅ Zero onboarding friction for users
- ✅ Centralized monitoring and troubleshooting
- ✅ Single token renewal process (60-day automated task)

**Cons:**
- ❌ Limited scale (6 Agency or 117 Professional users max)
- ❌ Single point of failure (token expires → all users affected)
- ❌ Must implement global rate limiting across all users
- ❌ Cannot isolate misbehaving users (one user's burst affects all)

**Implementation (Lambda):**
```python
# lambda/collector/app.py
import os
import time
from boto3.dynamodb.conditions import Key

FB_ACCESS_TOKEN = os.environ['FB_ACCESS_TOKEN']  # Shared token
RATE_LIMIT_TABLE = os.environ['RATE_LIMIT_TABLE']

def check_rate_limit():
    """Check if shared token has API calls remaining this hour."""
    table = dynamodb.Table(RATE_LIMIT_TABLE)

    now = int(time.time())
    hour_start = now - 3600

    # Count API calls in last hour across ALL users
    response = table.query(
        KeyConditionExpression=Key('token_id').eq('SHARED') & Key('timestamp').gt(hour_start)
    )

    call_count = len(response['Items'])

    if call_count >= 190:  # Leave 10 call buffer
        raise RateLimitExceededError(f"Rate limit: {call_count}/200 calls used this hour")

    # Record this API call
    table.put_item(Item={
        'token_id': 'SHARED',
        'timestamp': now,
        'user_id': context.user_id,  # Track which user made the call
        'ttl': now + 7200  # Auto-delete after 2 hours
    })
```

**Token Renewal (EventBridge + Lambda):**
```python
# lambda/token_renewal/app.py
# Triggered every 50 days by EventBridge rule

import requests

def renew_shared_token(event, context):
    """Renew shared FB access token before 60-day expiration."""

    # Exchange short-lived token for long-lived (60 days)
    response = requests.get(
        'https://graph.facebook.com/v18.0/oauth/access_token',
        params={
            'grant_type': 'fb_exchange_token',
            'client_id': os.environ['FB_APP_ID'],
            'client_secret': os.environ['FB_APP_SECRET'],
            'fb_exchange_token': os.environ['FB_ACCESS_TOKEN']
        }
    )

    new_token = response.json()['access_token']

    # Update Lambda environment variable via AWS SDK
    lambda_client = boto3.client('lambda')
    lambda_client.update_function_configuration(
        FunctionName='MetaAdsCollector',
        Environment={
            'Variables': {
                'FB_ACCESS_TOKEN': new_token
            }
        }
    )

    # Send alert to admin
    sns.publish(
        TopicArn=os.environ['ADMIN_ALERT_TOPIC'],
        Message=f"✅ Shared FB token renewed. Expires in 60 days."
    )
```

---

#### **Option 2: Token Pool (Growth - 50 to 500 users)**

**How It Works:**
- Create **5-10 Facebook Apps** owned by the platform
- Generate **one access token per app** (10 tokens total)
- **Distribute users across the token pool** (hash by user_id % pool_size)
- Each token group has isolated 200/hour limit

**Scale Limits:**
```
With 10 tokens in the pool:
- Agency tier: 60 users max (6 per token)
- Professional tier: 1,170 users max (117 per token)
- Starter tier: 7,780 users max
- Free tier: 46,800 users max
```

**Pros:**
- ✅ 10x scale increase (60 Agency or 1,170 Professional users)
- ✅ Fault tolerance (one token fails → only 10% of users affected)
- ✅ Isolated rate limits (users in pool A don't affect pool B)
- ✅ Can rebalance users across pools if one becomes overloaded
- ✅ Still platform-managed (no user onboarding friction)

**Cons:**
- ❌ More complex rate limiting (must track per-token usage)
- ❌ 10x token renewal overhead (10 tokens to renew every 60 days)
- ❌ Uneven distribution if user activity varies widely
- ❌ Still a scale ceiling (60 Agency users max)

**Implementation (DynamoDB Schema):**
```python
# Table: RateLimits
PK: token_id (e.g., "TOKEN_001", "TOKEN_002", ..., "TOKEN_010")
SK: timestamp (Unix timestamp)
Attributes:
  - user_id (which user made this call)
  - ttl (auto-delete after 2 hours)

# Table: UserTokenMapping
PK: user_id
Attributes:
  - token_id (which token pool this user is assigned to)
  - assigned_at (timestamp of assignment)
```

**User-to-Token Assignment:**
```python
# lambda/user_signup/app.py

def assign_user_to_token_pool(user_id):
    """Assign new user to least-loaded token pool."""

    # Option A: Simple hash (deterministic, even distribution)
    token_id = f"TOKEN_{hash(user_id) % 10:03d}"  # TOKEN_000 to TOKEN_009

    # Option B: Least-loaded (dynamic rebalancing)
    token_loads = get_current_token_loads()  # Query RateLimits table
    token_id = min(token_loads, key=token_loads.get)  # Pick least loaded

    # Save mapping
    dynamodb.Table('UserTokenMapping').put_item(Item={
        'user_id': user_id,
        'token_id': token_id,
        'assigned_at': now_iso8601()
    })

    return token_id

def get_user_token(user_id):
    """Retrieve which token pool this user belongs to."""
    response = dynamodb.Table('UserTokenMapping').get_item(Key={'user_id': user_id})
    return response['Item']['token_id']
```

**Rate Limiting (per Token):**
```python
# lambda/collector/app.py

def check_rate_limit_for_user(user_id):
    """Check if this user's assigned token has capacity."""

    # Get user's token pool
    token_id = get_user_token(user_id)
    token = FB_TOKENS[token_id]  # Dictionary of 10 tokens

    # Check this token's usage in last hour
    now = int(time.time())
    hour_start = now - 3600

    response = dynamodb.Table('RateLimits').query(
        KeyConditionExpression=Key('token_id').eq(token_id) & Key('timestamp').gt(hour_start)
    )

    call_count = len(response['Items'])

    if call_count >= 190:
        raise RateLimitExceededError(
            f"Token {token_id} rate limit: {call_count}/200 calls used. "
            f"Users in this pool: {get_users_in_pool(token_id)}"
        )

    # Record this call
    dynamodb.Table('RateLimits').put_item(Item={
        'token_id': token_id,
        'timestamp': now,
        'user_id': user_id,
        'ttl': now + 7200
    })

    return token
```

**Token Pool Configuration (Lambda Environment):**
```bash
# Environment variables for collector Lambda
FB_TOKEN_000=EAABwz...  # Facebook App #1
FB_TOKEN_001=EAABwz...  # Facebook App #2
FB_TOKEN_002=EAABwz...  # Facebook App #3
# ... (10 tokens total)
```

---

#### **Option 3: User-Provided Tokens (Scale - 500+ users)**

**How It Works:**
- **Each user creates their own Facebook App** during onboarding
- **Each user provides their own access token** via settings page
- Platform **never shares tokens** between users
- Each user has **isolated 200/hour limit** (infinite scale)

**Scale Limits:**
```
Infinite scale:
- Each user has their own 200 calls/hour bucket
- 10,000 Agency users = 10,000 independent rate limits
- No cross-user interference
```

**Pros:**
- ✅ Infinite scale (every user brings their own rate limit)
- ✅ Perfect isolation (no user affects another)
- ✅ Zero platform liability (token issues are user's responsibility)
- ✅ No token renewal burden on platform
- ✅ Users can increase their own limits by creating multiple apps

**Cons:**
- ❌ **High onboarding friction** (users must create FB Developer account)
- ❌ Support burden (many users struggle with FB App creation)
- ❌ Token security risk (users may expose tokens accidentally)
- ❌ Platform has no control over token quality/expiration
- ❌ Harder to troubleshoot (can't inspect user's token)

**Implementation (User Settings Page):**
```typescript
// frontend/src/views/Settings.vue

<template>
  <div class="settings">
    <h2>Meta API Configuration</h2>

    <div v-if="!user.fb_access_token" class="token-setup">
      <p class="warning">
        ⚠️ You need to provide your own Facebook App access token to use MetaAds.
      </p>

      <button @click="showInstructions = true">
        📖 Step-by-Step Token Setup Guide
      </button>

      <input
        v-model="newToken"
        type="password"
        placeholder="Paste your Facebook access token here"
      />
      <button @click="saveToken">Save Token</button>
    </div>

    <div v-else class="token-status">
      <p>✅ Token configured</p>
      <p>Expires: {{ user.fb_token_expires_at }}</p>
      <button @click="renewToken">Renew Token</button>
    </div>

    <!-- Step-by-step guide modal -->
    <TokenSetupGuide v-if="showInstructions" />
  </div>
</template>

<script>
export default {
  methods: {
    async saveToken() {
      // Validate token with Meta API
      const isValid = await this.validateToken(this.newToken);

      if (!isValid) {
        alert('Invalid token. Please check the setup guide.');
        return;
      }

      // Save to DynamoDB (encrypted)
      await this.$api.post('/users/token', {
        fb_access_token: this.newToken
      });

      alert('✅ Token saved successfully!');
    }
  }
}
</script>
```

**Backend API (Token Storage):**
```python
# lambda/api/users.py

from cryptography.fernet import Fernet
import boto3

KMS_KEY_ID = os.environ['KMS_KEY_ID']

def encrypt_token(plaintext_token):
    """Encrypt user's FB token using AWS KMS."""
    kms = boto3.client('kms')

    response = kms.encrypt(
        KeyId=KMS_KEY_ID,
        Plaintext=plaintext_token.encode()
    )

    return response['CiphertextBlob']

@app.post('/users/token')
def save_user_token(request):
    """Save user's Facebook access token (encrypted)."""
    user_id = request.user_id
    token = request.json['fb_access_token']

    # Validate token with Meta API
    validation = requests.get(
        'https://graph.facebook.com/v18.0/me',
        params={'access_token': token}
    )

    if validation.status_code != 200:
        return {'error': 'Invalid Facebook access token'}, 400

    # Get token expiration
    debug_token = requests.get(
        'https://graph.facebook.com/v18.0/debug_token',
        params={
            'input_token': token,
            'access_token': token
        }
    )

    expires_at = debug_token.json()['data']['expires_at']

    # Encrypt and store
    encrypted_token = encrypt_token(token)

    dynamodb.Table('Users').update_item(
        Key={'user_id': user_id},
        UpdateExpression='SET fb_access_token = :token, fb_token_expires_at = :expires',
        ExpressionAttributeValues={
            ':token': encrypted_token,
            ':expires': expires_at
        }
    )

    return {'success': True, 'expires_at': expires_at}
```

**Rate Limiting (Per User):**
```python
# lambda/collector/app.py

def get_user_token(user_id):
    """Decrypt and return user's personal FB token."""
    user = dynamodb.Table('Users').get_item(Key={'user_id': user_id})['Item']

    encrypted_token = user['fb_access_token']

    # Decrypt with KMS
    kms = boto3.client('kms')
    response = kms.decrypt(CiphertextBlob=encrypted_token)

    return response['Plaintext'].decode()

def check_user_rate_limit(user_id):
    """Check if THIS user has exceeded their personal 200/hour limit."""

    now = int(time.time())
    hour_start = now - 3600

    # Query only THIS user's API calls
    response = dynamodb.Table('RateLimits').query(
        KeyConditionExpression=Key('user_id').eq(user_id) & Key('timestamp').gt(hour_start)
    )

    call_count = len(response['Items'])

    if call_count >= 190:
        raise RateLimitExceededError(
            f"You've used {call_count}/200 API calls this hour. "
            f"Your limit resets at {hour_start + 3600}."
        )

    # Record this call
    dynamodb.Table('RateLimits').put_item(Item={
        'user_id': user_id,
        'timestamp': now,
        'ttl': now + 7200
    })
```

---

### Recommended Migration Path

**Stage 1: MVP (0-50 users) → Use Option 1**
- Simplest implementation
- Focus on product-market fit, not scale
- Single token renewal process
- Implementation time: **2 hours** (just store token in env var)

**Stage 2: Growth (50-500 users) → Migrate to Option 2**
- Triggered when approaching 50 Agency or 100 Professional users
- Create 10 Facebook Apps over 1 week
- Migrate existing users to token pool (hash by user_id)
- Implementation time: **1-2 days** (token pool + rebalancing logic)
- **No user disruption** (platform-managed, invisible to users)

**Stage 3: Scale (500+ users) → Migrate to Option 3**
- Triggered when approaching 500 Professional or 50 Agency users per token
- Add "Token Setup" to user onboarding flow
- Grandfather existing users (keep them on Option 2 pool)
- New users must provide their own tokens
- Implementation time: **3-5 days** (UI + KMS encryption + guides)
- **High friction** (requires user education and support docs)

---

### Implementation Checklist

Before starting Phase 0, decide which option to implement:

**For Option 1 (Shared Token):**
- [ ] Create one Facebook App at developers.facebook.com
- [ ] Generate long-lived access token (60 days)
- [ ] Store token in Lambda environment variable `FB_ACCESS_TOKEN`
- [ ] Create DynamoDB table `RateLimits` (PK: token_id, SK: timestamp, TTL: ttl)
- [ ] Implement global rate limiting in collector Lambda
- [ ] Create EventBridge rule to renew token every 50 days
- [ ] Test with 10 simultaneous collections

**For Option 2 (Token Pool):**
- [ ] Create 10 Facebook Apps (can use same developer account)
- [ ] Generate 10 long-lived tokens
- [ ] Store tokens in Lambda env vars (`FB_TOKEN_000` to `FB_TOKEN_009`)
- [ ] Create DynamoDB table `UserTokenMapping` (PK: user_id)
- [ ] Implement token assignment logic (hash or least-loaded)
- [ ] Implement per-token rate limiting
- [ ] Create monitoring dashboard for token pool health
- [ ] Test with 100 users across all pools

**For Option 3 (User-Provided Tokens):**
- [ ] Create KMS key for token encryption
- [ ] Add `fb_access_token` field to Users table (encrypted blob)
- [ ] Build "Token Setup" UI in Settings page
- [ ] Write step-by-step guide for FB App creation
- [ ] Implement token validation endpoint
- [ ] Implement per-user rate limiting (isolated)
- [ ] Create user support docs and video tutorial
- [ ] Test onboarding flow with 5 non-technical users

---

### Cost Comparison

**Option 1 (Shared Token):**
- DynamoDB RateLimits table: ~$0.01/month (100 users)
- EventBridge token renewal: $0.00 (1 event/50 days)
- Lambda token renewal: $0.00 (runs 1x/50 days)
- **Total: ~$0.01/month**

**Option 2 (Token Pool):**
- DynamoDB RateLimits table: ~$0.10/month (1,000 users)
- DynamoDB UserTokenMapping table: ~$0.05/month
- EventBridge token renewal: $0.00 (10 events/50 days)
- Lambda token renewal: $0.00 (runs 10x/50 days)
- **Total: ~$0.15/month**

**Option 3 (User-Provided Tokens):**
- DynamoDB RateLimits table: ~$1.00/month (10,000 users)
- KMS encryption/decryption: ~$0.03/month (1 decrypt per collection)
- **Total: ~$1.03/month**

**Conclusion:** Token management costs are negligible compared to other AWS costs. Choose based on scale requirements, not cost.

---

## DynamoDB Performance Management: What You Actually Do

Unlike SQL databases where you continuously add and optimize indices as performance issues arise, **DynamoDB requires upfront design** for 90% of performance optimization. Understanding this fundamental difference is critical for long-term success.

### Understanding GSI (Global Secondary Index)

**What is a GSI?**

A Global Secondary Index is an alternate query path for your DynamoDB table. Think of it as a "materialized view" that:
- Has its own Partition Key (PK) and Sort Key (SK) - different from the base table
- Is automatically kept in sync by DynamoDB when you write to the base table
- Has its own throughput capacity (separate RCU/WCU billing)
- Can have different attribute projections (ALL, KEYS_ONLY, or INCLUDE specific attributes)

**SQL Analogy:**
```sql
-- SQL: Add index anytime
CREATE INDEX idx_page_name ON ads(page_name);  -- Instant on small tables

-- DynamoDB: GSI is like a separate table that's auto-populated
-- Must be planned upfront or takes HOURS to backfill on large tables
```

**Key Differences from SQL Indices:**

| Feature | SQL Index | DynamoDB GSI |
|---------|-----------|--------------|
| **Creation time** | Seconds to minutes | Hours to days (backfills entire table) |
| **Cost** | Storage overhead only | Double storage + separate RCU/WCU |
| **Limit** | Hundreds possible | **20 GSIs maximum per table** (hard limit) |
| **When to add** | Anytime, based on slow queries | **Design upfront** - expensive to add later |
| **Query performance** | Index scan (fast) | Full query capability (extremely fast) |

**Example from MetaAds Schema (Phase 2, Step 2.1):**

```python
# Base table query: List ads by niche
PK = "NICHE#abc-123"
SK = begins_with("AD#")
# Fast: O(1) partition lookup

# GSI1 query: List ads by page within niche
GSI1PK = "NICHE_PAGE#abc-123#page-456"
GSI1SK = begins_with("AD#")
# Fast: O(1) partition lookup on GSI1

# GSI2 query: List saved ads by niche (sorted by save date)
GSI2PK = "NICHE_SAVED#abc-123"
GSI2SK = "2026-02-22T10:30:00Z#ad-789"
# Fast: O(1) partition lookup + sort order by save date
```

**Learning Resources:**

1. **AWS Official Docs** (Best starting point):
   - Overview: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/GSI.html
   - Best practices: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-indexes-general.html

2. **AWS Workshop** (Hands-on):
   - DynamoDB Immersion Day: https://catalog.workshops.aws/dynamodb-labs/en-US
   - Section on GSIs and access patterns (2-3 hours)

3. **Alex DeBrie's "The DynamoDB Book"** (Industry standard):
   - Free guide: https://www.dynamodbguide.com/
   - Chapter on Secondary Indexes: https://www.dynamodbguide.com/secondary-indexes

4. **Video Tutorial**:
   - "AWS re:Invent - Advanced Design Patterns for DynamoDB" (Rick Houlihan)
   - YouTube: Search "DynamoDB advanced design patterns" (1 hour)

---

> **Further reading**: Design-time optimization, performance strategies (GSI, denormalization, caching, provisioned capacity), problem-specific solutions, and the long-term action plan are documented in detail in **[DYNAMODB_PERFORMANCE_MANAGEMENT.md](./DYNAMODB_PERFORMANCE_MANAGEMENT.md)**.

### Design-Time Optimization (90% of Performance Work)

**Critical: Define ALL access patterns BEFORE creating the table.**

For MetaAds, we've already identified 8 access patterns in Phase 2 — see [DYNAMODB_PERFORMANCE_MANAGEMENT.md](./DYNAMODB_PERFORMANCE_MANAGEMENT.md) for the full table, trade-off analysis, and optimization strategies.

---

### When Performance Issues Hit - Your Options

> See **[DYNAMODB_PERFORMANCE_MANAGEMENT.md](./DYNAMODB_PERFORMANCE_MANAGEMENT.md)** for the full 5-strategy breakdown (Add GSI, Denormalize, FilterExpression, Caching, Provisioned Capacity), specific problem walkthroughs (variant sorting, hot partitions, history growth), and the recommended action plan by scale.

---

## Phase 0: AWS Credential Setup (Prerequisite)
**Objective**: Configure local AWS credentials for Terraform.
**Estimated: 0.5 hours**

| Step | Description | Notes |
|------|-------------|-------|
| 0.1 | **Create IAM user** in AWS Console: IAM > Users > `terraform-deploy`. Attach `AdministratorAccess` policy (temporary; restricted in Phase 7). Create Access Key for CLI use. | Save Access Key ID + Secret Access Key securely |
| 0.2 | **Configure AWS CLI profile**: `aws configure --profile metaads` (enter key ID, secret, region `us-east-1`, output `json`) | Credentials stored in `~/.aws/credentials` |
| 0.3 | **Terraform provider** in `infra/main.tf` references the profile: `provider "aws" { region = "us-east-1"; profile = "metaads" }` | Alternative: export `AWS_ACCESS_KEY_ID` + `AWS_SECRET_ACCESS_KEY` env vars |
| 0.4 | **Verify access**: `aws sts get-caller-identity --profile metaads` | Should return your account ID and IAM user ARN |

**Security**:
- Never commit credentials to git (`.gitignore` includes `.env`, `*.tfvars`, `.terraform/`)
- `AdministratorAccess` is temporary -- replaced by scoped policy after Phase 7 audit
- In Phase 9 (CI/CD), local keys are replaced by OIDC federation (GitHub Actions assumes a role, no static keys)
- After CI/CD is live, deactivate the `terraform-deploy` user's access key

---

## Phase 1: Foundation & Infrastructure (Terraform)
**Objective**: IaC foundation for all AWS resources.
**Estimated: 6-8 hours**

| Step | Description | Hours | Security Notes |
|------|-------------|-------|----------------|
| 1.1 | Create `infra/` Terraform project structure (main.tf, variables.tf, outputs.tf, modules) | 1.0 | S3 backend + DynamoDB lock for state; state encrypted at rest |
| 1.2 | DynamoDB single table (`metaads-{env}`) with PK/SK + 2 GSIs, PAY_PER_REQUEST billing, PITR enabled | 1.0 | Encryption at rest (AWS-managed KMS), point-in-time recovery |
| 1.3 | S3 buckets: frontend hosting + Lambda deployment packages | 1.0 | Block ALL public access; CloudFront OAC only; AES-256 encryption; versioning |
| 1.4 | IAM roles: Lambda execution (least-privilege DynamoDB + Secrets + Logs), Collection Lambda role, API GW logging role | 1.5 | No `*` in resource ARNs; scoped to specific table/secret/log-group ARNs |
| 1.5 | Secrets Manager: `metaads/{env}/meta-api` (FB_ACCESS_TOKEN), `metaads/{env}/clerk` (keys + webhook secret) | 0.5 | IAM-scoped access; never in env vars or code |
| 1.6 | CloudFront distribution with ACM cert, HTTPS redirect, SPA error routing (403/404 -> /index.html) | 1.0 | TLS 1.2+ enforced; OAC to S3; CSP response headers |

**Key files created**: `infra/main.tf`, `infra/dynamodb.tf`, `infra/s3_cloudfront.tf`, `infra/iam.tf`, `infra/secrets.tf`, `infra/lambda.tf`, `infra/api_gateway.tf`, `infra/monitoring.tf`, `infra/variables.tf`, `infra/outputs.tf`

---

## Phase 2: DynamoDB Data Layer
**Objective**: Single-table design + Python repository layer replacing SQLAlchemy.
**Estimated: 10-12 hours**

### Step 2.1: Single-Table Design (3 hours)

Converting 6 SQLite tables (User, Niche, Ad, Page, NichePage, CollectionRun) into one DynamoDB table:

| Entity | PK | SK | GSI1PK | GSI1SK | GSI2PK | GSI2SK |
|--------|----|----|--------|--------|--------|--------|
| User | `USER#<clerk_id>` | `METADATA` | `USER_EMAIL#<email>` | `METADATA` | -- | -- |
| Niche | `USER#<user_id>` | `NICHE#<niche_id>` | `NICHE#<niche_id>` | `METADATA` | `USER_SLUG#<user_id>#<slug>` | `METADATA` |
| Ad | `NICHE#<niche_id>` | `AD#<meta_ad_id>` | `NICHE_PAGE#<niche_id>#<page_id>` | `AD#<meta_ad_id>` | `NICHE_SAVED#<niche_id>` | `<saved_at>#<ad_id>` (only when saved) |
| Page | `PAGE#<page_id>` | `METADATA` | -- | -- | -- | -- |
| NichePage | `NICHE#<niche_id>` | `PAGE#<page_id>` | -- | -- | -- | -- |
| CollectionRun | `NICHE#<niche_id>` | `RUN#<timestamp>#<run_id>` | -- | -- | -- | -- |

**Access patterns resolved**:
- List niches by user: `PK=USER#<user_id>, SK begins_with("NICHE#")`
- Get niche by slug: `GSI2: PK=USER_SLUG#<user_id>#<slug>`
- List ads by niche: `PK=NICHE#<niche_id>, SK begins_with("AD#")` + FilterExpression for is_active/cta/days_active/text
- Ads by page: `GSI1: PK=NICHE_PAGE#<niche_id>#<page_id>`
- Saved ads: `GSI2: PK=NICHE_SAVED#<niche_id>` (sorted by saved_at in SK)
- Collection runs: `PK=NICHE#<niche_id>, SK begins_with("RUN#")` (chronological by SK)
- **Ad grouping by variant (page_name+headline)**: Application-side (same as current `ads.py:130-198`)
- **Sort ads by variant count**: Application-side grouping + sorting (see note below)

**Note on Variant Count Sorting:**

Current behavior (`ads.py:143-148`): Sort ad groups by number of variants (e.g., show ads with 5 variants before ads with 2 variants). This requires:
1. Fetch all ads for niche
2. Group by `page_name|headline` in Lambda
3. Sort groups by `len(group)`
4. Paginate groups (not individual ads)

**DynamoDB limitation**: Cannot natively sort by "count of items with same variant_id" without denormalizing the count.

**Solution options** (in order of recommendation):

1. **Application-side (current approach - RECOMMENDED for MVP)**:
   ```python
   # Fetch all ads, group in Lambda, sort by len(group)
   # Cost: 1 DynamoDB query + O(n) Python grouping
   # Works well for <5000 ads per niche (typical case)
   ```

2. **Denormalize variant_count (if >5000 ads per niche)**:
   ```python
   # When ad is created/updated, calculate and store variant_count:
   variant_id = hashlib.md5(f"{page_name}{headline}".encode()).hexdigest()[:8]

   # Count existing ads with same variant_id (requires scan or counter)
   variant_count = count_ads_with_variant(niche_id, variant_id)

   # Store in SK for native sorting:
   SK = f"AD#{variant_count:03d}#{days_active:05d}#{meta_ad_id}"

   # Query with KeyConditionExpression (natively sorted by variant_count desc)
   ```
   **Trade-off**: Requires updating ALL ads in variant group when new ad added (write amplification).

3. **Maintain variant count in separate items**:
   ```python
   # Store variant metadata as separate item:
   PK = f"NICHE#{niche_id}"
   SK = f"VARIANT#{variant_id}"
   variant_count = 5  # Updated on each ad add/remove

   # Query variants sorted by count, then fetch ads for top variants
   # Cost: 2 queries (variants, then ads)
   ```

**Recommendation**: Keep application-side grouping for MVP (current plan). If variant sorting becomes a performance bottleneck (>10K ads per niche), implement solution #3 (variant metadata items).

### Step 2.2: DynamoDB Repository Layer (5-6 hours)

| File to create | Replaces | Notes |
|----------------|----------|-------|
| `backend/app/dynamodb/__init__.py` | -- | Module init |
| `backend/app/dynamodb/client.py` | `app/__init__.py` (SQLAlchemy `db`) | boto3 singleton, table name from env var |
| `backend/app/dynamodb/models.py` | `app/models/*.py` | Dataclasses + `to_dict()` / `to_item()` / `from_item()` converters |
| `backend/app/dynamodb/user_repo.py` | `app/services/user_service.py` + `app/models/user.py` | get, create, update, deactivate |
| `backend/app/dynamodb/niche_repo.py` | `app/services/niche_service.py` + `app/models/niche.py` | CRUD + get_by_slug + stats |
| `backend/app/dynamodb/ad_repo.py` | `app/services/ad_service.py` + `app/models/ad.py` | create_or_update, query with filters, save/unsave, clear |
| `backend/app/dynamodb/page_repo.py` | `app/models/page.py` + `app/models/niche_page.py` | Merges Page + NichePage operations |
| `backend/app/dynamodb/collection_repo.py` | `app/models/collection_run.py` | create_run, update_status, mark_completed/error |

**Reuse**: `app/utils/ids.py` (generate_uuid, now_iso8601, generate_sort_key) used as-is.

### Step 2.3: Data Migration Script (2-3 hours)

Create `scripts/migrate_sqlite_to_dynamodb.py`:
- Reads all data from SQLite via existing SQLAlchemy models
- Transforms to DynamoDB item format (PK/SK/GSI keys + attributes)
- Bulk writes via `batch_write_item` (25 items per batch)
- Progress reporting + error handling

**Security**: DynamoDB access via IAM role only; condition expressions prevent overwrites; all queries scoped by user_id/niche_id in PK (tenant isolation).

---

## Phase 3: Lambda Functions
**Objective**: Convert Flask routes to Lambda handlers behind API Gateway HTTP API.
**Estimated: 12-15 hours**

---

### ⚠️ CRITICAL: Meta Ad Library API Rate Limits

**The Meta Ad Library API enforces a strict limit of 200 API calls per hour** (per access token).

**What this means for MetaAds:**
- Each `/ads_archive` query = 1 API call
- Pagination requests (using `next` URL) = 1 additional API call each
- **Maximum 200 calls per 60-minute rolling window**
- Exceeding this limit results in HTTP 429 errors and temporary API blocks

**Sources:**
- [How to Use the Facebook (Meta) Ad Library API](https://apidog.com/blog/facebook-ad-library-api/)
- [Meta API Rate Limits vs. Throttling](https://www.adamigo.ai/blog/meta-api-rate-limits-vs-throttling-key-differences)
- [Facebook Ad Library API Overview](https://paulcbauer.github.io/apis_for_social_scientists_a_review/facebook-ad-library-api.html)

**Current protection** (already implemented in `CLAUDE.md` lines 390-413):
```python
class RateLimiter:
    def __init__(self, max_requests_per_hour: int = 200):
        self.max_requests = max_requests_per_hour
        self.requests = []

    def wait_if_needed(self):
        now = time.time()
        # Remove requests older than 1 hour
        self.requests = [r for r in self.requests if now - r < 3600]

        if len(self.requests) >= self.max_requests:
            # Calculate wait time until oldest request expires
            oldest = self.requests[0]
            wait_time = 3600 - (now - oldest) + 1
            time.sleep(wait_time)  # BLOCKS until rate limit resets
            self.requests = []

        self.requests.append(now)
```

**Lambda Implementation Requirements:**

**1. DynamoDB-backed rate limit tracking** (Phase 2, Step 2.1 - add to schema):
```python
# Add item type for rate limit tracking:
{
    'PK': 'RATE_LIMIT#user-abc-123',
    'SK': 'CALL#2026-02-22T14:30:15Z',
    'niche_id': 'niche-xyz-456',
    'api_endpoint': '/ads_archive',
    'pagination_count': 3,  # This query had 3 pagination calls
    'ttl_expiry': 1708705815  # Unix timestamp (2 hours from now)
}

# TTL auto-deletes after 2 hours (we only need 1-hour window)
```

**2. Per-user rate limit checking** (Phase 3, Step 3.4 - Collection Lambda):
```python
# backend/lambdas/collection_worker/handler.py
import boto3
from datetime import datetime, timedelta

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

def check_rate_limit(user_id):
    """Check if we can collect without exceeding Meta API limits."""
    now = datetime.utcnow()
    hour_ago = now - timedelta(hours=1)

    # Query API calls in last hour (across ALL niches for this user)
    response = table.query(
        KeyConditionExpression='PK = :pk AND SK > :hour_ago',
        ExpressionAttributeValues={
            ':pk': f"RATE_LIMIT#{user_id}",
            ':hour_ago': f"CALL#{hour_ago.isoformat()}"
        }
    )

    api_calls_last_hour = sum(
        item.get('pagination_count', 1) for item in response['Items']
    )

    if api_calls_last_hour >= 180:  # Conservative limit (90% of 200)
        raise RateLimitException(
            f"Rate limit approaching: {api_calls_last_hour}/200 calls in last hour. "
            f"Next available slot: {(hour_ago + timedelta(hours=1)).isoformat()}"
        )

    return api_calls_last_hour

def record_api_call(user_id, niche_id, pagination_count=1):
    """Record API call for rate limit tracking."""
    now = datetime.utcnow()

    table.put_item(Item={
        'PK': f"RATE_LIMIT#{user_id}",
        'SK': f"CALL#{now.isoformat()}",
        'niche_id': niche_id,
        'pagination_count': pagination_count,
        'ttl_expiry': int((now + timedelta(hours=2)).timestamp())
    })
```

**3. Collection staggering for multi-niche users** (Phase 3, Step 3.4):
```python
# Problem: Agency tier user with 50 niches, 8 collections/day
# = 400 collections/day
# If all run simultaneously = 400 API calls in 5 minutes = EXCEEDS 200/hour limit

# Solution: Distribute collections across time windows
def schedule_staggered_collections(user_id, niches, collections_per_day):
    """Distribute collection invocations to respect 200/hour API limit."""

    # Calculate safe rate: 180 calls/hour (90% of limit for buffer)
    # Each collection may paginate 2-3 times on average
    max_collections_per_hour = 180 / 3  # = 60 collections/hour (conservative)

    # Calculate delay between niches
    delay_seconds = 3600 / max_collections_per_hour  # = 60 seconds

    for i, niche in enumerate(niches):
        delay = i * delay_seconds

        # Schedule Lambda invocation with delay
        lambda_client.invoke(
            FunctionName='collection-worker',
            InvocationType='Event',  # Async
            Payload=json.dumps({
                'user_id': user_id,
                'niche_id': niche['id'],
                'execute_at': (datetime.utcnow() + timedelta(seconds=delay)).isoformat()
            })
        )

    logger.info(
        f"Scheduled {len(niches)} collections over "
        f"{(len(niches) * delay_seconds) / 60:.1f} minutes"
    )
```

**4. Graceful degradation when limit approached** (Phase 3, Step 3.4):
```python
def collect_with_retry(user_id, niche_id):
    """Collect ads with automatic retry if rate limit hit."""
    try:
        # Check rate limit before calling API
        calls_used = check_rate_limit(user_id)

        if calls_used >= 150:  # Warn at 75%
            logger.warning(
                f"Rate limit at 75%: {calls_used}/200 calls used. "
                f"Consider staggering collections."
            )

        # Fetch from Meta API (with pagination)
        ads, pagination_count = fetch_from_meta_api(niche_id)

        # Record API usage
        record_api_call(user_id, niche_id, pagination_count)

        # Store in DynamoDB
        store_ads(ads)

    except RateLimitException as e:
        # Don't fail - queue for retry in 1 hour
        sqs_client.send_message(
            QueueUrl=os.environ['RETRY_QUEUE_URL'],
            MessageBody=json.dumps({
                'user_id': user_id,
                'niche_id': niche_id,
                'retry_reason': 'rate_limit'
            }),
            DelaySeconds=3600  # Retry in 1 hour
        )

        logger.warning(
            f"Rate limit hit for user {user_id}, niche {niche_id}. "
            f"Queued for retry in 1 hour."
        )

        # Update collection run status
        update_collection_status(niche_id, status='rate_limited')
```

**5. CloudWatch monitoring** (Phase 7, Step 7.3):
```hcl
# infra/monitoring.tf
resource "aws_cloudwatch_metric_alarm" "api_rate_limit_warning" {
  alarm_name          = "MetaAPI-RateLimitWarning"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "APICallsPerHour"  # Custom metric from Lambda
  namespace           = "MetaAds/Collection"
  period              = 300  # 5 minutes
  statistic           = "Sum"
  threshold           = 150  # Alert at 75% of 200 limit
  alarm_description   = "Meta API usage at 75% - approaching rate limit"

  alarm_actions = [aws_sns_topic.alerts.arn]
}

resource "aws_cloudwatch_metric_alarm" "api_rate_limit_critical" {
  alarm_name          = "MetaAPI-RateLimitCritical"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "APICallsPerHour"
  namespace           = "MetaAds/Collection"
  period              = 300
  statistic           = "Sum"
  threshold           = 180  # Alert at 90% of 200 limit
  alarm_description   = "Meta API usage at 90% - CRITICAL rate limit risk"

  alarm_actions = [aws_sns_topic.alerts.arn]
}
```

**Projected API usage by tier:**

| Tier | Niches | Collections/Day | Avg Calls/Hour | Peak Calls/Hour | Risk Level |
|------|--------|-----------------|----------------|-----------------|------------|
| **Free** | 1 | 1 (manual) | 0.04 | 5 | ✅ Safe |
| **Starter** | 3 | 2×/day (12h) | 0.25 | 15 | ✅ Safe |
| **Professional** | 10 | 4×/day (6h) | 1.7 | 50 | ✅ Safe (with staggering) |
| **Agency** | 50 | 8×/day (3h) | 8.3 | **200** | ⚠️ **CRITICAL - MUST stagger** |

**Agency tier requires mandatory staggering:**
- 50 niches × 8 collections/day = 400 collections/day
- Distributed over 24 hours = 16.6 collections/hour
- Each collection ≈ 2-3 API calls (pagination) = **33-50 calls/hour** ✅ SAFE
- **BUT**: If all 50 run simultaneously = 150 API calls in 5 minutes = ❌ EXCEEDS LIMIT
- **Solution**: Stagger collections 1 per minute (60-second delay between niches)

**Testing rate limit protection** (Phase 6 - Testing):
```python
# tests/test_rate_limiter.py
def test_rate_limit_blocks_at_200():
    """Ensure DynamoDB-backed rate limiter blocks after 200 calls."""
    user_id = 'test-user-123'

    # Simulate 180 API calls in last hour
    for i in range(180):
        record_api_call(user_id, f'niche-{i}', pagination_count=1)

    # Should still allow (under 180 threshold)
    calls_used = check_rate_limit(user_id)
    assert calls_used == 180

    # Add 10 more calls (total 190) - should warn but allow
    for i in range(10):
        record_api_call(user_id, f'niche-{i}', pagination_count=1)

    calls_used = check_rate_limit(user_id)
    assert calls_used == 190  # Still under limit

    # Try to exceed (total 200) - should BLOCK
    with pytest.raises(RateLimitException):
        check_rate_limit(user_id)

def test_agency_tier_staggering():
    """Ensure 50-niche Agency tier doesn't exceed rate limit."""
    # Agency tier: 50 niches × 8 collections/day
    niches = [{'id': f'niche-{i}'} for i in range(50)]

    schedule = schedule_staggered_collections(
        user_id='agency-user',
        niches=niches,
        collections_per_day=8
    )

    # Verify collections spread over at least 50 minutes (1 per minute)
    time_span_minutes = (schedule[-1]['execute_at'] - schedule[0]['execute_at']).seconds / 60
    assert time_span_minutes >= 50, f"Collections too clustered: {time_span_minutes} minutes"

    # Verify no 1-hour window exceeds 180 API calls
    for hour_window in sliding_window_hours(schedule):
        api_calls = sum(c.get('pagination_count', 3) for c in hour_window)
        assert api_calls < 180, f"Exceeded safe limit in hour: {api_calls}"
```

**Key Implementation Notes:**

- ✅ **RateLimiter already exists** in current codebase (`CLAUDE.md:390-413`)
- ⚠️ **Must migrate to DynamoDB-backed tracking** (not in-memory) for Lambda statelessness
- ⚠️ **Cross-niche coordination required** for Professional (10 niches) and Agency (50 niches) tiers
- ⚠️ **Pagination multiplier**: Each query may trigger 2-5 API calls (initial + pagination)
- ✅ **TTL on rate limit items** = auto-cleanup after 2 hours (no manual deletion needed)
- ⚠️ **SQS retry queue** needed for graceful degradation when limit hit

**Implementation Priority:**
1. **Phase 2**: Add `RATE_LIMIT#` item type to DynamoDB schema
2. **Phase 3.4**: Implement rate limit checking in collection Lambda
3. **Phase 3.4**: Implement collection staggering for multi-niche users
4. **Phase 7.3**: Add CloudWatch alarms for rate limit monitoring
5. **Phase 6**: Write comprehensive rate limit tests

---

### Step 3.1: Lambda Layer for Shared Code (1.5 hours)

Create `lambda_layers/shared/` containing:
- `app/dynamodb/` (repository layer from Phase 2)
- `app/utils/` (ids.py)
- `collectors/meta_api_collector.py` (stateless, lift as-is; replace `Config` import with env var)
- `processors/ad_parser.py` (stateless, lift as-is; no Flask dependencies)
- Shared pip packages: PyJWT, requests, svix

### Step 3.2: Lambda Handler Structure (2 hours)

**Grouping by domain** (5 handler functions + 1 authorizer):

| Lambda | Routes | Source to port | Timeout |
|--------|--------|---------------|---------|
| `auth_handler` | `POST /api/auth/webhook`, `GET /api/auth/me` | `routes/auth.py` | 10s |
| `niches_handler` | CRUD `/api/niches/*`, `/api/niches/{slug}/stats` | `routes/niches.py` | 10s |
| `ads_handler` | `/api/niches/{slug}/ads/*` (search, detail, related, variants, clear) | `routes/ads.py` | 15s |
| `saved_handler` | `/api/niches/{slug}/saved`, `/api/niches/{slug}/ads/{id}/save` | `routes/saved.py` | 10s |
| `collect_trigger` | `POST /api/niches/{slug}/collect` | `routes/niches.py:301-439` (trigger only) | 10s |
| `collect_worker` | Async Meta API collection | `routes/niches.py:339-414` + collector + parser | **900s (15min)** |

Translation pattern:
- `request.args` -> `event['queryStringParameters']`
- `request.get_json()` -> `json.loads(event['body'])`
- `g.user_id` -> `event['requestContext']['authorizer']['lambda']['user_id']`
- `jsonify(data), status` -> `{'statusCode': N, 'body': json.dumps(data)}`

### Step 3.3: Implement Each Handler Group (8-10 hours)

Port logic from each Flask route file into Lambda handler, replacing SQLAlchemy calls with DynamoDB repository calls. The search/filter/group/paginate logic in `ads.py:54-198` is the most complex -- DynamoDB Query + FilterExpression + application-side grouping.

### Step 3.4: API Gateway HTTP API (2 hours)

Terraform config for:
- HTTP API (v2) -- lower cost than REST API
- CORS: allow frontend domain, methods GET/POST/PATCH/DELETE/OPTIONS
- Route mappings for all endpoints
- Lambda integrations with payload format 2.0
- Throttling: 100 req/s burst, 50 req/s sustained (cost protection)
- Stage: `$default` with auto-deploy

**Security**: Lambda concurrency limits (prevent runaway costs); CORS restricts to frontend domain; input validation in every handler.

---

## Phase 4: Authentication (Clerk JWT in Lambda)
**Objective**: Replace Flask `g` object auth with Lambda authorizer using proper JWKS verification.
**Estimated: 4-5 hours**

| Step | Description | Hours | Notes |
|------|-------------|-------|-------|
| 4.1 | Lambda Authorizer: Clerk JWT validation via JWKS (RS256) | 2.5 | **Major security upgrade** from current decode-without-verify in `middleware/auth.py:121-138`. Uses `PyJWKClient` for proper RS256 verification. Caches JWKS across warm invocations. |
| 4.2 | Webhook signature verification using `svix` library | 1.0 | Replaces `auth.py:130-151`. Webhook endpoint has NO authorizer. |
| 4.3 | API Gateway authorizer config (5-min result TTL) | 0.5 | All routes except `/api/auth/webhook` and `/api/health` use authorizer |
| 4.4 | User auto-creation in `/auth/me` via DynamoDB conditional PutItem | 1.0 | Ports `auth.py:154-195` placeholder user logic |

**Security**: RS256 JWKS verification (not insecure decode); 5-min authorizer cache reduces invocations; webhook uses Svix cryptographic verification.

---

## Phase 5: Collection Pipeline (Async)
**Objective**: Convert synchronous collection to async Lambda pattern.
**Estimated: 6-8 hours**

Current problem: `POST /niches/{slug}/collect` in `routes/niches.py:301-439` is synchronous (10-60 seconds). API Gateway has 30s timeout.

**Solution**: Two-Lambda pattern:

| Step | Description | Hours |
|------|-------------|-------|
| 5.1 | `collect_trigger` Lambda: validates request, creates CollectionRun (status=pending), async-invokes worker, returns 202 with run_id | 1.5 |
| 5.2 | `collect_worker` Lambda (15-min timeout): calls Meta API via `MetaAdLibraryAPI`, parses via `AdParser`, writes to DynamoDB, updates CollectionRun status | 3.5 |
| 5.3 | Collection status endpoint: `GET /api/niches/{slug}/collection-runs/{run_id}` for polling | 1.0 |
| 5.4 | Dead letter queue (SQS) for failed async invocations + CloudWatch alarm on failures | 1.0 |

**Reuse**: `collectors/meta_api_collector.py` and `processors/ad_parser.py` are stateless -- lift directly. Only change: replace `Config.FB_ACCESS_TOKEN` with Secrets Manager lookup.

**Security**: Worker Lambda concurrency limit of 5 (prevent Meta API rate limit abuse); Meta API token from Secrets Manager only; SQS dead-letter queue for failure handling.

---

## Phase 6: Frontend Deployment
**Objective**: Deploy Vue 3 SPA to S3 + CloudFront.
**Estimated: 3-4 hours**

| Step | Description | Hours | Notes |
|------|-------------|-------|-------|
| 6.1 | Create `.env.production` with `VITE_API_URL` (API GW endpoint) and `VITE_CLERK_PUBLISHABLE_KEY` | 0.5 | No code changes -- `frontend/src/services/api.js:14` already reads `VITE_API_URL` |
| 6.2 | S3 upload script (`npm run build` + `aws s3 sync` + CloudFront invalidation) | 1.0 | |
| 6.3 | CloudFront: HTTPS, SPA routing, caching (immutable assets vs index.html), custom domain (optional) | 1.5 | Cache-Control headers; CSP header via response headers policy |
| 6.4 | Smoke test: frontend loads, Clerk login works, API calls reach Lambda | 1.0 | |

**No frontend code changes required.** Only build-time environment variables change.

---

## Phase 7: Security Hardening
**Objective**: Defense-in-depth across all services.
**Estimated: 8-11 hours** *(updated: +3h for Meta API rate-limit items)*

| Step | Description | Hours |
|------|-------------|-------|
| 7.1 | IAM policy audit: no `*` resources, scoped to exact ARNs, separate roles per function group | 2.0 |
| 7.2 | API Gateway throttling (100 burst / 50 sustained per route) -- replaces WAF at $0/month vs WAF's $5/month | 1.0 |
| 7.3 | CloudWatch alarms: Lambda errors (>5/5min), DynamoDB throttling (>0), API 5xx (>10/5min), collection failures; SNS topic for email alerts | 2.0 |
| 7.4 | Security audit checklist: CloudWatch log retention (7 days), no secrets in env vars, HTTPS everywhere, S3 public access blocked, PITR on DynamoDB | 1.0 |
| 7.5 | Meta API global rate-limit counter in DynamoDB | 1.5 |
| 7.6 | Meta API token auto-renewal via EventBridge + Lambda | 1.5 |

**Decision**: Skip AWS WAF ($5/month minimum) -- use API Gateway throttling + Lambda concurrency limits instead. Revisit if abuse detected.

### Step 7.5 — Meta API Global Rate-Limit Counter

**Why needed**: The in-process `RateLimiter(200)` in `meta_api_collector.py` tracks calls **per Lambda instance only**. With up to 5 concurrent `collect_worker` instances (enforced by `reserved_concurrent_executions = 5`), the hard Meta API ceiling of 200 calls/hour is shared across all instances but not enforced globally. In the worst case, 5 workers starting simultaneously and each making 40 paginated calls = 200 calls in 5 minutes, exhausting the hourly budget in one burst.

**What's already in place** (does not need to be re-done):
- `reserved_concurrent_executions = 5` on `collect_worker` — caps simultaneous workers at the infrastructure level; naturally staggers collections and limits burst exposure
- `RateLimiter(200)` in `meta_api_collector.py` — prevents a single runaway worker from hitting the ceiling on its own
- `collect_worker_errors` CloudWatch alarm — fires immediately on any Lambda error, which includes HTTP 429 responses from Meta

**What still needs to be built** (Step 7.5):
- Add a `RateLimitCounters` item to the existing DynamoDB main table (PK: `RATE_LIMIT#meta-api`, SK: `WINDOW#<hour-epoch>`, TTL: epoch+7200) tracking the total number of Meta API calls made in the current rolling hour across **all** concurrent workers
- In `collect_worker/handler.py`, before calling `api.search_ads()`: atomically increment the counter with `ADD call_count :n` and read the result; abort the run (mark as `throttled`) if `call_count >= 190` (10-call safety buffer)
- This is an **Option 1 (Shared Token)** implementation as described in the plan's "Implementation Checklist"; sufficient for MVP scale (≤50 users)

**Cost**: ~$0.01/month additional DynamoDB writes (negligible).

### Step 7.6 — Meta API Token Auto-Renewal

**Why needed**: The Meta API access token stored in Secrets Manager (`metaads/{env}/meta-api`) is a long-lived token that expires every **60 days**. Currently there is no automated renewal. Token expiry causes all `collect_worker` invocations to fail silently with HTTP 401 errors — every user's collection jobs stop working until an operator manually rotates the secret.

**What needs to be built**:
- **EventBridge Scheduler rule** — fires every 50 days (10-day buffer before the 60-day expiry)
- **`token_renewal` Lambda** — calls the Meta Graph API token-exchange endpoint (`/oauth/access_token?grant_type=fb_exchange_token`) to extend the token's lifetime, then calls `secretsmanager:PutSecretValue` to update `metaads/{env}/meta-api` with the new token string
- **IAM role** for the renewal Lambda — `secretsmanager:PutSecretValue` on `metaads/{env}/meta-api` only; `lambda:InvokeFunction` not needed (EventBridge invokes directly)
- **CloudWatch alarm** — alert on `token_renewal` Lambda errors so expiry is never silent

**Terraform resources to add** (`lambda.tf`, `iam.tf`, `monitoring.tf`):
```
aws_lambda_function.token_renewal
aws_cloudwatch_event_rule.token_renewal_schedule   (EventBridge Scheduler, rate 50 days)
aws_cloudwatch_event_target.token_renewal
aws_lambda_permission.allow_eventbridge_token_renewal
aws_iam_role.lambda_token_renewal
aws_iam_role_policy.lambda_token_renewal_secrets   (PutSecretValue on meta-api secret only)
aws_iam_role_policy_attachment.lambda_token_renewal_logs
aws_cloudwatch_metric_alarm.token_renewal_errors
```

**Cost**: $0.00 (1 Lambda invocation per 50 days; EventBridge Scheduler free tier covers millions of invocations).

---

## Phase 8: Testing & Validation
**Objective**: Functional correctness, performance, and cost compliance.
**Estimated: 6-8 hours**

| Step | Description | Hours |
|------|-------------|-------|
| 8.1 | Unit tests: DynamoDB repository layer using `moto` library (mock DynamoDB). Port existing tests from `backend/tests/` (test_ads.py, test_niches.py, test_saved.py, test_health.py) | 2.0 |
| 8.2 | Integration tests: each Lambda handler locally via SAM CLI `sam local invoke` | 2.0 |
| 8.3 | End-to-end smoke tests: deploy to `dev` env, full flow (login -> create niche -> collect -> search -> save) | 1.5 |
| 8.4 | Cost validation after 1 week: verify AWS Cost Explorer matches projections | 1.0 |
| 8.5 | Load test: 100 concurrent users with Artillery/k6; verify cold starts <3s, p99 <500ms reads, no DynamoDB throttle | 1.5 |

---

## Phase 9: CI/CD Pipeline
**Objective**: Automated deployment via GitHub Actions.
**Estimated: 4-5 hours**

| Step | Description | Hours |
|------|-------------|-------|
| 9.1 | GitHub Actions workflow: test -> package Lambda -> Terraform apply -> build frontend -> S3 sync -> CloudFront invalidation | 2.5 |
| 9.2 | OIDC federation for GitHub Actions (no long-lived AWS keys) | 1.0 |
| 9.3 | Environment separation: `dev.tfvars` / `prod.tfvars` | 0.5 |
| 9.4 | Rollback strategy: Lambda versioned aliases, S3 versioning, DynamoDB PITR | 1.0 |

**Security**: OIDC federation (no static credentials); deploy role scoped to `main` branch only; Terraform plan-then-apply with manual approval for prod.

---

## Cost Projection (100 Users)

| Service | Monthly Usage | Cost | Notes |
|---------|--------------|------|-------|
| Lambda | ~31K invocations, ~50K GB-s | $0.00 | Within 1M free requests + 400K GB-s free tier |
| API Gateway (HTTP) | ~30K requests | $0.00-$0.35 | 1M free (12 months); after: $1/M requests |
| DynamoDB (On-Demand) | 25K writes, 100K reads | $0.06 | Well within 25 WCU/RCU always-free tier |
| S3 | ~50MB storage, 10K requests | $0.01 | |
| CloudFront | ~1GB transfer | $0.00 | Within 1TB free (12 months) |
| Secrets Manager | 2 secrets | $0.80 | $0.40/secret/month |
| CloudWatch Logs | <1GB | $0.00 | Within 5GB free tier |
| **TOTAL** | | **$0.87-$1.22/mo** | **$1.50-$2.50 after free tier expiry** |

---

## Security Architecture Summary

| Service | Encryption at Rest | Encryption in Transit | Access Control | Monitoring |
|---------|-------------------|----------------------|----------------|------------|
| DynamoDB | AWS-managed KMS | HTTPS (SDK default) | IAM least-privilege role | CloudWatch throttle alarm |
| Lambda | N/A (ephemeral) | HTTPS (API GW) | IAM execution role, concurrency limits | Error alarm, duration alarm |
| API Gateway | N/A | TLS 1.2+ enforced | Lambda authorizer (Clerk JWT) | 5xx alarm, throttling |
| S3 (frontend) | AES-256 | HTTPS (CloudFront OAC) | Block all public access, OAC policy | Access logging |
| CloudFront | N/A | TLS 1.2+ (ACM cert) | OAC to S3, HTTPS redirect | Real-time logs (optional) |
| Secrets Manager | AWS KMS | HTTPS | IAM resource policy | CloudTrail |
| CloudWatch Logs | AWS KMS (optional) | HTTPS | IAM resource policy | Retention policy (7 days) |

---

## Implementation Timeline

```
Week 1:    Phase 1 (Foundation) + Phase 2 (DynamoDB Layer)
Week 2:    Phase 4 (Auth) + Phase 3 (Lambda Functions)
Week 3:    Phase 5 (Collection) + Phase 6 (Frontend Deploy)
Week 4:    Phase 7 (Security) + Phase 8 (Testing)
Week 4-5:  Phase 9 (CI/CD)
```

**Total estimated effort: 52-64 hours** (~7-8 working days)

---

## Verification Plan

1. **DynamoDB**: Run migration script against test table; verify all access patterns return correct data
2. **Lambda**: SAM local invoke for each handler with sample events; verify JSON responses match current Flask API
3. **Auth**: Test Clerk JWT flow end-to-end (sign in -> get token -> call protected endpoint)
4. **Collection**: Trigger collection, poll status, verify ads appear in DynamoDB
5. **Frontend**: Load app from CloudFront, verify all views work (NicheSelector, Search, Saved, Settings)
6. **Cost**: Monitor AWS Cost Explorer for 1 week; verify <$3/month projection
7. **Security**: Run `terraform plan` to verify no unintended resource exposure; verify all S3 buckets block public access; verify CloudWatch alarms fire on synthetic errors
