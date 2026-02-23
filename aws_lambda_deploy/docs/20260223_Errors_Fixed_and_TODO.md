# Deployment Session - February 23, 2026

## Summary

This document tracks the issues fixed during the second AWS Lambda debugging session and the
open TODO items discovered during testing. The session started from a partially-working deploy
(login OK, niches 500 error) and ended with core features functional: niche list, ad collection,
search/results view (grouped variant rows, correct pagination), save/unsave, and saved-ads tab.

---

## Issues Fixed

### 1. ✅ GET /api/niches → 500 (Invalid ProjectionExpression: attribute name #s not defined)

**Error (CloudWatch):**
```
botocore.exceptions.ClientError: An error occurred (ValidationException) when calling
the Query operation: Invalid ProjectionExpression: attribute name #s not defined
```

**Root Cause:**
Dead code in `niche_repo.py:get_stats()` called the internal `_query()` helper with
`"#s, completed_at, ads_found"` as a projection. The `_query` helper has no
`ExpressionAttributeNames` parameter so `#s` was undefined.
The correct query with `ExpressionAttributeNames={"#s": "status"}` already existed
immediately below the dead call.

**Fix Applied:**
Removed the dead `_query("RUN#", "#s, completed_at, ads_found")` line from `get_stats()`.

**File Modified:** `lambda_layers/shared/python/app/dynamodb/niche_repo.py`

---

### 2. ✅ PATCH /api/niches/{slug} → 500 (NicheRepo.update() missing argument 'user_id')

**Error (CloudWatch):**
```
TypeError: NicheRepo.update() missing 1 required positional argument: 'user_id'
```

**Root Cause:**
`_update_niche` in the niches handler called `NicheRepo.update(niche.id, **updates)`
but the repo signature is `update(niche_id, user_id, **kwargs)`.
Same bug in `_delete_niche`: `NicheRepo.delete(niche.id)` instead of
`NicheRepo.delete(user_id, niche.id)`.

**Fix Applied:**
```python
# _update_niche
NicheRepo.update(niche.id, user_id, **updates)

# _delete_niche
NicheRepo.delete(user_id, niche.id)
```

**File Modified:** `lambda_src/niches/handler.py`

---

### 3. ✅ collect_worker fatal error: No module named 'pandas'

**Error (CloudWatch):**
```
[ERROR] collect_worker fatal error: No module named 'pandas'
```

**Root Cause:**
`ad_parser.py` had `import pandas as pd` at module top level.
Pandas is not included in the Lambda layer (too large at ~30MB).
The collect worker only calls `parse_ad()` which returns a plain dict —
it never calls `parse_batch()` which returns a DataFrame.

**Fix Applied:**
Moved `import pandas as pd` inside the `parse_batch()` method body (lazy import).
The collect worker is now unaffected.

**File Modified:** `lambda_layers/shared/python/ad_parser.py`

---

### 4. ✅ Results view showing zero ads (API Gateway route mismatches)

**Symptoms:**
- Collection worker completed successfully (`new=100` in logs)
- DynamoDB confirmed 100 AD# items for the niche
- Results list showed nothing; ads Lambda responded in ~25ms (404 fallback)

**Root Cause:**
Multiple API Gateway routes were wrong — the deployed route keys didn't match
what the Lambda handlers expected:

| Deployed (broken) | Should be |
|---|---|
| `GET /api/niches/{slug}/ads` | `GET /api/niches/{slug}/ads/search` |
| `GET .../ads/{ad_id}/variants` | `GET .../ads/{ad_id}/variants/analysis` |
| `POST /api/niches/{slug}/ads/clear` | `DELETE /api/niches/{slug}/ads/clear` |
| `PATCH .../ads/{ad_id}/save` (only) | `POST` (save) + `DELETE` (unsave) + `PATCH` (update) |
| *(missing)* | `GET /api/niches/{slug}/pages` |

**Fix Applied:** Corrected all five mismatches in `infra/api_gateway.tf`.

**File Modified:** `aws_lambda_deploy/infra/api_gateway.tf`

---

### 5. ✅ AdTable/AdGrid showing zero ads (group_by_variant format mismatch)

**Symptoms:**
Routes were correct, DynamoDB had 100 ads, but the results list rendered nothing.

**Root Cause:**
The backend returns pre-grouped variant objects by default:
```json
{ "variant_key": "...", "page_name": "...", "headline": "...", "ads": [...] }
```
But `AdTable.groupedAds` was re-grouping assuming flat ad objects, causing every
field access (`ad.body`, `ad.is_active`, etc.) to return `undefined`.

**Fix Applied:**
- `AdTable.groupedAds`: replaced client-side grouping with a direct `.map()` over
  the pre-grouped backend response — one item = one row.
- `AdGrid`: detect grouped vs flat items via `item.ads` presence and render accordingly.
- `api.js`: removed the temporary `group_by_variant: false` override added during
  debugging; backend now controls grouping as designed.

**Files Modified:**
- `frontend/src/components/AdTable.vue`
- `frontend/src/components/AdGrid.vue`
- `frontend/src/services/api.js`

---

### 6. ✅ Pagination showing "5 ads found" instead of 100

**Two separate bugs:**

**Bug A — Pagination controls never rendered:**
Backend returned `{ page, per_page, total, has_next }` but frontend components
checked `pagination.pages > 1` to show Previous/Next buttons.
`pages` was `undefined`, so the controls never rendered.

**Fix:** Added `pages` (total page count) and `has_prev` to the pagination response
in `lambda_src/ads/handler.py`.

**Bug B — "5 ads found" header (groups instead of ads):**
The results header showed `pagination.total` (number of variant groups = 5)
instead of the total raw ad count (= 100).

**Fix:** Backend now returns `total_ads` (raw count) alongside `total` (group count).
Frontend header changed from `pagination.total` to `pagination.total_ads`.

**Files Modified:**
- `lambda_src/ads/handler.py`
- `lambda_layers/shared/python/app/dynamodb/ad_repo.py`
- `frontend/src/views/SearchView.vue`

---

### 7. ✅ Save button dead in Ad Detail view (meta_ad_id vs id mismatch)

**Symptoms:**
Clicking "☆ Save" in the Ad Detail panel had no visible effect.

**Root Cause:**
The API routes use `meta_ad_id` (the Meta Ad Library numeric ID, used as DynamoDB SK)
in the URL. But all frontend calls passed `ad.id` (the internal UUID),
causing every `AdRepo.get()` lookup to return `None` silently.

Affected calls: `fetchAdDetail`, `fetchRelatedAds`, `saveAd`, `unsaveAd`,
`updateSavedAd`, `toggleSave`, `updateAdInList`, `handleSelectAd`,
`handleUpdateNotes`, `handleViewRelated`, and `selectedAdId` highlight bindings.

**Fix Applied:**
Replaced every `ad.id` reference with `ad.meta_ad_id` across:
- `frontend/src/stores/ads.js`
- `frontend/src/views/SearchView.vue`
- `frontend/src/views/SavedView.vue`

Also fixed `updateAdInList` to search inside `group.ads[]` since `this.ads` now
holds grouped variant objects, not flat ads.

---

### 8. ✅ Saved tab empty (AdGrid expected grouped objects, got flat ads)

**Root Cause:**
After the variant-group refactor, `AdGrid` assumed every item was a group with
`item.ads[0]`. But `SavedView` passes flat ad objects from `AdRepo.list_saved()`
(which returns `to_dict()` objects, not groups).
Every card rendered `ad = undefined`.

**Fix Applied:**
`AdGrid` now checks for `item.ads` presence:
- if `item.ads` exists → grouped item, render `item.ads[0]` as the card
- otherwise → flat ad, render `item` directly

**File Modified:** `frontend/src/components/AdGrid.vue`

---

### 9. ✅ "Your Niches" card showing 13 ads instead of 100

**Root Cause:**
`niche_repo.py:get_stats()` used an internal `_query()` helper that made a single
DynamoDB `.query()` call with no pagination loop. DynamoDB can return a
`LastEvaluatedKey` even for small result sets, silently dropping remaining items.

**Fix Applied:**
Added a `while True` / `ExclusiveStartKey` pagination loop inside `_query()`,
matching the pattern used everywhere else in the codebase.

**File Modified:** `lambda_layers/shared/python/app/dynamodb/niche_repo.py`

---

### 10. ✅ Decimal type from DynamoDB serialized as string (days_active: "1" vs 1)

**Root Cause:**
boto3's high-level DynamoDB resource returns Number attributes as Python `Decimal`.
`json.dumps(..., default=str)` in the Lambda `_response()` helper serialized
`Decimal("1")` as `"1"` (string) instead of `1` (number), breaking numeric
comparisons and sort operations in the frontend.

**Fix Applied:**
`Ad.from_item()` now explicitly casts `days_active` and `text_length` to `int()`.

**File Modified:** `lambda_layers/shared/python/app/dynamodb/models.py`

---

## Current Status (end of session)

| Feature | Status |
|---|---|
| Authentication (Clerk) | ✅ Working |
| Your Niches view (correct ad count) | ✅ Working |
| Create / Edit / Delete niche | ✅ Working |
| Manual ad collection | ✅ Working |
| Results view — grouped rows (20 rows/page) | ✅ Working |
| Results view — "N ads found" header | ✅ Working |
| Results view — pagination controls | ✅ Working |
| Ad Detail panel | ✅ Working |
| Save / Unsave ad | ✅ Working |
| Saved tab | ✅ Working |
| Variant Analysis modal | ⚠️  Partially working (see TODO #2, #3, #4) |
| Periodic collection (scheduler) | ❌ Not implemented |
| Custom domain | ❌ Not configured |

---

## TODO

### 1. 🔴 HIGH — "Sort by Variants" filter not working

**Symptoms:**
Selecting "Variants" in the Sort dropdown has no visible effect on the results order.

**Likely Root Cause:**
The frontend sends `sort=variants` as a query param. The backend `AdRepo.search()`
doesn't read a `sort` param from `filters` — it always sorts groups by
`len(group.ads)` descending inside `_group_by_variant()`. Need to verify whether
the sort param is even being passed through the filter pipeline and honoured.

**Files to check:**
- `frontend/src/components/SearchFilters.vue` — what params are sent
- `lambda_src/ads/handler.py` — is `sort` extracted from query params?
- `lambda_layers/shared/python/app/dynamodb/ad_repo.py` — `_group_by_variant()` sort logic

---

### 2. 🔴 HIGH — Variant Analysis broken for "Booked in Love"

**Symptoms:**
Opening the Variant Analysis modal for a "Booked in Love" ad shows an error
or incomplete data.

**Likely Root Cause:**
`GET /api/niches/{slug}/ads/{ad_id}/variants/analysis` calls `AdRepo.get_related()`
using `page_id`. "Booked in Love" ads may have inconsistent `page_id` values
across collected items (some `None`, some populated), causing the related-ads query
to return fewer items than expected or fail.

**Files to check:**
- `lambda_src/ads/handler.py` → `_get_variant_analysis()`
- `lambda_layers/shared/python/app/dynamodb/ad_repo.py` → `get_related()`
- DynamoDB items: verify `page_id` field is consistently populated for this page

---

### 3. 🟡 MEDIUM — "View 6 other campaigns" but modal says "Total Variants: 7"

**Symptoms:**
The AdTable row for "Booked in Love" shows a "+6" expand button (meaning 6 variants
in the group beyond the first = 7 total), but the Variant Analysis modal header
displays "Total Variants: 7" while the "View N other campaigns" link says 6.

**Likely Root Cause:**
Off-by-one: the button count is `group.ads.length - 1` (variants beyond the first)
while the modal likely uses `group.ads.length` or `relatedAds.length` (total).
One of the two counts includes/excludes the currently-displayed ad inconsistently.

**Files to check:**
- `frontend/src/components/AdTable.vue` — expand button count expression
- `frontend/src/components/VariantAnalysis.vue` (or similar) — "Total Variants" display
- `lambda_src/ads/handler.py` → `_get_related()` — whether the current ad is excluded

---

### 4. 🟡 MEDIUM — Variant Analysis not showing for "Romantic Lover"

**Symptoms:**
The Variant Analysis button/link is visible for "Booked in Love" but not for
"Romantic Lover", even though "Romantic Lover" likely has multiple ads in the niche.

**Likely Root Cause:**
The "View related / Variant Analysis" feature is gated on `relatedCount > 0`.
`fetchRelatedAds` calls `GET .../ads/{ad_id}/related` which queries by `page_id`.
If "Romantic Lover" ads were collected without a `page_id` value (or with a
different value), the GSI1 query returns 0 results and the button is hidden.

**Files to check:**
- `lambda_layers/shared/python/app/dynamodb/ad_repo.py` → `get_related()` query
- DynamoDB: inspect `page_id` field on "Romantic Lover" AD# items
- `ad_parser.py` → `parse_ad()` — is `page_id` always extracted from the Meta API response?

---

### 5. 🟡 MEDIUM — Browser cache: restore last niche view state

**Description:**
When a user returns to a niche they previously visited, the app should restore:
- Last active tab (Search / Saved / Settings)
- Last search filters (keyword, is_active, platform, sort order)
- Last view mode (table vs cards)
- Last selected Ad Detail (if any)

**Suggested Approach:**
Use `localStorage` keyed by `niche_slug`. Persist state on filter change,
view-mode toggle, and ad selection. Rehydrate in `onMounted()` before the
initial `searchAds()` call so the first fetch uses the restored filters.

**Files to update:**
- `frontend/src/stores/ads.js` — persist/rehydrate `filters` and `viewMode`
- `frontend/src/views/NicheWorkspaceView.vue` — persist active tab
- `frontend/src/views/SearchView.vue` — restore viewMode and selectedAd

---

### 6. 🟡 MEDIUM — Implement periodic collection every 3 hours

**Description:**
Ads should be automatically refreshed every 3 hours per niche (or per keyword)
without manual user intervention.

**Suggested Approach — EventBridge Scheduler:**
1. Add an `aws_scheduler_schedule` Terraform resource that fires every 3 hours
2. Target: `collect_trigger` Lambda (already handles collection orchestration)
3. Payload: iterate all active niches from DynamoDB and trigger a worker per keyword

**Alternative — DynamoDB TTL + Stream:**
Set a `next_collection_at` TTL field on each niche; a DynamoDB Stream triggers
the collector when the item "expires".

**Files to update / create:**
- `aws_lambda_deploy/infra/lambda.tf` — add EventBridge Scheduler resource
- `aws_lambda_deploy/infra/iam.tf` — grant scheduler permission to invoke Lambda
- `aws_lambda_deploy/lambda_src/collect_trigger/handler.py` — support "sweep all niches" mode

---

### 7. 🟢 LOW — Point metads.app to CloudFront via Cloudflare

**Description:**
Add a CNAME record in Cloudflare for `metads.app` (and `www.metads.app`) pointing
to the CloudFront distribution, and configure the distribution to accept the
custom domain with an ACM certificate.

**Steps:**
1. **ACM certificate** — request `metads.app` + `*.metads.app` in `us-east-1`
   (CloudFront requires us-east-1 for ACM certs)
2. **Terraform** — add `aliases` and `viewer_certificate` to the
   `aws_cloudfront_distribution` resource in `infra/cloudfront.tf`
3. **Cloudflare** — add `CNAME metads.app → d3ba787xl1d882.cloudfront.net`
   with proxy **disabled** (grey cloud — CloudFront handles TLS)
4. **Terraform apply** to update the distribution

**Resources:**
- CloudFront distribution: `E9Q8645UTHPJD` (`d3ba787xl1d882.cloudfront.net`)
- Target domain: `metads.app`

---

### 8. 🟢 LOW — Consider renaming app to "adsmania.app" (post-MVP)

**Description:**
`adsmania.app` is being considered as the production app name once the MVP is
validated. Defer until core features are stable.

**Checklist when ready:**
- [ ] Register `adsmania.app` domain
- [ ] Request ACM certificate for `adsmania.app` + `*.adsmania.app`
- [ ] Update CloudFront aliases
- [ ] Update Clerk allowed redirect URLs
- [ ] Update `cors_allow_origins` in `dev.tfvars` / `prod.tfvars`
- [ ] Update branding strings in the Vue frontend
- [ ] Update API Gateway CORS headers

---

### 9. 🟡 MEDIUM — Get real Clerk webhook secret (carried over from Feb 22)

**Current State:**
Webhook secret is still placeholder: `whsec_placeholder_get_from_clerk_dashboard`.
The `POST /api/auth/webhook` endpoint won't validate Clerk events without it.

**Action Required:**
1. Go to https://dashboard.clerk.com → Webhooks
2. Add endpoint: `https://f4k5jdd47a.execute-api.us-east-1.amazonaws.com/api/auth/webhook`
3. Subscribe to `user.created`, `user.updated`, `user.deleted`
4. Copy the signing secret and update AWS Secrets Manager:
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

## Deployment Resources

### URLs
- **Frontend (CloudFront):** https://d3ba787xl1d882.cloudfront.net/
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
- **Lambda Layer (current):** `arn:aws:lambda:us-east-1:645069181643:layer:metaads-dev-shared-layer:7`
- **CloudFront Distribution:** E9Q8645UTHPJD

---

## Quick Commands Reference

```bash
# Rebuild + deploy Lambda code and layer
cd aws_lambda_deploy
./scripts/package.sh
cd infra && terraform apply -var-file=dev.tfvars -auto-approve

# Deploy frontend only
BUCKET=$(terraform -chdir=infra output -raw frontend_bucket_name)
npm --prefix ../frontend run build
aws s3 sync ../frontend/dist s3://$BUCKET --delete --profile metads
DIST_ID=$(terraform -chdir=infra output -raw cloudfront_distribution_id)
aws cloudfront create-invalidation --profile metads --distribution-id $DIST_ID --paths "/*"

# Tail Lambda logs
aws logs tail /aws/lambda/metaads-dev-ads      --profile metads --since 15m
aws logs tail /aws/lambda/metaads-dev-niches   --profile metads --since 15m
aws logs tail /aws/lambda/metaads-dev-saved    --profile metads --since 15m
aws logs tail /aws/lambda/metaads-dev-collect-worker --profile metads --since 15m

# Count ads in DynamoDB for a niche
NICHE_ID="849b0c47-7d1f-4037-abe2-e12afbead6f9"
aws dynamodb query --profile metads --region us-east-1 \
  --table-name metaads-dev-table \
  --key-condition-expression "PK = :pk AND begins_with(SK, :sk)" \
  --expression-attribute-values "{\":pk\":{\"S\":\"NICHE#$NICHE_ID\"},\":sk\":{\"S\":\"AD#\"}}" \
  --select COUNT
```

---

## Lessons Learned

1. **Paginate every DynamoDB query.** A single `.query()` call silently truncates
   results at the 1 MB page boundary even for small datasets if DynamoDB decides
   to paginate. Always use a `while True` / `ExclusiveStartKey` loop.

2. **Use `meta_ad_id` as the API identifier, not the internal UUID.**
   The DynamoDB SK is `AD#<meta_ad_id>`. Every URL parameter named `ad_id` in the
   API routes refers to `meta_ad_id`. The internal `id` (UUID) is only used
   internally and must never be sent in API paths.

3. **Backend grouping = frontend row count.**
   `AdRepo.search(group_by_variant=True)` paginates by *group count*, not raw ad
   count. The frontend must not re-group the response — it should render one row per
   item received. Pagination controls then show the correct "page N of M rows".

4. **Decimal from DynamoDB is not JSON-serialisable.**
   boto3 high-level resource returns numeric DynamoDB attributes as `Decimal`.
   Always cast to `int` or `float` in `from_item()` before the value reaches
   `json.dumps()`.

5. **Dead import at module level crashes the Lambda cold start.**
   If a module-level import fails (e.g. `import pandas`), the Lambda function fails
   every invocation, not just the code path that uses it.
   Keep heavyweight or optional imports lazy (inside the function body).

---

**Session Date:** February 23, 2026
**Duration:** ~5 hours
**Status:** Core app features working end-to-end on AWS serverless
**Next Priority:** Fix variant analysis (TODOs #1–#4), then periodic collection (#6)
