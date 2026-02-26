# Periodic Collection Feature - Implementation Plan

## Executive Summary

Implement automatic ad collection every 3 hours for all active niches with comprehensive auditing to distinguish between genuinely failing keywords and system bugs.

**Key Insight**: We need to differentiate between:
- ✅ **Long-tail keywords** that legitimately return 0 ads (not a bug)
- ❌ **System bugs** that prevent collection (needs fixing)
- ⚠️ **Intermittent Meta API failures** (need retry logic - already exists)

---

## Current State Analysis

### ✅ What We Already Have

1. **Collection Infrastructure** (fully functional):
   - `CollectionRun` model tracks each collection attempt
   - `collect_trigger` Lambda orchestrates collections
   - `collect_worker` Lambda performs actual collection
   - DynamoDB stores collection history with stats

2. **CollectionRun Tracking** (lines 528-600 in `models.py`):
   ```python
   @dataclass
   class CollectionRun:
       id: str
       niche_id: str
       status: str              # pending | running | completed | error
       keywords_used: List[str]
       ads_found: int           # ✅ Total ads returned by Meta API
       ads_new: int             # ✅ New ads inserted
       ads_updated: int         # ✅ Existing ads refreshed
       error_message: Optional[str]
       started_at: str
       completed_at: Optional[str]
   ```

3. **Ad Tracking** (lines 198-253 in `models.py`):
   - `collected_at`: Timestamp when ad was first collected
   - `is_active`: Whether ad is currently active (from Meta API)
   - `start_date`, `end_date`: Ad lifecycle dates

### ❌ What's Missing

1. **Scheduled Execution**: No EventBridge Scheduler to trigger collections
2. **Last Updated Tracking**: Can't tell how "fresh" an ad is
3. **Collection Health Dashboard**: No UI to audit collection performance
4. **Stale Ad Detection**: No way to mark ads that haven't been seen recently
5. **Keyword Performance Analytics**: Can't identify consistently failing keywords

---

## Problem Analysis: Audit Requirements

### Question 1: Where do we store attempted collections?

**Answer**: Already stored in `CollectionRun` items!

**DynamoDB Layout**:
```
PK: NICHE#<niche_id>
SK: RUN#<ISO8601_timestamp>#<run_id>
```

**Example Query** (already works):
```python
CollectionRepo.list_for_niche(niche_id="abc-123", limit=20)
# Returns last 20 collection runs, newest first
```

### Question 2: How many are new vs updated?

**Answer**: Already tracked per collection run!

```python
CollectionRun:
    ads_found: 50      # Meta API returned 50 ads
    ads_new: 12        # 12 were new (first time seeing them)
    ads_updated: 38    # 38 already existed (refreshed their data)
```

**Derived Metrics** (can calculate):
- `ads_unchanged = ads_found - ads_new - ads_updated` (should be 0)
- `success_rate = ads_found / expected_ads`
- `new_discovery_rate = ads_new / ads_found`

### Question 3: Do we need `last_updated_timestamp`?

**Answer**: YES! Critical missing piece.

**Current Issue**:
- `Ad.collected_at`: Set once when ad is first seen (never updated)
- `Ad.is_active`: Reflects Meta API status at collection time
- **Missing**: When was this ad last refreshed?

**Why It Matters**:
```
Scenario: Ad collected on Jan 1, periodic collection enabled Jan 15

Question: Is this ad stale because:
A) Meta API stopped showing it (ad ended)
B) Our collection hasn't run recently (system issue)

Without last_updated_timestamp: Can't tell!
```

---

## Proposed Solution

### Phase 0: User Opt-In (CRITICAL)

#### 0.1 Add `auto_collect_enabled` to Niche Model

**Rationale**: Users must **explicitly enable** periodic collection for each niche to avoid wasting resources on niches they're not actively monitoring.

**Schema Change** (`models.py` - Niche dataclass):
```python
@dataclass
class Niche:
    # ... existing fields ...
    is_active: bool = True
    auto_collect_enabled: bool = False  # ✅ NEW: Explicit opt-in for periodic collection
    auto_collect_interval_hours: int = 3  # ✅ NEW: Collection frequency (default 3h)
    created_at: str = ""
    updated_at: str = ""
```

**Default Behavior**:
- New niches: `auto_collect_enabled = False` (manual collection only)
- User must toggle ON in UI to enable periodic collection
- Prevents wasting Meta API calls on abandoned/test niches

**Business Logic**:
```python
# In collect_scheduler Lambda
def handler(event: dict, context) -> dict:
    # Only get niches with auto_collect_enabled = True
    niches = NicheRepo.list_all_with_auto_collect()  # ✅ Filter by flag

    for niche in niches:
        # Check if enough time has passed since last collection
        last_run = CollectionRepo.get_latest_for_niche(niche.id)
        if last_run:
            hours_since = calculate_hours_since(last_run.started_at)
            if hours_since < niche.auto_collect_interval_hours:
                continue  # Skip, not time yet

        # Trigger collection...
```

#### 0.2 Frontend: Niche Settings UI

**Location**: `NicheWorkspaceView.vue` → Settings Tab

**New UI Section**: "Automatic Collection"

```vue
<template>
  <div class="auto-collect-settings">
    <div class="setting-header">
      <h3>⏰ Automatic Collection</h3>
      <span class="badge" :class="niche.auto_collect_enabled ? 'active' : 'inactive'">
        {{ niche.auto_collect_enabled ? 'ENABLED' : 'DISABLED' }}
      </span>
    </div>

    <div class="setting-description">
      <p>
        When enabled, MetaAds will automatically refresh ads for this niche every
        {{ niche.auto_collect_interval_hours }} hours.
      </p>
      <p class="info">
        💡 <strong>Tip:</strong> Enable this for niches you actively monitor.
        Leave disabled for test or archived niches to save costs.
      </p>
    </div>

    <div class="setting-controls">
      <!-- Toggle Switch -->
      <label class="toggle">
        <input
          type="checkbox"
          v-model="autoCollectEnabled"
          @change="handleToggleAutoCollect"
        >
        <span class="slider"></span>
        <span class="label">Enable automatic collection</span>
      </label>

      <!-- Interval Selector (only show if enabled) -->
      <div v-if="autoCollectEnabled" class="interval-selector">
        <label>Collection frequency:</label>
        <select v-model="collectionInterval" @change="handleUpdateInterval">
          <option value="2">Every 2 hours (high activity)</option>
          <option value="3">Every 3 hours (recommended)</option>
          <option value="6">Every 6 hours (low activity)</option>
          <option value="12">Every 12 hours (minimal)</option>
        </select>
      </div>

      <!-- Last Collection Info -->
      <div v-if="lastCollection" class="last-collection-info">
        <span class="label">Last automatic collection:</span>
        <span class="value">{{ formatRelativeTime(lastCollection.started_at) }}</span>
        <span v-if="lastCollection.status === 'completed'" class="status success">
          ✓ {{ lastCollection.ads_new }} new, {{ lastCollection.ads_updated }} updated
        </span>
        <span v-else-if="lastCollection.status === 'error'" class="status error">
          ✗ Error: {{ lastCollection.error_message }}
        </span>
      </div>

      <!-- Cost Estimate -->
      <div v-if="autoCollectEnabled" class="cost-estimate">
        <span class="label">Estimated cost:</span>
        <span class="value">
          ~${{ estimateMonthlyCost(niche.keywords.length, collectionInterval) }}/month
        </span>
        <small class="info">Based on Meta API usage</small>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { nicheApi } from '@/services/api'

const props = defineProps({
  niche: {
    type: Object,
    required: true
  },
  lastCollection: {
    type: Object,
    default: null
  }
})

const autoCollectEnabled = ref(props.niche.auto_collect_enabled || false)
const collectionInterval = ref(props.niche.auto_collect_interval_hours || 3)

async function handleToggleAutoCollect() {
  try {
    await nicheApi.updateNiche(props.niche.slug, {
      auto_collect_enabled: autoCollectEnabled.value
    })

    // Show success message
    showNotification({
      type: 'success',
      message: autoCollectEnabled.value
        ? '✓ Automatic collection enabled'
        : '✓ Automatic collection disabled'
    })
  } catch (error) {
    console.error('Failed to update auto-collect:', error)
    // Revert toggle
    autoCollectEnabled.value = !autoCollectEnabled.value
  }
}

async function handleUpdateInterval() {
  try {
    await nicheApi.updateNiche(props.niche.slug, {
      auto_collect_interval_hours: parseInt(collectionInterval.value)
    })

    showNotification({
      type: 'success',
      message: `✓ Collection interval updated to ${collectionInterval.value} hours`
    })
  } catch (error) {
    console.error('Failed to update interval:', error)
  }
}

function estimateMonthlyCost(keywordCount, intervalHours) {
  // 30 days × (24 hours / interval) × keywords × 50 ads × $0.0001 per API call
  const collectionsPerMonth = 30 * (24 / intervalHours)
  const apiCallsPerMonth = collectionsPerMonth * keywordCount * 50
  const cost = apiCallsPerMonth * 0.0001
  return cost.toFixed(2)
}

function formatRelativeTime(isoString) {
  // Helper to format "2 hours ago", "3 days ago", etc.
  const date = new Date(isoString)
  const now = new Date()
  const diffMs = now - date
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))

  if (diffHours < 1) return 'Less than 1 hour ago'
  if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`
  const diffDays = Math.floor(diffHours / 24)
  return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`
}
</script>

<style scoped>
.auto-collect-settings {
  background: var(--color-bg-secondary);
  border-radius: var(--radius-lg);
  padding: var(--spacing-4);
  margin-top: var(--spacing-4);
}

.setting-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-3);
}

.badge {
  padding: var(--spacing-1) var(--spacing-2);
  border-radius: var(--radius-full);
  font-size: var(--font-size-sm);
  font-weight: 600;
}

.badge.active {
  background: var(--color-success-100);
  color: var(--color-success-700);
}

.badge.inactive {
  background: var(--color-gray-100);
  color: var(--color-gray-600);
}

.toggle {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  cursor: pointer;
}

.cost-estimate {
  margin-top: var(--spacing-3);
  padding: var(--spacing-2);
  background: var(--color-warning-50);
  border-left: 3px solid var(--color-warning-500);
  border-radius: var(--radius-md);
}
</style>
```

#### 0.3 Backend: Update Niche Endpoints

**Update `PUT /api/niches/{slug}` Handler**:
```python
# lambda_src/niches/handler.py

def _update_niche(event: dict) -> dict:
    """Update niche settings."""
    user_id = _get_user_id(event)
    slug = _path_params(event).get("slug", "")
    body = json.loads(event.get("body", "{}"))

    niche = NicheRepo.get_by_slug(user_id, slug)
    if not niche:
        return _response(404, {"success": False, "error": "Niche not found"})

    # Allow updating auto_collect settings
    if "auto_collect_enabled" in body:
        niche.auto_collect_enabled = body["auto_collect_enabled"]

    if "auto_collect_interval_hours" in body:
        interval = int(body["auto_collect_interval_hours"])
        if interval not in [2, 3, 6, 12]:
            return _response(400, {"success": False, "error": "Invalid interval"})
        niche.auto_collect_interval_hours = interval

    # ... existing update logic ...

    NicheRepo.update(niche)

    return _response(200, {
        "success": True,
        "data": niche.to_dict()
    })
```

**New Repo Method** (`niche_repo.py`):
```python
@staticmethod
def list_all_with_auto_collect() -> List[Niche]:
    """
    Return all niches with auto_collect_enabled = True.
    Used by periodic collection scheduler.
    """
    table = get_table()
    items = []
    scan_kwargs = {
        "FilterExpression": (
            Attr("entity_type").eq("NICHE") &
            Attr("is_active").eq(True) &
            Attr("auto_collect_enabled").eq(True)  # ✅ Only enabled niches
        ),
    }

    while True:
        resp = table.scan(**scan_kwargs)
        items.extend(resp.get("Items", []))

        if "LastEvaluatedKey" not in resp:
            break
        scan_kwargs["ExclusiveStartKey"] = resp["LastEvaluatedKey"]

    return [Niche.from_item(i) for i in items]
```

#### 0.4 Migration Strategy

**For Existing Niches**:
```python
# One-time migration script (optional)
# Default all existing niches to auto_collect_enabled = False
# Users must explicitly enable

def migrate_existing_niches():
    """Set auto_collect_enabled = False for all existing niches."""
    niches = NicheRepo.list_all_active()

    for niche in niches:
        if not hasattr(niche, 'auto_collect_enabled'):
            niche.auto_collect_enabled = False
            niche.auto_collect_interval_hours = 3
            NicheRepo.update(niche)

    print(f"Migrated {len(niches)} niches to opt-in model")
```

**User Communication**:
- Show banner in UI: "🆕 New Feature: Automatic Collection — Enable it in Niche Settings!"
- Email notification (optional): "Keep your ads fresh with automatic collection"

---

### Phase 1: Core Infrastructure (MVP)

#### 1.1 Add `last_seen_at` to Ad Model

**Rationale**: Track ad freshness independently of initial collection.

**Schema Change** (`models.py` - Ad dataclass):
```python
@dataclass
class Ad:
    # ... existing fields ...
    collected_at: str = ""        # First time we saw this ad (immutable)
    last_seen_at: str = ""        # Most recent collection that found this ad (updated)

    # Optional: Track staleness
    collection_miss_count: int = 0  # Times we ran collection but didn't see this ad
```

**Migration**: Add field with default value (backward compatible):
```python
# Existing ads get last_seen_at = collected_at on first update
if not existing.last_seen_at:
    ad.last_seen_at = existing.collected_at
```

**Update Logic** (`ad_repo.py` - `create_or_update`):
```python
def create_or_update(ad: Ad) -> Tuple[Ad, bool]:
    existing = AdRepo.get(ad.niche_id, ad.meta_ad_id)
    is_new = existing is None
    now = now_iso8601()

    if is_new:
        ad.collected_at = now
        ad.last_seen_at = now        # ✅ First time seeing
        ad.collection_miss_count = 0
    else:
        ad.collected_at = existing.collected_at  # ✅ Preserve original
        ad.last_seen_at = now                    # ✅ Update to NOW
        ad.collection_miss_count = 0             # ✅ Reset (we found it!)
        # Preserve saved state
        ad.is_saved = existing.is_saved
        ad.saved_at = existing.saved_at
        ad.saved_tags = existing.saved_tags

    table.put_item(Item=ad.to_item())
    return ad, is_new
```

#### 1.2 EventBridge Scheduler for Periodic Collection

**Terraform Resource** (`infra/eventbridge.tf` - new file):
```hcl
# EventBridge Scheduler — triggers collection every 3 hours
resource "aws_scheduler_schedule" "periodic_collection" {
  name        = "${var.project_name}-${var.environment}-periodic-collection"
  description = "Trigger ad collection every 3 hours for all active niches"

  flexible_time_window {
    mode = "OFF"
  }

  # Every 3 hours: 0 */3 * * *
  schedule_expression = "cron(0 */3 * * ? *)"

  # US Eastern timezone (adjust as needed)
  schedule_expression_timezone = "America/New_York"

  target {
    arn      = aws_lambda_function.collect_scheduler.arn
    role_arn = aws_iam_role.eventbridge_scheduler.arn

    input = jsonencode({
      trigger_source = "eventbridge_periodic"
      collection_mode = "refresh"  # vs "initial"
    })
  }
}

# IAM role for EventBridge Scheduler
resource "aws_iam_role" "eventbridge_scheduler" {
  name = "${var.project_name}-${var.environment}-eventbridge-scheduler"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "scheduler.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })
}

# Permission to invoke Lambda
resource "aws_iam_role_policy" "eventbridge_invoke_lambda" {
  role = aws_iam_role.eventbridge_scheduler.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "lambda:InvokeFunction"
      Resource = aws_lambda_function.collect_scheduler.arn
    }]
  })
}
```

#### 1.3 New Lambda: Collect Scheduler

**Purpose**: Query all active niches and trigger collection for each.

**Code** (`lambda_src/collect_scheduler/handler.py` - new):
```python
"""
Collect Scheduler Lambda — triggered by EventBridge every 3 hours.

Responsibilities:
    1. Query all active niches from DynamoDB
    2. For each niche, invoke collect_trigger Lambda
    3. Log scheduling metrics (niches processed, errors)

Environment variables:
    DYNAMODB_TABLE          — DynamoDB table name
    COLLECT_TRIGGER_ARN     — ARN of collect_trigger Lambda
"""

import json
import logging
import os
import boto3

from app.dynamodb.niche_repo import NicheRepo

logger = logging.getLogger()
logger.setLevel(logging.INFO)

lambda_client = boto3.client("lambda")


def handler(event: dict, context) -> dict:
    """
    Scheduler entry point — invoked by EventBridge.
    """
    trigger_source = event.get("trigger_source", "unknown")
    collection_mode = event.get("collection_mode", "refresh")

    logger.info(f"Periodic collection started: source={trigger_source} mode={collection_mode}")

    # Get niches with auto_collect_enabled = True
    niches = NicheRepo.list_all_with_auto_collect()  # ✅ Only opt-in niches
    logger.info(f"Found {len(niches)} niches with auto-collect enabled")

    triggered = 0
    errors = 0
    skipped = 0

    for niche in niches:
        try:
            # Check if enough time has passed since last collection
            last_run = CollectionRepo.get_latest_for_niche(niche.id)
            if last_run:
                hours_since = _calculate_hours_since(last_run.started_at)
                if hours_since < niche.auto_collect_interval_hours:
                    logger.info(
                        f"Skipping {niche.slug}: last run {hours_since:.1f}h ago, "
                        f"interval is {niche.auto_collect_interval_hours}h"
                    )
                    skipped += 1
                    continue

            # Invoke collect_trigger for this niche
            payload = {
                "niche_id": niche.id,
                "user_id": niche.user_id,
                "keywords": niche.keywords,
                "countries": niche.countries,
                "platforms": niche.platforms,
                "limit": 50,  # Default for periodic refresh
                "trigger_source": "periodic_scheduler",
            }

            lambda_client.invoke(
                FunctionName=os.environ["COLLECT_TRIGGER_ARN"],
                InvocationType="Event",  # Async
                Payload=json.dumps(payload),
            )

            triggered += 1
            logger.info(f"Triggered collection for niche {niche.slug} ({niche.id})")

        except Exception as exc:
            errors += 1
            logger.error(f"Failed to trigger collection for niche {niche.id}: {exc}")

    result = {
        "triggered": triggered,
        "skipped": skipped,
        "errors": errors,
        "total_niches_with_auto_collect": len(niches),
    }

    logger.info(f"Periodic collection complete: {result}")
    return result


def _calculate_hours_since(iso_timestamp: str) -> float:
    """Calculate hours elapsed since given timestamp."""
    from datetime import datetime
    then = datetime.fromisoformat(iso_timestamp.replace("Z", "+00:00"))
    now = datetime.now(then.tzinfo)
    delta = now - then
    return delta.total_seconds() / 3600
```

**Required Repo Methods** (`collection_repo.py`):
```python
@staticmethod
def get_latest_for_niche(niche_id: str) -> Optional[CollectionRun]:
    """Get the most recent collection run for a niche."""
    runs = CollectionRepo.list_for_niche(niche_id, limit=1)
    return runs[0] if runs else None
```

#### 1.4 Update Terraform Lambda Definitions

**Add to `infra/lambda.tf`**:
```hcl
# Collect Scheduler Lambda
resource "aws_lambda_function" "collect_scheduler" {
  function_name = "${var.project_name}-${var.environment}-collect-scheduler"
  role          = aws_iam_role.lambda_collector.arn
  handler       = "handler.handler"
  runtime       = "python3.11"
  timeout       = 60  # 1 minute (just schedules, doesn't collect)
  memory_size   = 256

  filename         = "../lambda_src/collect_scheduler.zip"
  source_code_hash = filebase64sha256("../lambda_src/collect_scheduler.zip")

  layers = [aws_lambda_layer_version.shared.arn]

  environment {
    variables = {
      DYNAMODB_TABLE       = aws_dynamodb_table.main.name
      COLLECT_TRIGGER_ARN  = aws_lambda_function.collect_trigger.arn
      AWS_REGION          = var.aws_region
    }
  }
}

# Grant scheduler permission to invoke other Lambdas
resource "aws_iam_role_policy" "lambda_collector_invoke" {
  role = aws_iam_role.lambda_collector.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "lambda:InvokeFunction"
      Resource = [
        aws_lambda_function.collect_trigger.arn,
        aws_lambda_function.collect_worker.arn,
      ]
    }]
  })
}
```

---

### Phase 2: Auditing & Analytics

#### 2.1 Collection Health Endpoint

**New API Route**: `GET /api/admin/collection/health`

**Returns**:
```json
{
  "success": true,
  "data": {
    "last_24h": {
      "total_runs": 42,
      "successful": 38,
      "errors": 4,
      "avg_ads_per_run": 47.3,
      "total_ads_collected": 1987,
      "total_ads_new": 234,
      "total_ads_updated": 1753
    },
    "by_niche": [
      {
        "niche_id": "abc-123",
        "niche_name": "Fitness Over 40",
        "slug": "fitness-40",
        "last_collection": "2026-02-27T03:00:00Z",
        "hours_since_last": 2.5,
        "recent_runs": 8,
        "avg_ads_found": 52.3,
        "success_rate": 0.95,
        "keywords_failing": ["very niche long tail keyword"]
      }
    ],
    "failing_keywords": [
      {
        "keyword": "super specific long tail",
        "niches": ["fitness-40", "health-seniors"],
        "attempts": 12,
        "successes": 0,
        "last_attempt": "2026-02-27T05:00:00Z"
      }
    ]
  }
}
```

**Lambda Handler** (`lambda_src/admin/handler.py` - extend existing):
```python
def _get_collection_health(event: dict) -> dict:
    """Aggregate collection statistics for monitoring."""
    from datetime import datetime, timedelta

    # Get all collection runs from last 24h
    cutoff = (datetime.now() - timedelta(hours=24)).isoformat() + "Z"

    # Query all niches
    niches = NicheRepo.list_all_active()

    stats_by_niche = []
    keyword_stats = {}

    for niche in niches:
        runs = CollectionRepo.list_for_niche(niche.id, limit=50)

        # Filter to last 24h
        recent_runs = [r for r in runs if r.started_at >= cutoff]

        if recent_runs:
            last_run = recent_runs[0]
            hours_since = (datetime.now() - datetime.fromisoformat(last_run.started_at.replace("Z", "+00:00"))).total_seconds() / 3600

            successful = [r for r in recent_runs if r.status == "completed"]
            avg_ads = sum(r.ads_found for r in successful) / len(successful) if successful else 0

            # Track keyword performance
            failing_keywords = []
            for keyword in niche.keywords:
                keyword_runs = [r for r in recent_runs if keyword in r.keywords_used]
                keyword_successes = [r for r in keyword_runs if r.ads_found > 0]

                if len(keyword_runs) > 3 and len(keyword_successes) == 0:
                    failing_keywords.append(keyword)

                    if keyword not in keyword_stats:
                        keyword_stats[keyword] = {
                            "keyword": keyword,
                            "niches": [],
                            "attempts": 0,
                            "successes": 0,
                        }
                    keyword_stats[keyword]["niches"].append(niche.slug)
                    keyword_stats[keyword]["attempts"] += len(keyword_runs)
                    keyword_stats[keyword]["successes"] += len(keyword_successes)

            stats_by_niche.append({
                "niche_id": niche.id,
                "niche_name": niche.name,
                "slug": niche.slug,
                "last_collection": last_run.started_at,
                "hours_since_last": round(hours_since, 1),
                "recent_runs": len(recent_runs),
                "avg_ads_found": round(avg_ads, 1),
                "success_rate": len(successful) / len(recent_runs),
                "keywords_failing": failing_keywords,
            })

    # Aggregate totals
    all_runs = []
    for niche in niches:
        all_runs.extend([r for r in CollectionRepo.list_for_niche(niche.id, limit=50) if r.started_at >= cutoff])

    successful = [r for r in all_runs if r.status == "completed"]

    return _response(200, {
        "success": True,
        "data": {
            "last_24h": {
                "total_runs": len(all_runs),
                "successful": len(successful),
                "errors": len([r for r in all_runs if r.status == "error"]),
                "avg_ads_per_run": sum(r.ads_found for r in successful) / len(successful) if successful else 0,
                "total_ads_collected": sum(r.ads_found for r in successful),
                "total_ads_new": sum(r.ads_new for r in successful),
                "total_ads_updated": sum(r.ads_updated for r in successful),
            },
            "by_niche": stats_by_niche,
            "failing_keywords": list(keyword_stats.values()),
        },
    })
```

#### 2.2 Stale Ad Detection

**Query for Stale Ads**:
```python
def get_stale_ads(niche_id: str, hours_threshold: int = 12) -> List[Ad]:
    """
    Find ads that haven't been seen in recent collections.
    Indicates either:
    - Ad ended (Meta stopped showing it)
    - Collection not running (system issue)
    """
    from datetime import datetime, timedelta

    cutoff = (datetime.now() - timedelta(hours=hours_threshold)).isoformat() + "Z"

    table = get_table()
    resp = table.query(
        KeyConditionExpression=(
            Key("PK").eq(Ad.pk(niche_id)) &
            Key("SK").begins_with("AD#")
        ),
        FilterExpression=Attr("last_seen_at").lt(cutoff) & Attr("is_active").eq(True),
    )

    return [Ad.from_item(i) for i in resp.get("Items", [])]
```

**Use Case**: Flag ads in UI with ⚠️ if `last_seen_at > 12 hours ago`.

#### 2.3 Frontend Dashboard

**New Admin View**: `/admin/collection-health`

**Components**:
1. **Overall Stats Card**:
   - Last 24h: X runs, Y successful, Z errors
   - Total ads collected: new vs updated

2. **Per-Niche Table**:
   - Niche name | Last collection | Avg ads/run | Success rate
   - Red flag if `hours_since_last > 6`

3. **Failing Keywords List**:
   - Keyword | Niches using it | Attempts | Success rate
   - Action: "Remove from niches" button

---

### Phase 3: Advanced Features (Optional)

#### 3.1 Adaptive Collection Frequency

**Problem**: Not all niches need 3-hour refresh.

**Solution**: Adjust frequency based on activity:
```python
def calculate_collection_interval(niche_id: str) -> int:
    """Return hours between collections based on ad churn."""
    recent_runs = CollectionRepo.list_for_niche(niche_id, limit=10)

    # Calculate average new ads per run
    avg_new = sum(r.ads_new for r in recent_runs) / len(recent_runs)

    if avg_new > 10:
        return 2  # High activity: every 2 hours
    elif avg_new > 2:
        return 3  # Medium activity: every 3 hours (default)
    else:
        return 6  # Low activity: every 6 hours
```

#### 3.2 Cost Optimization

**Track Meta API Usage**:
```python
@dataclass
class CollectionRun:
    # ... existing fields ...
    meta_api_calls: int = 0      # Number of API requests made
    meta_api_cost: float = 0.0   # Estimated cost ($0.01 per 100 calls)
```

**Monthly Cost Report**:
- Total API calls
- Cost per niche
- ROI: Cost vs ads discovered

---

## Implementation Roadmap

### Week 1: User Opt-In + Core Infrastructure
- [ ] Day 1: Add `auto_collect_enabled` + `auto_collect_interval_hours` to Niche model
- [ ] Day 2: Build frontend UI for auto-collect toggle in Settings tab
- [ ] Day 3: Update niche update API endpoint to support auto-collect settings
- [ ] Day 4: Add `last_seen_at` field to Ad model + update logic
- [ ] Day 5: Create `collect_scheduler` Lambda with opt-in filtering

### Week 2: Scheduling + Testing
- [ ] Day 1-2: Add EventBridge Scheduler Terraform
- [ ] Day 2-3: Test end-to-end periodic collection with opt-in niches
- [ ] Day 3-4: Add CloudWatch alarms for collection failures
- [ ] Day 4-5: Migration script for existing niches (set auto_collect = false)

### Week 3: Auditing & Analytics
- [ ] Day 1-2: Implement collection health API endpoint
- [ ] Day 3-4: Build frontend admin dashboard for collection monitoring
- [ ] Day 5: Test stale ad detection + documentation

---

## UI Flow Examples

### Example 1: User Enables Auto-Collect

**Initial State** (Settings tab):
```
┌──────────────────────────────────────┐
│ ⏰ Automatic Collection    [DISABLED]│
├──────────────────────────────────────┤
│ When enabled, MetaAds will           │
│ automatically refresh ads for this   │
│ niche every 3 hours.                 │
│                                      │
│ 💡 Tip: Enable this for niches you  │
│ actively monitor.                    │
│                                      │
│ [ ] Enable automatic collection      │
└──────────────────────────────────────┘
```

**After Toggle ON**:
```
┌──────────────────────────────────────┐
│ ⏰ Automatic Collection    [ENABLED] │
├──────────────────────────────────────┤
│ ✓ Automatic collection enabled       │
│                                      │
│ Collection frequency:                │
│ [Every 3 hours (recommended) ▼]     │
│                                      │
│ Last automatic collection:           │
│ Never (will start within 3 hours)   │
│                                      │
│ Estimated cost: ~$3.20/month         │
│ Based on 2 keywords × 3h interval   │
└──────────────────────────────────────┘
```

**After First Collection**:
```
┌──────────────────────────────────────┐
│ ⏰ Automatic Collection    [ENABLED] │
├──────────────────────────────────────┤
│ Last automatic collection:           │
│ 2 hours ago                          │
│ ✓ 12 new, 38 updated                │
│                                      │
│ Next collection in: ~1 hour          │
└──────────────────────────────────────┘
```

### Example 2: Cost Warning for High-Frequency

**User selects "Every 2 hours"**:
```
┌──────────────────────────────────────┐
│ ⚠️ Warning                           │
├──────────────────────────────────────┤
│ High collection frequency will       │
│ increase Meta API costs.             │
│                                      │
│ Estimated cost: ~$4.80/month         │
│ (vs $3.20/month for 3-hour interval)│
│                                      │
│ [Cancel] [Confirm - I understand]   │
└──────────────────────────────────────┘
```

### Example 3: Disabled Niche (Inactive)

```
┌──────────────────────────────────────┐
│ ⏰ Automatic Collection    [DISABLED]│
├──────────────────────────────────────┤
│ ⚠️ This niche is inactive            │
│                                      │
│ Automatic collection is not          │
│ available for inactive niches.       │
│                                      │
│ [Activate Niche First]               │
└──────────────────────────────────────┘
```

---

## Success Metrics

### System Health
- ✅ **Collection Reliability**: >95% success rate
- ✅ **Latency**: <30s to schedule all niches
- ✅ **Freshness**: No ads with `last_seen_at > 6 hours`

### Operational Insights
- ✅ **Keyword Performance**: Identify failing keywords within 24h
- ✅ **Cost Tracking**: Meta API usage under budget
- ✅ **Ad Churn Rate**: % of ads that are new vs updated

---

## Risk Mitigation

### Risk 1: Lambda Cold Starts Delaying Scheduler

**Impact**: Scheduler takes >1min, causes timeout.

**Mitigation**:
- Use provisioned concurrency for `collect_scheduler`
- Or increase timeout to 5 minutes

### Risk 2: DynamoDB Throttling from Scan

**Impact**: `list_all_active()` scan exceeds RCUs.

**Mitigation**:
- Add GSI: `GSI3PK = ACTIVE_NICHE`, `GSI3SK = NICHE#<id>`
- Query GSI instead of scan

### Risk 3: EventBridge Not Triggering

**Impact**: Collections stop running, no alerts.

**Mitigation**:
- CloudWatch alarm: `CollectionRun` count < threshold in 6h window
- SNS notification to admin email

---

## Cost Estimate

### Scenario: 10 Niches with Auto-Collect Enabled

**Assumptions**:
- 10 niches with `auto_collect_enabled = True`
- Average 2 keywords per niche
- 3-hour collection interval (8 collections/day)
- 50 ads per keyword per collection

### AWS Resources
- **EventBridge Scheduler**: $0.00 (included in free tier)
- **Lambda Executions**:
  - Scheduler: 8/day × $0.0000002 = $0.000048/day = $0.0015/month
  - Additional overhead: ~$1/month
- **DynamoDB**:
  - CollectionRun items: ~240/day × 1KB = 7.2MB/month
  - Storage cost: $0.02/month
  - Read/write costs: ~$2/month

**Total AWS**: ~$3/month

### Meta API Costs (Variable by Adoption)
- **Per niche**: 8 collections/day × 2 keywords × 50 ads = 800 API requests/day
- **10 niches**: 8,000 requests/day
- **Meta API free tier**: 200/hour = 4,800/day
- **Overage**: 3,200/day × $0.0001 = $0.32/day = $9.60/month

**Total for 10 Niches**: ~$13/month

### Cost Scaling (Based on Opt-In Rate)

| Niches w/ Auto-Collect | API Calls/Day | Monthly Cost |
|------------------------|---------------|--------------|
| 1 niche                | 800           | $0 (free tier) |
| 5 niches               | 4,000         | $0 (free tier) |
| 10 niches              | 8,000         | ~$13          |
| 20 niches              | 16,000        | ~$37          |
| 50 niches              | 40,000        | ~$106         |

**Key Insight**: With opt-in model, users control costs. If only 3 niches have auto-collect enabled, cost is $0 (stays in free tier).

---

## Benefits of Opt-In Model

### 1. Cost Control
- **Problem**: Automatic collection for all niches = high Meta API costs
- **Solution**: Users only enable for niches they actively use
- **Result**: Typical user with 10 niches enables 2-3 → stays in free tier ($0)

### 2. Resource Efficiency
- **Problem**: Wasting API calls on test/abandoned niches
- **Solution**: Explicit opt-in ensures intentional usage
- **Result**: System only collects for niches users care about

### 3. User Awareness
- **Problem**: Users don't realize collection is happening (billing surprise)
- **Solution**: Prominent UI with cost estimate before enabling
- **Result**: Informed consent, no billing surprises

### 4. Flexibility
- **Problem**: One-size-fits-all interval doesn't work for everyone
- **Solution**: Per-niche interval configuration (2h, 3h, 6h, 12h)
- **Result**: High-activity niches get frequent updates, low-activity get less

### 5. Easy Troubleshooting
- **Problem**: "Why isn't my niche updating?"
- **Solution**: Check Settings → "Auto-collect is DISABLED"
- **Result**: Clear cause-and-effect, users can self-diagnose

---

## Open Questions

1. **Should we retry failed collections immediately?**
   - Pro: Faster recovery from transient errors
   - Con: Might hit rate limits
   - Recommendation: Wait for next scheduled run (3h later)

2. **How long to keep CollectionRun history?**
   - Recommendation: 30 days (DynamoDB TTL)
   - Aggregate stats to separate table for long-term analytics

3. **Should periodic collections use lower `limit` than manual?**
   - Manual: 50-100 ads (user expects full results)
   - Periodic: 25-50 ads (just refresh, not deep discovery)
   - Recommendation: 50 for consistency

---

## Conclusion

This plan provides:
- ✅ **Automated collection** every 3 hours
- ✅ **Comprehensive auditing** to distinguish bugs from long-tail keywords
- ✅ **Ad freshness tracking** with `last_seen_at`
- ✅ **Admin dashboard** for monitoring collection health
- ✅ **Cost-effective** implementation (~$13/month)

**Next Steps**: Review plan → Approve → Start Week 1 implementation.
