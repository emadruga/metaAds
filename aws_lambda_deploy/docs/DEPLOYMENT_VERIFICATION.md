# Lambda Deployment Verification Guide

## Quick Check: Is My Code Deployed?

**TL;DR:** Run this from the project root:
```bash
./aws_lambda_deploy/scripts/verify-lambda-deployment.sh
```

Or from the aws_lambda_deploy directory:
```bash
cd aws_lambda_deploy
./scripts/verify-lambda-deployment.sh
```

This compares your local Lambda ZIP files with what's deployed on AWS.

---

## Methods to Verify Deployment

### Method 1: Automated Script (Recommended) ⭐

Use the verification script that compares code hashes:

```bash
# From project root
./aws_lambda_deploy/scripts/verify-lambda-deployment.sh

# Or from aws_lambda_deploy directory
cd aws_lambda_deploy
./scripts/verify-lambda-deployment.sh

# Custom function/layer names
./scripts/verify-lambda-deployment.sh metaads-dev-niches metaads-dev-shared-layer
```

**What it checks:**
1. ✅ Lambda function code hash matches local ZIP
2. ✅ Lambda layer code hash matches local ZIP
3. ✅ Function is using the latest layer version

**Output example:**
```
🔍 Checking Lambda deployment status...
   Using AWS profile: metads

1️⃣  Lambda Function: metaads-dev-ads
   Local hash:  /WL5baVM6JustZmxR5SfA6vIenCqCxnGTgZwP3wx1bw=
   AWS hash:    /WL5baVM6JustZmxR5SfA6vIenCqCxnGTgZwP3wx1bw=
   ✅ Function code matches!

2️⃣  Lambda Layer: metaads-dev-shared-layer
   Layer version: 13
   Local hash:  f+8+MgJDAFtLeoxg7ec+riQ/s3kHGT9Sl4ZNpH4/Wbw=
   AWS hash:    f+8+MgJDAFtLeoxg7ec+riQ/s3kHGT9Sl4ZNpH4/Wbw=
   ✅ Layer code matches!

3️⃣  Layer attachment:
   Function using layer version: 13
   Latest layer version:         13
   ✅ Function using latest layer!

═══════════════════════════════════════════════════
✅ ALL CHECKS PASSED - Deployment is up to date!
═══════════════════════════════════════════════════
```

---

### Method 2: Manual AWS Console Check

1. **Go to AWS Lambda Console**: https://console.aws.amazon.com/lambda
2. **Select your function** (e.g., `metaads-dev-ads`)
3. **Check "Last modified"** timestamp - should match your recent deployment
4. **Check "Layers"** section - verify layer version number

**Pros:** Visual, no CLI needed
**Cons:** Doesn't show code hash, manual comparison

---

### Method 3: Terraform State Check

Check what Terraform thinks is deployed:

```bash
cd aws_lambda_deploy/infra
terraform show | grep -A 10 "aws_lambda_function.ads"
```

Look for:
- `source_code_hash` - should match your local ZIP hash
- `last_modified` - recent timestamp

**Calculate local hash:**
```bash
openssl dgst -sha256 -binary aws_lambda_deploy/lambda_stubs/ads.zip | openssl enc -base64
```

---

### Method 4: Git Commit + Deployment Log

Track deployments by creating git tags or commit messages:

```bash
# After successful deployment
git tag -a deploy-$(date +%Y%m%d-%H%M) -m "Deployed: $(terraform output -json | jq -r '.api_gateway_url.value')"
git push --tags
```

Then check:
```bash
git tag -l 'deploy-*' | tail -1
```

---

### Method 5: CloudWatch Logs (Runtime Verification)

Verify the deployed code is actually running:

**Add version info to your Lambda handler:**
```python
# In lambda_src/ads/handler.py
import os

VERSION = os.getenv('GIT_COMMIT', 'unknown')

def handler(event, context):
    logger.info(f"Handler version: {VERSION}")
    # ... rest of handler
```

**Set in Terraform:**
```hcl
# In infra/lambda.tf
resource "aws_lambda_function" "ads" {
  environment {
    variables = {
      GIT_COMMIT = var.git_commit  # Pass via: terraform apply -var="git_commit=$(git rev-parse --short HEAD)"
    }
  }
}
```

**Check logs:**
```bash
aws logs tail /aws/lambda/metaads-dev-ads --profile metads --follow
```

---

## Understanding Code Hashes

### What is CodeSha256?

AWS Lambda computes a SHA256 hash of your deployment package (ZIP file) and stores it. This hash changes **only when the code changes**, not when you redeploy the same code.

### Why Hashes Differ Even if Code is "Same"

**ZIP file metadata** affects the hash:
- Timestamps of files in the ZIP
- Compression level
- File ordering

**Solution:** Always rebuild ZIPs from source before comparing:
```bash
# Rebuild Lambda ZIPs
cd aws_lambda_deploy/lambda_stubs
rm -f shared_layer.zip ads.zip

cd ../lambda_layers/shared
zip -r ../../lambda_stubs/shared_layer.zip python/ -x "*.pyc" -x "*__pycache__*"

cd ../../lambda_src/ads
zip ../../lambda_stubs/ads.zip handler.py

# Now verify
cd ../../../
./scripts/verify-lambda-deployment.sh
```

---

## Deployment Workflow Best Practices

### 1. Before Making Changes
```bash
# Verify current deployment is clean
./aws_lambda_deploy/scripts/verify-lambda-deployment.sh
```

### 2. After Code Changes
```bash
# Check what changed
git diff aws_lambda_deploy/lambda_src/
git diff aws_lambda_deploy/lambda_layers/

# Commit changes
git add .
git commit -m "fix: your change description"
```

### 3. Build & Deploy
```bash
# Rebuild ZIPs
cd aws_lambda_deploy/lambda_stubs
rm -f shared_layer.zip ads.zip

cd ../lambda_layers/shared
zip -r ../../lambda_stubs/shared_layer.zip python/ -x "*.pyc" -x "*__pycache__*"

cd ../../lambda_src/ads
zip ../../lambda_stubs/ads.zip handler.py

# Deploy with Terraform
cd ../../infra
terraform apply -target=aws_lambda_layer_version.shared -target=aws_lambda_function.ads
```

### 4. Verify Deployment
```bash
cd ../../../  # Back to project root
./aws_lambda_deploy/scripts/verify-lambda-deployment.sh
```

### 5. Test in Browser
- Hard refresh (Cmd+Shift+R / Ctrl+Shift+R)
- Test the feature
- Check browser network tab for API responses

---

## Troubleshooting

### "Function code DIFFERS" but I just deployed

**Likely cause:** You modified source files after building the ZIP.

**Solution:**
```bash
# Rebuild ZIPs from current source
cd aws_lambda_deploy/lambda_layers/shared
zip -r ../../lambda_stubs/shared_layer.zip python/ -x "*.pyc" -x "*__pycache__*"

cd ../../lambda_src/ads
zip ../../lambda_stubs/ads.zip handler.py

# Verify again
cd ../../../
./aws_lambda_deploy/scripts/verify-lambda-deployment.sh
```

### "Layer code DIFFERS" but function code matches

**Likely cause:** You updated the layer source but didn't redeploy.

**Solution:**
```bash
cd aws_lambda_deploy/infra
terraform apply -target=aws_lambda_layer_version.shared
```

### "Function using OLD layer"

**Likely cause:** New layer version exists but function wasn't updated.

**Solution:**
```bash
cd aws_lambda_deploy/infra
terraform apply -target=aws_lambda_function.ads
```

### Browser still shows old behavior after deployment

**Solutions:**
1. Hard refresh: Cmd+Shift+R (Mac) / Ctrl+Shift+R (Windows/Linux)
2. Clear browser cache
3. Open in incognito/private window
4. Check browser console for API errors
5. Check Network tab - verify API calls are going to correct endpoint

---

## Quick Reference: AWS CLI Commands

```bash
# Get function info
aws lambda get-function --profile metads --function-name metaads-dev-ads

# Get function code hash
aws lambda get-function --profile metads --function-name metaads-dev-ads \
  --query 'Configuration.CodeSha256' --output text

# List layer versions
aws lambda list-layer-versions --profile metads --layer-name metaads-dev-shared-layer

# Get layer code hash
aws lambda get-layer-version --profile metads \
  --layer-name metaads-dev-shared-layer --version-number 13 \
  --query 'Content.CodeSha256' --output text

# Get function's layer version
aws lambda get-function --profile metads --function-name metaads-dev-ads \
  --query 'Configuration.Layers[0].Arn' --output text

# Check when function was last modified
aws lambda get-function --profile metads --function-name metaads-dev-ads \
  --query 'Configuration.LastModified' --output text
```

---

## Automated Deployment Verification in CI/CD

Add to your CI/CD pipeline:

```yaml
# .github/workflows/deploy.yml
- name: Verify deployment
  run: |
    ./aws_lambda_deploy/scripts/verify-lambda-deployment.sh
    if [ $? -ne 0 ]; then
      echo "❌ Deployment verification failed!"
      exit 1
    fi
```

---

## FAQ

**Q: Why do I need to rebuild ZIPs manually?**
A: Terraform doesn't automatically rebuild ZIPs from source. You need to explicitly rebuild them when source code changes.

**Q: Can I automate the ZIP building?**
A: Yes! Use a Makefile or shell script. Example:
```bash
# aws_lambda_deploy/scripts/build-lambdas.sh
#!/bin/bash
cd "$(dirname "$0")/.."
cd lambda_layers/shared
zip -r ../../lambda_stubs/shared_layer.zip python/ -x "*.pyc" -x "*__pycache__*"

cd ../../lambda_src/ads
zip ../../lambda_stubs/ads.zip handler.py

echo "✅ Lambda ZIPs rebuilt"
```

**Q: What if hashes match but code still seems old?**
A: Check CloudWatch Logs to see what version is actually running. You may have multiple Lambda instances with stale code cached.

**Q: How long does it take for new code to be active?**
A: Usually immediate. But if you have warm Lambda instances, they may continue running old code until they expire (~15 minutes of inactivity).

**Q: Can I force Lambda to use new code immediately?**
A: Update an environment variable (even a dummy one) to force all instances to restart:
```bash
aws lambda update-function-configuration --profile metads \
  --function-name metaads-dev-ads \
  --environment "Variables={FORCE_REDEPLOY=$(date +%s)}"
```

---

## Related Documentation

- [Terraform Lambda Configuration](../infra/lambda.tf)
- [Lambda Source Code](../lambda_src/)
- [Lambda Layers](../lambda_layers/)
- [Deployment Session Log](20260224_Errors_Fixed_and_TODO.md)
