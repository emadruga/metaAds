# Andromeda Scoring Pipeline — Feasibility Results

## Document Purpose

This document records the results of Phase 1 of the Andromeda feasibility test, as defined in
`ANDROMEDA_FEASIBILITY_PLAN.md`. It covers steps 1–8 of the single-ad validation script:
token fetch → Playwright browser → snapshot navigation → networkidle wait → CDN URL extraction →
expiry check → MP4 download → thumbnail download.

**Test date**: 2026-03-10
**Instance**: `t3.small` (2 vCPU, 2 GB RAM), Amazon Linux 2023, `us-east-1`
**Reference ad**: `2162596270894996` (Lost Dutchman Leather Goods, Moda niche, ~35 days active)
**Test script**: `aws_feasibility/andromeda_single_ad_test.py`
**Raw results JSON**: `aws_feasibility/docs/ANDROMEDA_FEASIBILITY_RESULTS.json`

---

## Phase 1 Results — All 8 Steps PASSED (8/8)

| Step | Description | Status | Detail |
|---|---|---|---|
| 1 | Secrets Manager token fetch | ✅ PASS | token length=205, starts with `EAFuK2eb…` |
| 2 | Playwright headless Chromium launch | ✅ PASS | stealth=True, browser ready |
| 3 | Navigate to snapshot URL | ✅ PASS | `domcontentloaded` in **1.5s** |
| 4 | Wait for networkidle | ✅ PASS | idle in **1.1s** |
| 5 | Extract CDN URLs from DOM | ✅ PASS | `video=yes`, `poster=yes`, img_fallback=no |
| 6 | URL validity + expiry check | ✅ PASS | expires 2026-03-14 11:34 UTC (~106h remaining) |
| 7 | MP4 download to `/tmp` | ✅ PASS | **1.64 MB** in **0.2s** |
| 8 | Thumbnail download to `/tmp` | ✅ PASS | **275 KB** in **0.0s** |

**Total elapsed**: 34 seconds (including Chromium startup ~20s, actual page work ~2.6s, downloads <1s).

---

## Must-Pass Checklist (from Feasibility Plan)

| # | Must-Pass Check | Result | Notes |
|---|---|---|---|
| 1 | Snapshot loads in Playwright; `<video>` tag present in DOM | ✅ PASS | `video.src` and `video.poster` both non-null |
| 2 | CDN URLs extracted — both non-null and not expired | ✅ PASS | ~106h remaining on both URLs |
| 3 | MP4 download — file size > 1 MB, no error | ✅ PASS | 1.64 MB downloaded cleanly |
| 4 | FFmpeg frame extraction | **Not yet tested** | Phase 1 scope: steps 1–8 only |
| 5 | Claude API scoring | **Not yet tested** | Phase 1 scope: steps 1–8 only |
| 6 | DynamoDB write | **Not yet tested** | Phase 1 scope: steps 1–8 only |
| 7 | 10-ad batch success rate ≥ 80% | **Not yet tested** | Phase 2 scope |
| 8 | Peak RSS < 1.5 GB on t3.small | ✅ PASS | Peak observed ~347 MB / 1.9 GB available |

**Phase 1 verdict: GO** — the three checks relevant to steps 1–8 all pass cleanly.

---

## Infrastructure Observations

### IAM + Secrets Manager

`boto3` on the EC2 instance automatically acquired credentials via the IMDSv2 instance metadata
service. The IAM role `metaads-andromeda-feasibility-role` (attached via instance profile) had the
minimum required permission: `secretsmanager:GetSecretValue` on `metaads/dev/meta-api*`. No
credentials were injected manually into the instance.

### Playwright on Amazon Linux 2023

Playwright downloaded a **ubuntu24.04 fallback build** of Chromium (~167 MB) because Amazon Linux
2023 is not an officially listed platform. The browser ran correctly despite this. The
`playwright install-deps chromium` step (run as root in `user_data.sh`) failed with
`apt-get: command not found` — this is expected because Playwright's dep installer targets Debian-
based systems. The issue was pre-empted by a manual `dnf install` of all required system libraries
(step 2.5 in `user_data.sh`): `nss`, `atk`, `libdrm`, `pango`, `gtk3`, `xorg-x11-server-Xvfb`,
etc.

**Net result**: Chromium starts and renders pages correctly on AL2023 using the ubuntu fallback
binary + pre-installed dnf libraries. The `playwright install-deps` failure is cosmetic.

### playwright-stealth

`playwright-stealth` v2 was installed and imported successfully. The library issued a version
compatibility warning (minor API change between stealth 2.x and Playwright 1.58), but the patch
was applied and the test ran with `stealth=True`. No bot-detection was triggered.

### Memory Usage

Peak RSS at Chromium load was ~347 MB on the 2 GB instance — well within the 1.5 GB threshold.
This matches the plan's estimate of ~350 MB for a single-browser, single-page workload.

### Snapshot Page Render Time

The `domcontentloaded` event fired in 1.5s and the `networkidle` state was reached in 1.1s after
that. This is significantly faster than the 4–6s estimate in the plan, likely because the EC2
instance (same AWS region, `us-east-1`) has low latency to Meta's CDN and the page was served
without CAPTCHA friction.

---

## Extracted Asset Details

### Video URL

```
https://video-iad3-1.xx.fbcdn.net/o1/v/t2/f2/m412/AQN0W1TaDC-kVOaoQFKVhgv4p5VfkD2uobE3HgTf…mp4
  _nc_cat=101 _nc_sid=8bf8fe _nc_ht=video-iad3-1.xx.fbcdn.net
  efg=…xpv_progressive.VI_USECASE_PRODUCT_TYPE…C3.360.sve_sd…duration_s=57…
  oe=69B547BD  (expires 2026-03-14 11:34 UTC)
```

The `efg` field decodes to `xpv_progressive.VI_USECASE_PRODUCT_TYPE…360.sve_sd` — this is a
**Standard Definition (360p) progressive MP4**. The `duration_s=57` confirms a 57-second video,
matching the original findings document. The downloaded size was **1.64 MB** — much smaller than
the expected ~7 MB because the CDN served the SD (360p) stream, not the HD stream. This is the
expected behaviour when the requesting IP/User-Agent triggers the low-quality tier.

**For Claude vision analysis**: The SD stream is acceptable for frame extraction. Lower resolution
means smaller frame JPEG files (~50–100 KB vs ~200–400 KB for HD) and lower Claude vision token
cost.

### Thumbnail URL

```
https://scontent-iad3-1.xx.fbcdn.net/v/t39.35426-6/569066098_…n.jpg
  oe=69B54628  (expires 2026-03-14 11:27 UTC)
```

**Downloaded size**: 275 KB. Standard JPEG thumbnail, ~1080px wide. Suitable as a primary still
frame if FFmpeg extraction is not needed (e.g., for image ads or as a fallback).

---

## Observations vs. Plan Predictions

| Metric | Plan Prediction | Actual | Delta |
|---|---|---|---|
| networkidle time | 4–6s | 1.1s | 4× faster |
| MP4 file size | ~7 MB (HD) | 1.64 MB (SD 360p) | CDN served SD tier |
| Video duration | 57s | 57s (from efg) | Matches |
| Peak RSS | ~350 MB | ~347 MB | On target |
| Total test duration | ~18s (page work only) | ~34s (includes Chromium startup) | Startup ~20s |
| Chromium startup | Not quantified | ~20s (first launch, cold) | Warm launches will be faster |
| Bot detection | Possible CAPTCHA risk | No detection triggered | stealth=True effective |
| `playwright install-deps` | Expected to work | Failed (apt-get not found) | Pre-installed via dnf instead |

---

## Issues Found and Resolutions

### Issue 1 — Key pair `metaads-test` not in AWS

The `metaads-test` key pair existed on disk (`~/.ssh/metaads-test.pem`) but had never been
imported into the AWS account in `us-east-1`. Terraform's first `apply` failed with
`InvalidKeyPair.NotFound`.

**Resolution**: Extract the public key from the PEM and import it:
```bash
ssh-keygen -y -f ~/.ssh/metaads-test.pem | \
  aws ec2 import-key-pair --profile metads --region us-east-1 \
  --key-name metaads-test --public-key-material fileb:///dev/stdin
```

### Issue 2 — Test script not on `main` branch

The EC2 user_data clones `github_branch = "main"` from GitHub. The test script
`andromeda_single_ad_test.py` was committed only to the `ANDROMEDA` branch. The auto-run step in
user_data silently skipped the test with "script not found".

**Resolution for this run**: SCP the file directly to the running instance.

**Resolution going forward**: Change `terraform.tfvars` to `github_branch = "ANDROMEDA"` so future
test instances clone the correct branch and the script runs automatically at boot.

### Issue 3 — `playwright install-deps` uses `apt-get`

Playwright's `install-deps` command detected AL2023 as "unsupported" and attempted a Ubuntu/Debian
package install via `apt-get`, which does not exist on AL2023.

**Resolution**: Pre-install all required Chromium system libraries via `dnf` in step 2.5 of
`user_data.sh`. The browser runs correctly without `playwright install-deps` completing.

**Permanent fix**: Add `|| true` to the `playwright install-deps` call in user_data so it doesn't
log a warning that looks like a fatal error, and document that step 7.5 is now a no-op on AL2023.

---

## Risk Reassessment After Phase 1

| Risk | Pre-test Likelihood | Post-test Assessment |
|---|---|---|
| Playwright fingerprint detected | Medium | **Reduced** — stealth=True worked cleanly on first run; page loaded with full ad content |
| IP range block (AWS EC2 IPs) | Low-Medium | **Low** — EC2 `us-east-1` IP served snapshot normally; CDN latency was very low |
| `render_ad` page gated behind FB login | Low | **Confirmed Low** — page rendered without any login prompt |
| CDN URL expired before download | Low | **Confirmed Low** — URLs are valid for ~106h after snapshot load |
| `playwright install-deps` issue on AL2023 | Not anticipated | **Resolved** — pre-installing dnf libs is the correct approach |
| t3.small OOM with Chromium | Low-Medium | **Confirmed Low** — peak 347 MB / 2 GB; large headroom |
| Video quality (SD vs HD) | Not anticipated | **Low impact** — SD stream sufficient for Claude vision analysis |

---

## GO / NO-GO Decision

### For Steps 9–16 (FFmpeg + Claude API + DynamoDB)

**Decision: GO**

Phase 1 confirms the hardest unknowns:
1. Meta does not block headless Chromium from EC2 for snapshot pages (with stealth).
2. The DOM is fully rendered and asset URLs are extractable within ~2.6 seconds of page load.
3. CDN URLs are valid for ~106 hours — plenty of time for a batch process.
4. Assets download cleanly from EC2 without additional authentication.
5. Memory usage is well within t3.small capacity.

The remaining steps (FFmpeg frame extraction, Claude API scoring, DynamoDB write) are all
well-understood engineering tasks with no equivalent uncertainty. FFmpeg is a known-working
tool; Claude vision API is used elsewhere in the project; DynamoDB writes are already used by
every other Lambda in the stack.

### For Full Production Cron (50+ ads/day)

**Decision: CONDITIONAL GO — pending Phase 2 batch test**

The single-ad test does not stress-test bot detection. The key unknown is whether Meta rate-
limits or blocks after N consecutive snapshot page loads from the same IP. Phase 2 (10-ad
matrix with delays) must be run before committing to a production cron schedule.

**Recommended Phase 2 approach**:
- Run Config C (stealth=True, 5–15s random delay) against 10 real ads from the `moda` niche.
- If ≥ 8/10 succeed: proceed with daily cron at 50 ads/day.
- If < 8/10 succeed: add a residential proxy for the snapshot page requests only (keepng direct
  AWS networking for Secrets Manager / DynamoDB / Claude API calls).

---

## Next Steps

### Immediate (before committing to production)

1. **Fix `terraform.tfvars`**: Set `github_branch = "ANDROMEDA"` so the test script is
   auto-deployed on the next EC2 spin-up.

2. **Steps 9–13 implementation**: Add FFmpeg frame extraction, Claude API vision scoring, and
   DynamoDB write to `andromeda_single_ad_test.py`. Requires:
   - Add `anthropic` SDK to the Python deps in `user_data.sh`
   - Store Anthropic API key in Secrets Manager (`metaads/dev/anthropic`) and add
     `secretsmanager:GetSecretValue` on that ARN to the IAM policy
   - Add `dynamodb:PutItem` + `dynamodb:Query` + `dynamodb:GetItem` on `metaads-dev-table` to
     the IAM policy
   - Install `ffmpeg` (static binary from johnvansickle.com) in `user_data.sh`

3. **Phase 2 batch test**: Run Config C (stealth + 5–15s delays) against 10 real ads to
   validate that the pipeline survives consecutive page loads without triggering bot detection.

4. **ANDROMEDA branch cleanup**: Once Phase 2 passes, update `user_data.sh`'s
   `playwright install-deps` step to use `|| true` to silence the false error, and update the
   setup_complete.txt to reflect the correct test instructions.

### Infrastructure changes required before production

| Change | File | Status |
|---|---|---|
| `github_branch = "ANDROMEDA"` | `terraform.tfvars` | Pending |
| `anthropic` SDK in pip install | `user_data.sh` | Pending |
| `ffmpeg` static binary install | `user_data.sh` | Pending |
| `secretsmanager:GetSecretValue` on Anthropic key ARN | `main.tf` IAM policy | Pending |
| `dynamodb:PutItem / Query / GetItem` on metaads-dev-table | `main.tf` IAM policy | Pending |
| `|| true` on `playwright install-deps` line | `user_data.sh` | Pending |

---

**Document Version**: 1.0
**Date**: 2026-03-10
**Test Status**: Phase 1 complete (8/8 PASS). Phases 2–4 pending.
**Recommendation**: Proceed to Phase 2 (batch bot-detection matrix).
