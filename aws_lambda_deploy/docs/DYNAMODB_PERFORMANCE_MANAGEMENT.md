# DynamoDB Performance Management: What You Actually Do

> **Context**: This document is a companion to [`PLAN_MIGRATE_TO_SERVERLESS.md`](./PLAN_MIGRATE_TO_SERVERLESS.md).
> It covers everything from design-time optimization through long-term scaling strategies for the MetaAds DynamoDB single-table design.

## Table of Contents

- [Design-Time Optimization (90% of Performance Work)](#design-time-optimization-90-of-performance-work)
- [When Performance Issues Hit — Your Options](#when-performance-issues-hit---your-options)
  - [Option A: Add a GSI (Plan Carefully)](#option-a-add-a-gsi-plan-carefully)
  - [Option B: Denormalize More Data (Cheaper Than GSI)](#option-b-denormalize-more-data-cheaper-than-gsi)
  - [Option C: Use FilterExpression (Application-Side Filtering)](#option-c-use-filterexpression-application-side-filtering)
  - [Option D: Caching (Cheapest Solution for Reads)](#option-d-caching-cheapest-solution-for-reads)
  - [Option E: Switch to Provisioned Capacity](#option-e-switch-to-provisioned-capacity)
- [Monitoring: What to Watch](#monitoring-what-to-watch)
- [Likely Performance Issues for MetaAds](#likely-performance-issues-for-metaads)
  - [Problem 1: Ad Search with Many Filters](#problem-1-ad-search-with-many-filters)
  - [Problem 2: Saved Ads Growing Large (Hot Partition)](#problem-2-saved-ads-growing-large-hot-partition)
  - [Problem 3: Sorting Ads by Variant Count](#problem-3-sorting-ads-by-variant-count)
  - [Problem 4: Collection Runs History Growing](#problem-4-collection-runs-history-growing)
- [When to Migrate Away from DynamoDB](#when-to-migrate-away-from-dynamodb)
- [Recommended Action Plan](#recommended-action-plan)

---

### Design-Time Optimization (90% of Performance Work)

**Critical: Define ALL access patterns BEFORE creating the table.**

For MetaAds, we've already identified 8 access patterns in Phase 2:

| Access Pattern | Method | Index Used |
|----------------|--------|------------|
| List niches by user | Query | Base table (PK=USER#id, SK=NICHE#*) |
| Get niche by slug | Query | GSI2 (PK=USER_SLUG#id#slug) |
| List ads by niche | Query | Base table (PK=NICHE#id, SK=AD#*) |
| List ads by page | Query | GSI1 (PK=NICHE_PAGE#niche#page) |
| List saved ads | Query | GSI2 (PK=NICHE_SAVED#id, sorted by saved_at) |
| Get ad by ID | Query | Base table (PK=NICHE#id, SK=AD#meta_id) |
| List collection runs | Query | Base table (PK=NICHE#id, SK=RUN#timestamp) |
| Search ads by text | Query + FilterExpression | Base table + app-side filter |

**Why This Matters:**

```python
# ❌ BAD: Realizing later you need to query by CTA type
# Would require:
# 1. Add GSI3 via Terraform (5 minutes)
# 2. DynamoDB backfills GSI3 (6+ HOURS for 100K items)
# 3. Costs double during backfill (read all items to populate GSI)
# 4. Application downtime or complex migration logic

# ✅ GOOD: Planned upfront in Phase 2
# Already have filtering via FilterExpression:
response = table.query(
    KeyConditionExpression='PK = :niche AND begins_with(SK, :ad)',
    FilterExpression='cta_detected = :cta',  # Scans after fetching
)
# Trade-off: Uses more RCUs, but no GSI needed (cost-effective at small scale)
```

---

### When Performance Issues Hit — Your Options

Unlike SQL where you add an index, DynamoDB offers 5 strategies:

#### **Option A: Add a GSI (Plan Carefully)**

**When to use:**
- New access pattern that's impossible with base table + existing GSIs
- Query needs to be extremely fast (<10ms) and can't use FilterExpression
- Access pattern is frequent (>1000x per day)

**Cost:**
- Time: 6-12 hours backfill for 100K items
- Money: Doubles storage cost ($0.25/GB) + separate RCU/WCU

**How to add:**

```hcl
# infra/dynamodb.tf
resource "aws_dynamodb_table" "main" {
  # ... existing config ...

  # Add new GSI
  global_secondary_index {
    name            = "GSI3-CTA-Performance"
    hash_key        = "GSI3PK"
    range_key       = "GSI3SK"
    projection_type = "KEYS_ONLY"  # or ALL (more expensive)
  }
}

# Update repository to populate GSI3PK/GSI3SK on writes
# backend/app/dynamodb/ad_repo.py
def create_ad(ad_data):
    item = {
        'PK': f"NICHE#{ad_data['niche_id']}",
        'SK': f"AD#{ad_data['meta_ad_id']}",
        'GSI3PK': f"CTA#{ad_data['cta_detected']}",  # New
        'GSI3SK': f"{ad_data['days_active']:05d}",    # New (zero-padded for sorting)
        # ... other attributes
    }
    table.put_item(Item=item)
```

**Backfill script:**

```python
# scripts/backfill_gsi3.py
# REQUIRED: Must populate GSI3PK/GSI3SK for existing items
scan_response = table.scan()
for item in scan_response['Items']:
    table.update_item(
        Key={'PK': item['PK'], 'SK': item['SK']},
        UpdateExpression='SET GSI3PK = :pk, GSI3SK = :sk',
        ExpressionAttributeValues={
            ':pk': f"CTA#{item.get('cta_detected', 'unknown')}",
            ':sk': f"{item.get('days_active', 0):05d}"
        }
    )
```

---

#### **Option B: Denormalize More Data (Cheaper Than GSI)**

Instead of adding a GSI, **duplicate data** to avoid complex queries.

**Example: Ad variant grouping**

```python
# Current (Phase 2, line 98): Application-side grouping
# Fetch all ads for niche, then group in Python by (page_name + headline)
ads = query_ads_by_niche(niche_id)
variants = group_by_variant(ads)  # O(n) in memory

# Alternative: Denormalize variant_id into Ad items
item = {
    'PK': f"NICHE#{niche_id}",
    'SK': f"AD#{meta_ad_id}",
    'variant_id': hashlib.md5(f"{page_name}{headline}".encode()).hexdigest()[:8],
    # ... other fields
}

# Then query with FilterExpression:
table.query(
    KeyConditionExpression='PK = :niche',
    FilterExpression='variant_id = :variant'
)
```

**Cost:** Storage is cheap ($0.25/GB vs $0.47/mo per GSI minimum).

---

#### **Option C: Use FilterExpression (Application-Side Filtering)**

For non-critical queries, fetch more data and filter in Lambda.

**How it works:**

```python
# Query fetches ALL ads for niche, then filters by CTA
response = table.query(
    KeyConditionExpression='PK = :niche AND begins_with(SK, :ad)',
    FilterExpression='cta_detected = :cta AND days_active > :days',
    ExpressionAttributeValues={
        ':niche': f"NICHE#{niche_id}",
        ':ad': 'AD#',
        ':cta': 'learn more',
        ':days': 30
    }
)
# Returns only filtered items, but you PAY for all scanned items
```

**Cost Trade-off:**
- RCUs consumed = ALL items scanned (not just returned)
- If niche has 1000 ads, filtering to 50 costs 1000 item reads
- At $0.25 per 1M reads = negligible until millions of queries

**When to use:**
- Rare queries (<100x per day)
- Filter selectivity >10% (if filtering 1000 items to 100, acceptable)

---

#### **Option D: Caching (Cheapest Solution for Reads)**

For read-heavy workloads (MetaAds is 90% reads):

**Lambda-level cache:**

```python
# backend/app/utils/cache.py
import time
from functools import wraps

_cache = {}

def cached(ttl_seconds=300):
    """Cache function results for TTL seconds."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{args}:{kwargs}"
            now = time.time()

            if cache_key in _cache:
                result, timestamp = _cache[cache_key]
                if now - timestamp < ttl_seconds:
                    return result  # Cache hit

            # Cache miss - fetch from DynamoDB
            result = func(*args, **kwargs)
            _cache[cache_key] = (result, now)
            return result
        return wrapper
    return decorator

# Usage in ad_repo.py
@cached(ttl_seconds=300)  # 5-minute cache
def get_ads_by_niche(niche_id, filters):
    return table.query(...)
```

**DAX (DynamoDB Accelerator):**

```hcl
# infra/dax.tf
resource "aws_dax_cluster" "main" {
  cluster_name       = "metaads-cache"
  iam_role_arn       = aws_iam_role.dax.arn
  node_type          = "dax.t3.small"  # $0.04/hr = $30/month
  replication_factor = 1  # Single node (dev/small workloads)
}

# Lambda connects to DAX endpoint instead of DynamoDB
# All reads cached automatically (millisecond latency)
```

**When to use:**
- Read-heavy (>80% reads)
- Data changes slowly (ads run for days/weeks)
- Lambda cache: Free (uses Lambda memory)
- DAX: $30/month minimum (overkill for <1000 users)

---

#### **Option E: Switch to Provisioned Capacity**

If usage becomes predictable:

```hcl
# infra/dynamodb.tf
resource "aws_dynamodb_table" "main" {
  billing_mode = "PROVISIONED"  # Was: PAY_PER_REQUEST
  read_capacity_units  = 5      # $0.00065/hr/unit = $2.34/mo for 5 units
  write_capacity_units = 5      # $0.00325/hr/unit = $11.70/mo for 5 units

  # Enable auto-scaling for traffic spikes
  # (expands from 5 to 100 RCU automatically)
}
```

**Break-even calculation:**
- On-demand: $1.25 per 1M writes, $0.25 per 1M reads
- Provisioned: $0.00065/hr per RCU (1M reads/mo = 0.4 RCU on average)
- Break-even: ~7M writes/mo or 30M reads/mo

**For MetaAds:** Stay on-demand until >500 users (projected: 100K writes/mo).

---

### Monitoring: What to Watch

Unlike SQL (slow query logs), DynamoDB needs different CloudWatch metrics:

```hcl
# infra/monitoring.tf
resource "aws_cloudwatch_metric_alarm" "dynamodb_throttle" {
  alarm_name          = "DynamoDB-ThrottledRequests"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "UserErrors"  # Includes ThrottledRequests
  namespace           = "AWS/DynamoDB"
  period              = 60
  statistic           = "Sum"
  threshold           = 0
  alarm_description   = "DynamoDB throttling detected - under-provisioned or bad query"

  dimensions = {
    TableName = aws_dynamodb_table.main.name
  }
}

resource "aws_cloudwatch_metric_alarm" "high_consumed_rcu" {
  alarm_name          = "DynamoDB-HighReadCapacity"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "ConsumedReadCapacityUnits"
  namespace           = "AWS/DynamoDB"
  period              = 300  # 5 minutes
  statistic           = "Sum"
  threshold           = 1000  # Alert if >1000 RCU in 5 min (cost spike)
  alarm_description   = "High read capacity - check for inefficient queries"
}

resource "aws_cloudwatch_metric_alarm" "high_latency" {
  alarm_name          = "DynamoDB-HighLatency"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "SuccessfulRequestLatency"
  namespace           = "AWS/DynamoDB"
  period              = 60
  statistic           = "Average"
  threshold           = 100  # Alert if p50 latency >100ms
  alarm_description   = "DynamoDB queries slow - investigate access patterns"
}
```

**Key Metrics Dashboard:**

| Metric | Normal Range | Action Threshold | What to Do |
|--------|--------------|------------------|------------|
| **UserErrors** | 0 | >0 | Check for missing GSI or bad KeyConditionExpression |
| **ConsumedReadCapacity** | <100 RCU/min | >1000 RCU/min | Add caching or optimize FilterExpression |
| **ConsumedWriteCapacity** | <20 WCU/min | >200 WCU/min | Check for write amplification (GSIs multiply writes) |
| **SuccessfulRequestLatency** | <20ms p50 | >100ms p50 | Query too broad or hot partition |
| **ThrottledRequests** | 0 | >0 | Should NEVER happen on-demand mode (indicates bug) |

---

### Likely Performance Issues for MetaAds

Based on the schema design (Phase 2), here are realistic problems and solutions:

#### **Problem 1: Ad Search with Many Filters**

**Scenario:**
```python
# User filters: days_active>30 AND cta='learn more' AND has_emoji=True AND is_active=True
# Current plan (Phase 2, line 161): Query + FilterExpression
response = table.query(
    KeyConditionExpression='PK = :niche AND begins_with(SK, :ad)',
    FilterExpression='days_active > :days AND cta_detected = :cta AND has_emoji = :emoji'
)
# If niche has 5000 ads, filters to 50 → pays for 5000 item reads
```

**Solution Options:**
1. **Denormalize "performance_score"** (days_active * engagement_proxy):
   ```python
   performance_score = days_active * (1.5 if has_emoji else 1.0) * (1.2 if cta else 1.0)
   # Store in SK for native sorting: SK = f"AD#{performance_score:08d}#{meta_ad_id}"
   # Query top 50 directly without filtering
   ```

2. **Add GSI3 for days_active sorting**:
   ```python
   GSI3PK = f"NICHE#{niche_id}"
   GSI3SK = f"{days_active:05d}#{meta_ad_id}"  # Zero-padded for sort
   # Query GSI3 in descending order, filter remaining fields
   ```

3. **Lambda-level cache for "top ads per niche"** (5-minute TTL):
   ```python
   @cached(ttl_seconds=300)
   def get_top_ads(niche_id):
       # Cached result, only queries DynamoDB once per 5 min
   ```

**Recommended:** Option 3 (caching) for <1000 users, Option 1 (denormalize) if >1000.

---

#### **Problem 2: Saved Ads Growing Large (Hot Partition)**

**Scenario:**
```python
# Power user saves 10,000 ads over 6 months
# Current: GSI2 query on NICHE_SAVED#{niche_id}
# Problem: All 10K items in ONE partition (exceeds 10GB partition limit or hot partition throttle)
```

**Solution: Shard by month**

```python
# Change SK to include month prefix
saved_at = "2026-02-22T14:30:00Z"
month = saved_at[:7]  # "2026-02"
SK = f"SAVED#{month}#AD#{meta_ad_id}"

# Query becomes:
table.query(
    KeyConditionExpression='PK = :niche AND begins_with(SK, :month)',
    ExpressionAttributeValues={
        ':niche': f"NICHE_SAVED#{niche_id}",
        ':month': f"SAVED#2026-02"  # Current month
    },
    ScanIndexForward=False  # Descending order
)

# Frontend fetches "current month" by default, with pagination for older months
```

**When to implement:** If any user has >1000 saved ads (monitor `saved_count` per niche).

---

#### **Problem 3: Sorting Ads by Variant Count**

**Scenario:**
```python
# User wants to see ads sorted by "number of variants" (most variants first)
# Current: ads.py:143-148 - fetch all, group in Python, sort by len(group)
# Problem: Requires fetching ALL ads to calculate counts (can't paginate efficiently)
```

**Current approach (Application-side)**:

```python
# backend/app/dynamodb/ad_repo.py
def get_ads_grouped_by_variant(niche_id, sort_by_variant_count=True):
    # 1. Fetch all ads for niche
    response = table.query(
        KeyConditionExpression='PK = :niche AND begins_with(SK, :ad)',
        ExpressionAttributeValues={
            ':niche': f"NICHE#{niche_id}",
            ':ad': 'AD#'
        }
    )

    ads = response['Items']

    # 2. Group by variant (page_name + headline)
    from collections import defaultdict
    import hashlib

    groups = defaultdict(list)
    for ad in ads:
        variant_key = f"{ad['page_name']}|{ad.get('headline', '')}"
        groups[variant_key].append(ad)

    # 3. Sort by variant count
    if sort_by_variant_count:
        sorted_groups = sorted(
            groups.values(),
            key=lambda group: len(group),
            reverse=True  # Most variants first
        )
    else:
        sorted_groups = groups.values()

    return sorted_groups
```

**Performance**:
- ✅ Works well for <5,000 ads per niche (typical case)
- ✅ No additional DynamoDB cost (single query)
- ✅ Simple logic, no data duplication
- ❌ Must fetch ALL ads (can't paginate DynamoDB query)
- ❌ O(n) memory usage in Lambda

**When this becomes a problem**:
- Niche has >10,000 ads (>1MB DynamoDB response)
- Variant sorting is the primary use case (>50% of queries)

**Solution Options (if needed):**

**Option A: Denormalize variant_count into each ad** (Simple but write amplification)

```python
# When creating/updating ads:
def create_or_update_ad(niche_id, ad_data):
    variant_id = hashlib.md5(
        f"{ad_data['page_name']}{ad_data['headline']}".encode()
    ).hexdigest()[:8]

    # Count existing ads with same variant_id (expensive!)
    variant_count = count_ads_by_variant(niche_id, variant_id)

    # Store count in item
    item = {
        'PK': f"NICHE#{niche_id}",
        'SK': f"AD#{ad_data['meta_ad_id']}",
        'variant_id': variant_id,
        'variant_count': variant_count,  # Denormalized count
        # ... other fields
    }
    table.put_item(Item=item)

    # Update ALL other ads in same variant group (write amplification!)
    update_variant_counts(niche_id, variant_id, new_count=variant_count)

# Query with FilterExpression + Lambda sorting
response = table.query(
    KeyConditionExpression='PK = :niche AND begins_with(SK, :ad)',
)
ads = sorted(response['Items'], key=lambda x: x['variant_count'], reverse=True)
```

**Trade-off**: Each ad creation updates 1-50 other ads (expensive writes).

**Option B: Separate variant metadata items** (Recommended if >10K ads)

```python
# Store variant metadata as separate items in same table:
# Item type 1: Ad
{
    'PK': 'NICHE#abc-123',
    'SK': 'AD#meta-ad-456',
    'page_name': 'Company X',
    'headline': 'Best product ever',
    'variant_id': 'a3f5c8e1',
    # ... ad fields
}

# Item type 2: Variant metadata (NEW)
{
    'PK': 'NICHE#abc-123',
    'SK': 'VARIANT#a3f5c8e1',  # Variant metadata item
    'variant_id': 'a3f5c8e1',
    'page_name': 'Company X',
    'headline': 'Best product ever',
    'variant_count': 5,  # Count of ads with this variant
    'last_updated': '2026-02-22T10:30:00Z'
}

# When ad is created:
def create_ad(niche_id, ad_data):
    variant_id = generate_variant_id(ad_data['page_name'], ad_data['headline'])

    # 1. Create ad item
    table.put_item(Item={
        'PK': f"NICHE#{niche_id}",
        'SK': f"AD#{ad_data['meta_ad_id']}",
        'variant_id': variant_id,
        # ... other fields
    })

    # 2. Increment variant count (atomic)
    table.update_item(
        Key={
            'PK': f"NICHE#{niche_id}",
            'SK': f"VARIANT#{variant_id}"
        },
        UpdateExpression='ADD variant_count :inc SET page_name = :page, headline = :headline',
        ExpressionAttributeValues={
            ':inc': 1,
            ':page': ad_data['page_name'],
            ':headline': ad_data['headline']
        }
    )

# Query sorted by variant count:
def get_ads_by_variant_count(niche_id, limit=50):
    # 1. Query variant metadata items
    variant_response = table.query(
        KeyConditionExpression='PK = :niche AND begins_with(SK, :variant)',
        ExpressionAttributeValues={
            ':niche': f"NICHE#{niche_id}",
            ':variant': 'VARIANT#'
        }
    )
    variants = variant_response['Items']

    # 2. Sort by variant_count in Lambda
    variants_sorted = sorted(variants, key=lambda x: x['variant_count'], reverse=True)
    top_variants = variants_sorted[:10]  # Top 10 variants

    # 3. Fetch ads for top variants (parallel queries)
    ads = []
    for variant in top_variants:
        ad_response = table.query(
            KeyConditionExpression='PK = :niche AND begins_with(SK, :ad)',
            FilterExpression='variant_id = :variant_id',
            ExpressionAttributeValues={
                ':niche': f"NICHE#{niche_id}",
                ':ad': 'AD#',
                ':variant_id': variant['variant_id']
            }
        )
        ads.extend(ad_response['Items'])

    return ads
```

**Trade-off**: 2-3 queries instead of 1, but enables pagination by variant count.

**Option C: GSI3 with zero-padded variant_count in SK** (Most efficient, but complex)

```python
# Store variant_count in GSI3SK for native DynamoDB sorting:
item = {
    'PK': f"NICHE#{niche_id}",
    'SK': f"AD#{meta_ad_id}",
    'GSI3PK': f"NICHE#{niche_id}",  # Same as PK
    'GSI3SK': f"{variant_count:05d}#{variant_id}",  # Sort by count
    'variant_id': variant_id,
    # ... other fields
}

# Query GSI3 in descending order (native DynamoDB sort)
response = table.query(
    IndexName='GSI3',
    KeyConditionExpression='GSI3PK = :niche AND begins_with(GSI3SK, :prefix)',
    ExpressionAttributeValues={
        ':niche': f"NICHE#{niche_id}",
        ':prefix': ''  # All variants
    },
    ScanIndexForward=False,  # Descending order (highest count first)
    Limit=50
)
```

**Trade-off**: Must update GSI3SK for ALL ads in variant when count changes (write amplification + GSI backfill cost).

---

**Recommended Approach by Scale:**

| Niche Size | Approach | Reason |
|------------|----------|--------|
| <5,000 ads | Application-side (current) | Simple, no extra cost, works fine |
| 5,000-10,000 ads | Application-side + caching | Cache grouped results for 5 minutes |
| >10,000 ads | Option B (variant metadata items) | Enables pagination, 2-3 queries but manageable |
| >50,000 ads | Option C (GSI3 with variant_count in SK) | Native DynamoDB sorting, but write amplification cost |

**For MVP**: Stick with application-side grouping (current plan). Monitor per-niche ad counts in CloudWatch. If any niche exceeds 5,000 ads, implement variant metadata items.

---

#### **Problem 4: Collection Runs History Growing**

**Scenario:**
```python
# After 1 year: 365 collection runs per niche (daily collections)
# Query slows down: PK=NICHE#{id}, SK begins_with("RUN#")
```

**Solution: TTL (Time To Live)**

```hcl
# infra/dynamodb.tf
resource "aws_dynamodb_table" "main" {
  # ... existing config ...

  ttl {
    enabled        = true
    attribute_name = "ttl_expiry"  # Unix timestamp
  }
}
```

```python
# backend/app/dynamodb/collection_repo.py
def create_collection_run(niche_id, run_data):
    now = int(time.time())
    ttl_expiry = now + (90 * 24 * 60 * 60)  # Delete after 90 days

    item = {
        'PK': f"NICHE#{niche_id}",
        'SK': f"RUN#{now_iso8601()}#{run_id}",
        'ttl_expiry': ttl_expiry,  # DynamoDB auto-deletes after this timestamp
        # ... other fields
    }
    table.put_item(Item=item)
```

**Cost:** Free (DynamoDB deletes items within 48 hours of expiry, no charge).

---

### When to Migrate Away from DynamoDB

You'd only migrate to SQL/PostgreSQL if:

❌ **Complex joins across 5+ tables** (your design has 1 table!)
❌ **Analytics queries** (GROUP BY, SUM, AVG across millions of rows) → Use DynamoDB Streams → S3 → Athena instead
❌ **Need ACID transactions across items** (DynamoDB has TransactWriteItems, but limited to 25 items)
❌ **Frequent schema changes** (adding columns) → DynamoDB is schemaless (not an issue)

✅ **Your use case stays in DynamoDB because:**
- Simple access patterns (list, get, search within niche)
- Single-table design works perfectly
- Read-heavy workload (perfect for DynamoDB + caching)
- No complex aggregations (stats computed in Lambda)
- Cost-effective at scale ($0.87/mo vs $50/mo for RDS t3.micro)

---

### Recommended Action Plan

#### **Phase 1: Launch (Week 1-4)**
1. ✅ Deploy with current schema design (Phase 2, Step 2.1) - already optimized
2. ✅ Implement CloudWatch alarms (Phase 7, Step 7.3)
3. ✅ Set up Cost Explorer budget alert ($5/month threshold)

#### **Phase 2: Monitor (Week 1-4 after launch)**
1. **Daily**: Check CloudWatch dashboard
   - ConsumedReadCapacity: Should be <100 RCU/min for 100 users
   - SuccessfulRequestLatency: Should be <20ms p50
   - Any UserErrors or ThrottledRequests = immediate investigation

2. **Weekly**: Review Cost Explorer
   - DynamoDB cost should be <$0.10/week for 100 users
   - If >$1/week = inefficient queries (likely FilterExpression over-use)

3. **Identify slow queries**:
   ```python
   # Add timing to all repository methods
   import time

   def get_ads_by_niche(niche_id):
       start = time.time()
       result = table.query(...)
       duration_ms = (time.time() - start) * 1000

       if duration_ms > 100:
           logger.warning(f"Slow query: get_ads_by_niche took {duration_ms}ms")

       return result
   ```

#### **Phase 3: Optimize (Month 1-2)**
1. **Add Lambda-level caching** (free, 10-minute implementation):
   ```python
   # backend/app/utils/cache.py (create this)
   # Copy cached() decorator from Option D above

   # Apply to read-heavy methods:
   @cached(ttl_seconds=300)
   def get_ads_by_niche(niche_id):
       ...
   ```

2. **Expected impact**: 70% reduction in RCUs (most queries hit cache)

#### **Phase 4: Scale (Month 3-6)**
1. **If traffic grows >500 users**:
   - Evaluate provisioned capacity (break-even at ~7M writes/mo)
   - Consider DAX if reads >10M/month ($30/month for dax.t3.small)

2. **If new access pattern emerges** (e.g., "search ads by landing domain"):
   - Option A: Add GSI4 if query is frequent (>1000x/day)
   - Option B: Denormalize `landing_domain` into items (cheaper)
   - Option C: Use FilterExpression if query is rare (<100x/day)

3. **If saved ads >1000 per niche**:
   - Implement monthly sharding (Problem 2 solution above)

#### **Phase 5: Long-term (Month 6+)**
1. **Quarterly review**:
   - Check if any access pattern uses >50% of total RCUs (optimize that first)
   - Review GSI usage: Any GSI with <1% of queries? Consider removing.

2. **Annual review**:
   - Export 1 month of data to S3 via DynamoDB export ($0.10/GB)
   - Run analytics queries in Athena (complex aggregations)
   - Identify trends: Are certain niches growing >10K ads? May need sharding.

3. **Never worry about**:
   - ❌ Index maintenance (DynamoDB handles automatically)
   - ❌ Query plan optimization (no query planner)
   - ❌ Vacuuming/fragmentation (no concept in DynamoDB)
   - ❌ Connection pooling (HTTP API, not persistent connections)

---

**Summary:**
- **SQL mindset**: "Add index when slow query appears" → ❌ Expensive in DynamoDB
- **DynamoDB mindset**: "Design all access patterns upfront, monitor costs, cache reads, denormalize writes" → ✅ Cost-effective

Your schema (Phase 2) already follows best practices. The key is **monitoring and caching**, not continuous index tuning.
