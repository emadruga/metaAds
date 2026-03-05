# Procedure: Point metads.app → Cloudflare DNS → AWS CloudFront

**Domain**: `metads.app` (registered at Namecheap, currently pointing to GitHub Pages)
**Target**: CloudFront distribution `d3ba787xl1d882.cloudfront.net`
**DNS manager**: Cloudflare (free plan)

---

## Phase 1 — Move DNS to Cloudflare

**Step 1.** Sign up at [cloudflare.com](https://cloudflare.com) (free plan is enough), click **Add a Site**, enter `metads.app`.

**Step 2.** Cloudflare scans your current DNS records (it will import the GitHub Pages A/CNAME records automatically).

**Step 3.** At the end of the scan, Cloudflare gives you **two nameserver hostnames**, e.g.:
```
elaine.ns.cloudflare.com
jim.ns.cloudflare.com
```

**Step 4.** Log into **Namecheap** → Domain List → `metads.app` → **Manage** → change **Nameservers** from "Namecheap BasicDNS" to **Custom DNS**, paste the two Cloudflare nameservers, save.

**Step 5.** Wait for propagation (usually 5–30 min, max 48h). Cloudflare will email you when it's active.

---

## Phase 2 — Issue an ACM Certificate (MUST be in `us-east-1`)

CloudFront only accepts ACM certs from `us-east-1`, which is already the project region.

**Step 6.** In the AWS Console → **Certificate Manager** → region `us-east-1` → **Request certificate** → **Public certificate**.

**Step 7.** Add these two domain names:
```
metads.app
www.metads.app
```
(You can also use `*.metads.app` instead of `www.metads.app` to cover all subdomains.)

**Step 8.** Validation method: **DNS validation** → Request.

**Step 9.** ACM shows you one or two CNAME records to prove domain ownership, like:
```
_abc123.metads.app  CNAME  _xyz456.acm-validations.aws.
```

**Step 10.** In Cloudflare DNS, add those CNAME records (keep **proxy OFF** — gray cloud). ACM validates within 5–30 minutes after DNS propagates. Certificate status becomes **Issued**.

> Copy the **Certificate ARN** — you'll need it in the next phase.

---

## Phase 3 — Update Terraform

The `cloudfront.tf` already has the `var.custom_domain` hook but is missing `aliases` and the real cert config.

### `infra/cloudfront.tf`

Add `aliases` to the distribution and fix `viewer_certificate`:

```hcl
resource "aws_cloudfront_distribution" "frontend" {
  # ... existing config ...

  # ADD THIS BLOCK:
  aliases = var.custom_domain != "" ? [var.custom_domain, "www.${var.custom_domain}"] : []

  viewer_certificate {
    cloudfront_default_certificate = var.custom_domain == "" ? true : false
    acm_certificate_arn            = var.custom_domain != "" ? var.acm_certificate_arn : null
    ssl_support_method             = var.custom_domain != "" ? "sni-only" : null
    minimum_protocol_version       = "TLSv1.2_2021"
  }
```

### `infra/variables.tf`

Add the new variable:

```hcl
variable "acm_certificate_arn" {
  description = "ACM certificate ARN for custom domain (us-east-1)"
  type        = string
  default     = ""
}
```

### `infra/dev.tfvars`

```hcl
custom_domain       = "metads.app"
acm_certificate_arn = "arn:aws:acm:us-east-1:645069181643:certificate/PASTE-YOUR-CERT-ID-HERE"
cors_allow_origins  = [
  "https://d3ba787xl1d882.cloudfront.net",
  "https://metads.app",
  "https://www.metads.app"
]
```

### Deploy

```bash
cd /Users/emadruga/proj/metaAds/aws_lambda_deploy/infra
terraform apply -var-file=dev.tfvars -auto-approve
```

> CloudFront will reject the apply if the cert is not yet **Issued**, so complete Phase 2 first.

---

## Phase 4 — Point Cloudflare DNS to CloudFront

After `terraform apply` succeeds, go to Cloudflare DNS and:

**Step 11.** **Delete** the old GitHub Pages A records (they will be `185.199.108.153`, etc.).

**Step 12.** Add these records — **proxy must be OFF (gray cloud)**:

| Type | Name | Content | Proxy |
|------|------|---------|-------|
| CNAME | `metads.app` (apex) | `d3ba787xl1d882.cloudfront.net` | DNS only |
| CNAME | `www` | `d3ba787xl1d882.cloudfront.net` | DNS only |

> Cloudflare automatically **flattens** the apex CNAME (RFC violation workaround) — this is one key reason to use Cloudflare.

> Keep proxy **OFF** because CloudFront already handles CDN + TLS. Proxying through Cloudflare on top adds latency and complicates SSL.

---

## Phase 5 — Verify

```bash
# Check DNS propagated
dig metads.app CNAME +short
# Should resolve to d3ba787xl1d882.cloudfront.net or an IP

# Test HTTPS
curl -I https://metads.app
# Should return HTTP/2 200 with your CloudFront security headers
```

The site at `https://metads.app` and `https://www.metads.app` will serve the Vue SPA from CloudFront.

---

## Summary of files to edit in the repo

| File | Change |
|------|--------|
| `infra/cloudfront.tf` | Add `aliases` block + fix `viewer_certificate` |
| `infra/variables.tf` | Add `acm_certificate_arn` variable |
| `infra/dev.tfvars` | Set `custom_domain`, `acm_certificate_arn`, update `cors_allow_origins` |

---

## Wrap-up — Completion Verification (2026-03-04)

### Final state confirmed

Everything was already live and correct when verified. No Terraform changes were needed because the CloudFront distribution had already been updated prior to this session. The ACM certificate was issued and attached.

**CloudFront distribution `E9Q8645UTHPJD` — confirmed configuration:**

```json
{
  "Aliases": {
    "Quantity": 2,
    "Items": ["www.metads.app", "metads.app"]
  },
  "ViewerCert": {
    "CloudFrontDefaultCertificate": false,
    "ACMCertificateArn": "arn:aws:acm:us-east-1:645069181643:certificate/d89a893a-5230-433f-bbc8-f028c64dbe63",
    "SSLSupportMethod": "sni-only",
    "MinimumProtocolVersion": "TLSv1.2_2021"
  }
}
```

**DNS confirmed (via `dig`):**

```
$ dig metads.app NS +short
heather.ns.cloudflare.com.
nero.ns.cloudflare.com.

$ dig metads.app A +short
99.86.132.184   # CloudFront edge IPs (Cloudflare CNAME-flattened)
99.86.132.24
99.86.132.215
99.86.132.100
```

**End-to-end HTTPS test:**

```
$ curl -sI https://metads.app
HTTP/2 200
content-type: text/html
server: AmazonS3
via: 1.1 422308fde3db0e3a0f60208e4153c7f6.cloudfront.net (CloudFront)
strict-transport-security: max-age=31536000; includeSubDomains; preload
x-frame-options: DENY
x-content-type-options: nosniff
x-xss-protection: 1; mode=block
referrer-policy: strict-origin-when-cross-origin

$ curl -sI https://www.metads.app
HTTP/2 200
content-type: text/html
```

### Status summary

| Check | Result |
|---|---|
| `https://metads.app` | ✅ HTTP/2 200 |
| `https://www.metads.app` | ✅ HTTP/2 200 |
| ACM certificate | ✅ Issued — covers `metads.app` + `*.metads.app` |
| CloudFront aliases | ✅ `metads.app` + `www.metads.app` |
| DNS manager | ✅ Cloudflare (`heather` / `nero` nameservers) |
| Cloudflare proxy | ✅ OFF (gray cloud) — CloudFront handles CDN + TLS |
| Security headers | ✅ HSTS, X-Frame-Options, XSS-Protection, nosniff |

---

## E-mail Service Options

Since `metads.app` DNS is managed by Cloudflare, the existing MX records (previously pointing to Namecheap's `eforward5.registrar-servers.com` forwarders) can be replaced or supplemented with a proper email solution. Below is a full breakdown of the best options.

---

### Option 1 — Cloudflare Email Routing (Recommended for simplicity)

**Free, zero config, built right into the Cloudflare dashboard.**

- Go to **Cloudflare → metads.app → Email → Email Routing**
- Enable it → Cloudflare replaces the Namecheap MX records automatically
- Create rules like `hello@metads.app → yourpersonalemail@gmail.com`
- Supports catch-all (`*@metads.app → you`)

**Limitation**: receive-only forwarding. Cannot *send* from `hello@metads.app` natively.
**Workaround**: configure **Gmail "Send mail as"** (Settings → Accounts → Add another email address) using Gmail's SMTP relay — then you can reply from `hello@metads.app` inside Gmail at no extra cost.

---

### Option 2 — Zoho Mail (Free actual mailbox)

**Free tier: up to 5 users, 5 GB/mailbox — real inbox, no forwarding tricks.**

- Add MX records pointing to Zoho in Cloudflare
- Full webmail + mobile app at `mail.zoho.com`
- Send *and* receive from `you@metads.app` natively
- No ads; IMAP/POP3 available on the free tier

Best choice if a proper mailbox is needed without paying.

---

### Option 3 — ImprovMX / ForwardEmail.net

Pure forwarding services, similar to Cloudflare Email Routing but as standalone products. Less compelling since Cloudflare already provides the same capability built-in.

---

### Option 4 — Google Workspace

~$7/user/month. Full Gmail UX with `@metads.app`. Worth it only if Google Drive, Meet, etc. are needed as a bundle.

---

### AWS Email Services

AWS offers two distinct email services that serve very different purposes:

#### Amazon SES (Simple Email Service)

A developer-focused email *sending* platform — **not a mailbox**.

- Send transactional emails from the app (alerts, reports, password resets, job completion notifications, etc.)
- Receive emails → trigger a Lambda, store in S3, or forward
- Full DKIM / SPF / DMARC support on the custom domain
- Cost: **$0.10 per 1,000 emails sent**; receiving is free
- No webmail UI, no inbox — purely API / SMTP

**Relevant to this project**: since Lambdas are already running, SES is a natural fit for any app-level outbound email (e.g. collection job alerts, user signup confirmations). Can be added to the stack via Terraform.

**Catch**: new accounts start in **sandbox mode** (can only send to verified addresses). Production access must be requested via AWS Support — typically approved within 24 h.

#### Amazon WorkMail

A full mailbox service — AWS's answer to Google Workspace / Zoho.

- Webmail UI, calendar, contacts
- IMAP / SMTP (compatible with Outlook, Apple Mail, Thunderbird)
- Custom domain support (`you@metads.app`)
- **$4/user/month**

Honest assessment: functional but dated UI. At $4/month, Zoho Mail's free tier is more compelling for a solo project.

---

### Recommendation for metads.app

| Goal | Best pick |
|---|---|
| Just receive emails, already use Gmail | **Cloudflare Email Routing** + Gmail "Send mail as" |
| Real inbox, send & receive, free | **Zoho Mail** |
| App sends notification/transactional emails | **Amazon SES** |
| Full AWS-native mailbox | **Amazon WorkMail** ($4/mo) |
| Google ecosystem, don't mind paying | **Google Workspace** (~$7/mo) |

**Optimal setup for this stack**: add **Amazon SES for outbound app emails** (likely needed as the app grows), and use **Cloudflare Email Routing** for personal `@metads.app` forwarding — total cost near zero.
