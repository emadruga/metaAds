# MetaAds AWS Feasibility Test - Quick Start Guide

## 🎯 Overview

This guide provides step-by-step instructions to deploy and test the MetaAds data collection system on AWS using Terraform. The entire process takes approximately **60-90 minutes** and costs **less than $1** (or FREE with AWS Free Tier).

### 🚀 Quick Test Script

Once deployed, use the **comprehensive feasibility test script** to validate all components:

```bash
# After SSH into your EC2 instance
cd ~/metaAds
source venv/bin/activate
python final_feasibility.py
```

This automated script tests:
- ✅ API connectivity
- ✅ Data collection (50 ads)
- ✅ Data processing & analysis
- ✅ Database storage
- ✅ Performance metrics

See [Testing & Validation](#testing--validation) section for details.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [AWS Account Setup](#aws-account-setup)
3. [SSH Key Pair Creation](#ssh-key-pair-creation)
4. [Terraform Configuration](#terraform-configuration)
5. [Infrastructure Deployment](#infrastructure-deployment)
6. [Application Configuration](#application-configuration)
7. [Testing & Validation](#testing--validation)
8. [Monitoring & Troubleshooting](#monitoring--troubleshooting)
9. [Results Documentation](#results-documentation)
10. [Cleanup](#cleanup)

---

## Prerequisites

### Required Tools

Before starting, ensure you have the following installed:

#### 1. AWS CLI

**Check if installed:**
```bash
aws --version
```

**Install if needed:**
```bash
# macOS (Homebrew)
brew install awscli

# Linux
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Windows
# Download from: https://aws.amazon.com/cli/
```

#### 2. Terraform

**Check if installed:**
```bash
terraform version
```

**Install if needed:**
```bash
# macOS (Homebrew)
brew install terraform

# Linux
wget https://releases.hashicorp.com/terraform/1.7.0/terraform_1.7.0_linux_amd64.zip
unzip terraform_1.7.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/

# Windows (Chocolatey)
choco install terraform

# Or download from: https://www.terraform.io/downloads
```

#### 3. Git

**Check if installed:**
```bash
git --version
```

**Install if needed:**
```bash
# macOS
brew install git

# Linux
sudo yum install git  # Amazon Linux/RedHat
sudo apt install git  # Ubuntu/Debian

# Windows
# Download from: https://git-scm.com/download/win
```

### Required Accounts

- **AWS Account** (Free Tier eligible recommended)
- **GitHub Account** (if using private repository)
- **Meta Developer Account** (for API access token)

### System Requirements

- **OS**: macOS, Linux, or Windows 10+
- **RAM**: 4 GB minimum
- **Disk Space**: 500 MB free
- **Internet**: Stable connection required

---

## AWS Account Setup

### Step 1: Configure AWS Credentials

#### Option A: Using AWS Configure (Recommended)

```bash
aws configure
```

You'll be prompted for:
- **AWS Access Key ID**: Your IAM access key
- **AWS Secret Access Key**: Your IAM secret key
- **Default region**: `us-east-1` (recommended)
- **Default output format**: `json`

#### Option B: Manual Configuration

Create/edit `~/.aws/credentials`:
```ini
[default]
aws_access_key_id = YOUR_ACCESS_KEY_HERE
aws_secret_access_key = YOUR_SECRET_KEY_HERE
```

Create/edit `~/.aws/config`:
```ini
[default]
region = us-east-1
output = json
```

### Step 2: Verify AWS Access

```bash
# Test AWS CLI connectivity
aws sts get-caller-identity

# Expected output:
{
    "UserId": "AIDAXXXXXXXXXXXXXXXXX",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/your-username"
}
```

### Step 3: Check AWS Free Tier Eligibility

```bash
# Check if Free Tier eligible (account < 12 months old)
aws ce get-cost-and-usage \
  --time-period Start=2026-02-01,End=2026-02-21 \
  --granularity MONTHLY \
  --metrics "UsageQuantity" \
  --filter file://<(echo '{"Dimensions":{"Key":"SERVICE","Values":["Amazon Elastic Compute Cloud - Compute"]}}')
```

---

## SSH Key Pair Creation

### Step 1: Create Key Pair in AWS

#### Option A: AWS Console

1. Go to [EC2 Console](https://console.aws.amazon.com/ec2/)
2. Navigate to **Network & Security** → **Key Pairs**
3. Click **Create key pair**
4. Settings:
   - **Name**: `metaads-test`
   - **Key pair type**: RSA
   - **File format**: `.pem` (for macOS/Linux) or `.ppk` (for Windows)
5. Click **Create key pair**
6. Save the downloaded `.pem` file

#### Option B: AWS CLI (Recommended)

```bash
# Create key pair and save to file
aws ec2 create-key-pair \
  --key-name metaads-test \
  --query 'KeyMaterial' \
  --output text > ~/.ssh/metaads-test.pem

# Set correct permissions (critical!)
chmod 400 ~/.ssh/metaads-test.pem

# Verify key was created
aws ec2 describe-key-pairs --key-names metaads-test
```

### Step 2: Verify Key Pair

```bash
# List your key pairs
aws ec2 describe-key-pairs --query 'KeyPairs[*].[KeyName,KeyFingerprint]' --output table

# Expected output:
----------------------------------------
|          DescribeKeyPairs            |
+---------------+----------------------+
|  metaads-test |  aa:bb:cc:dd:ee:ff  |
+---------------+----------------------+
```

---

## Terraform Configuration

### Step 1: Navigate to Terraform Directory

```bash
cd /Users/emadruga/proj/metaAds/aws_feasibility/terraform
```

### Step 2: Create Configuration File

```bash
# Copy example file
cp terraform.tfvars.example terraform.tfvars

# Edit with your values
vim terraform.tfvars  # or nano, code, etc.
```

### Step 3: Configure Required Variables

Edit `terraform.tfvars` with your values:

```hcl
# ============================================================================
# REQUIRED: You MUST change these values
# ============================================================================

# SSH key pair name (created in previous step)
key_name = "metaads-test"

# Your GitHub repository URL
github_repo_url = "https://github.com/YOUR-USERNAME/metaAds.git"

# ============================================================================
# RECOMMENDED: Secure your instance
# ============================================================================

# Restrict SSH access to your IP only (more secure)
# Find your IP: curl ifconfig.me
allowed_ssh_cidr = ["YOUR.IP.ADDRESS.HERE/32"]

# ============================================================================
# OPTIONAL: Adjust if needed
# ============================================================================

aws_region       = "us-east-1"
instance_type    = "t3.micro"       # Free Tier eligible
root_volume_size = 20               # GB
use_elastic_ip   = false
github_branch    = "main"
```

### Step 4: Validate Configuration

```bash
# Check Terraform version
terraform version

# Validate syntax
terraform fmt
terraform validate
```

---

## Infrastructure Deployment

### Step 1: Initialize Terraform

```bash
terraform init
```

**Expected output:**
```
Initializing the backend...
Initializing provider plugins...
- Finding hashicorp/aws versions matching "~> 5.0"...
- Installing hashicorp/aws v5.x.x...
Terraform has been successfully initialized!
```

### Step 2: Review Planned Changes

```bash
terraform plan
```

**Review the output carefully:**
- Resources to be created: ~10-12 resources
- Instance type: t3.micro
- Region: us-east-1
- Security groups, IAM roles, etc.

**Example output:**
```
Plan: 10 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + instance_public_ip = (known after apply)
  + ssh_connection_command = (known after apply)
```

### Step 3: Deploy Infrastructure

```bash
terraform apply
```

**When prompted:**
```
Do you want to perform these actions?
  Terraform will perform the actions described above.
  Only 'yes' will be accepted to approve.

  Enter a value: yes
```

**Deployment timeline:**
```
[00:00] Creating security group...
[00:05] Creating IAM role and policies...
[00:10] Creating CloudWatch log group...
[00:15] Launching EC2 instance...
[00:45] Running user data script (automated setup)...
[05:00] Instance ready!
```

**Expected output:**
```
Apply complete! Resources: 10 added, 0 changed, 0 destroyed.

Outputs:

instance_id = "i-0123456789abcdef0"
instance_public_ip = "54.123.45.67"
ssh_connection_command = "ssh -i ~/.ssh/metaads-test.pem ec2-user@54.123.45.67"
```

### Step 4: Save Connection Information

```bash
# Save outputs to file for reference
terraform output > outputs.txt

# Get quick start commands
terraform output -raw quick_start_commands
```

### Step 5: Wait for User Data Completion

The instance runs an automated setup script that takes 5-10 minutes. Monitor progress:

```bash
# Get instance IP
INSTANCE_IP=$(terraform output -raw instance_public_ip)

# Wait 2-3 minutes, then check setup status
ssh -i ~/.ssh/metaads-test.pem ec2-user@$INSTANCE_IP "tail -f /var/log/user-data.log"

# Or check if setup is complete
ssh -i ~/.ssh/metaads-test.pem ec2-user@$INSTANCE_IP "cat ~/setup_complete.txt"
```

**Expected completion message:**
```
╔══════════════════════════════════════════════════════════════════════╗
║           MetaAds Feasibility Test - Setup Complete                  ║
╚══════════════════════════════════════════════════════════════════════╝

✅ Setup completed successfully at: [timestamp]
```

---

## Application Configuration

### Step 1: Prepare .env File Locally

Ensure your `.env` file exists and has the correct format:

```bash
# Navigate to project root
cd /Users/emadruga/proj/metaAds

# Verify .env file exists
ls -la .env

# Check contents (don't commit this!)
cat .env
```

**Expected `.env` format:**
```bash
FB_ACCESS_TOKEN=your_meta_access_token_here
FB_API_VERSION=v18.0
DB_PATH=data/ads_intelligence.db
```

### Step 2: Copy .env to EC2 Instance

```bash
# Get instance IP
INSTANCE_IP=$(terraform output -raw instance_public_ip)

# Copy .env file
scp -i ~/.ssh/metaads-test.pem .env ec2-user@$INSTANCE_IP:~/metaAds/

# Verify file was copied
ssh -i ~/.ssh/metaads-test.pem ec2-user@$INSTANCE_IP "ls -la ~/metaAds/.env"
```

**Expected output:**
```
-rw------- 1 ec2-user ec2-user 123 Feb 21 10:00 /home/ec2-user/metaAds/.env
```

### Step 3: SSH into Instance

```bash
# Connect via SSH
ssh -i ~/.ssh/metaads-test.pem ec2-user@$INSTANCE_IP
```

### Step 4: Verify Installation

Once connected to the instance:

```bash
# Check setup completion
cat ~/setup_complete.txt

# Navigate to application directory
cd ~/metaAds

# Verify directory structure
ls -la

# Expected output:
# drwxr-xr-x  src/
# drwxr-xr-x  data/
# drwxr-xr-x  logs/
# drwxr-xr-x  reports/
# drwxr-xr-x  venv/
# -rw-------  .env
# -rw-r--r--  requirements.txt
# -rw-r--r--  test_api.py
# -rwxr-xr-x  final_feasibility.py    # Comprehensive feasibility test
# -rw-r--r--  example_usage.py

# Activate virtual environment
source venv/bin/activate

# Verify Python version
python --version  # Should be Python 3.12.x

# Check installed packages
pip list | grep -E "(requests|pandas|sqlalchemy)"
```

---

## Testing & Validation

### Phase 1: API Connectivity Test

```bash
# Ensure you're in the MetaAds directory with venv activated
cd ~/metaAds
source venv/bin/activate

# Test 1: Basic API connectivity
python test_api.py
```

**Expected output:**
```
╔══════════════════════════════════════════════════════════════════════╗
║           Meta Ad Library API - Connection Test                      ║
╚══════════════════════════════════════════════════════════════════════╝

✅ SUCCESS: Meta Ad Library API is accessible!

Test Results:
├─ API Endpoint: Working
├─ Access Token: Valid
├─ Sample Query: Success
└─ Ads Retrieved: 5 ads

Sample Ad:
├─ Page: Example Company
├─ Headline: Try our product today!
└─ Active: True

╚══════════════════════════════════════════════════════════════════════╝
```

**If test fails**, troubleshooting:
```bash
# Check .env file
cat .env

# Verify token is set
echo $FB_ACCESS_TOKEN

# Test network connectivity
curl https://graph.facebook.com/v18.0/
```

### Phase 2: Data Collection Test

```bash
# Test 2: Collect sample dataset (50 ads)
python -c "
from src.collectors.meta_api_collector import MetaAdLibraryAPI

api = MetaAdLibraryAPI()
ads = api.search_ads('video editing ai', limit=50)
print(f'✅ Successfully collected {len(ads)} ads')

# Print sample ad details
if ads:
    ad = ads[0]
    print(f'Sample Ad:')
    print(f'  Page: {ad.get(\"page_name\")}')
    print(f'  Headline: {ad.get(\"ad_creative_link_titles\", [\"N/A\"])[0]}')
"
```

**Expected output:**
```
✅ Successfully collected 50 ads
Sample Ad:
  Page: OpusClip
  Headline: Turn long videos into viral clips with AI
```

### Phase 3: Comprehensive Feasibility Test

**RECOMMENDED: Use the comprehensive feasibility test script**

```bash
# Test 3: Run comprehensive feasibility test
python final_feasibility.py
```

This script performs a complete validation of all components:
- ✅ API connectivity test
- ✅ Data collection test (50 ads)
- ✅ Data processing test
- ✅ Analysis engine test
- ✅ Database storage test
- ✅ Performance monitoring

**Expected output:**
```
================================================================================
  MetaAds AWS Feasibility Test - Comprehensive Validation
  Started at: 2024-02-21 15:30:00
================================================================================

================================================================================
  Test 1: API Connectivity
================================================================================

  Initialized Meta Ad Library API client
✓ API connectivity working! Retrieved 5 ads in 0.85s
  Average response time: 0.170s per ad

================================================================================
  Test 2: Data Collection
================================================================================

  Collecting ads for keyword: 'video editing ai'
✓ Collected 25 ads in 4.25s (0.170s per ad)
  Collecting ads for keyword: 'content creation'
✓ Collected 25 ads in 4.18s (0.167s per ad)
✓ Successfully collected 50 ads total

================================================================================
  Test 3: Data Processing
================================================================================

  Initialized Ad Parser
✓ Processed 50 ads in 0.15s
  Average text length: 1180 characters
  Emoji usage: 76.0%
  Hashtag usage: 4.0%

================================================================================
  Test 4: Analysis Engine
================================================================================

  Initialized Ad Analyzer
✓ Most common words (Top 10):
  - content: 154 occurrences
  - videos: 113 occurrences
  - create: 89 occurrences
  ...

✓ CTA distribution:
  - learn more: 18 ads
  - sign up: 12 ads
  ...

✓ Top 5 advertisers:
  - OpusClip: 14 ads
  - Descript: 8 ads
  ...

================================================================================
  Test 5: Database Storage
================================================================================

  Initialized database connection
✓ Saved 50 ads to database
  Database stats: 50 total ads, 45 active

================================================================================
  Test 6: Performance Monitoring
================================================================================

✓ CPU usage: 35.2%
✓ Memory usage: 42.5% (0.42GB / 0.98GB)
✓ Disk usage: 15.3% (2.45GB / 16.00GB)
✓ Memory usage within t3.micro limits (< 900MB)

================================================================================
  Feasibility Test Summary
================================================================================

Total Tests: 6
Passed: 6 ✓
Failed: 0 ✗
Success Rate: 100.0%

Detailed Results:
  API Connectivity: ✓ PASSED
  Data Collection: ✓ PASSED
  Data Processing: ✓ PASSED
  Analysis Engine: ✓ PASSED
  Database Storage: ✓ PASSED
  Performance Monitoring: ✓ PASSED

================================================================================
  ✅ FEASIBILITY TEST PASSED
================================================================================

Recommendation: MetaAds application is ready for AWS deployment!

All critical components are working:
  ✓ Meta API connectivity from AWS infrastructure
  ✓ Data collection and processing
  ✓ Analysis engine producing insights

Next Steps:
  1. Fix database NaN handling for production use
  2. Copy .env file with production credentials
  3. Set up automated scheduling (cron/systemd)
  4. Configure monitoring and alerting
  5. Test full pipeline end-to-end

================================================================================
  Feasibility test completed at: 2024-02-21 15:32:15
================================================================================
```

### Phase 3 (Alternative): Example Usage Test

If you prefer to test with the simpler example script:

```bash
# Alternative: Run example usage script
python example_usage.py
```

**Expected output:**
```
Starting MetaAds example usage...

[Collector] Searching for ads: 'video editing ai'
[Collector] Found 50 ads

[Parser] Processing 50 ads...
[Parser] Extracted CTAs: {'learn more': 15, 'sign up': 20, 'get started': 10}

[Storage] Saving to database: data/ads_intelligence.db
[Storage] ✓ Saved 50 ads (3 duplicates skipped)

[Analyzer] Analyzing patterns...
[Analyzer] Top performing ads (30+ days active): 5 found

✅ Example complete! Check data/ads_intelligence.db
```

### Phase 4: Performance Monitoring

While tests are running, open a second SSH session to monitor resources:

```bash
# Second terminal window
ssh -i ~/.ssh/metaads-test.pem ec2-user@$INSTANCE_IP

# Monitor CPU and memory
top

# Or use htop (if available)
htop

# Check disk usage
df -h

# Monitor specific Python process
ps aux | grep python
```

**Record these metrics:**
- CPU usage: Should be < 50% during collection
- Memory usage: Should be < 500 MB
- Disk I/O: Check with `iostat -x 1`
- Network: Check with `ifstat` or `nload`

### Phase 5: Database Validation

```bash
# Check database was created
ls -lh data/ads_intelligence.db

# Query database using Python
python -c "
from src.storage.database import AdDatabase

db = AdDatabase()
stats = db.get_stats()

print('Database Statistics:')
print(f'  Total ads: {stats[\"total_ads\"]}')
print(f'  Active ads: {stats[\"active_ads\"]}')
print(f'  Unique pages: {stats[\"unique_pages\"]}')
"
```

### Phase 6: Advanced Testing (Optional)

```bash
# Test scheduler (dry run)
python -c "
from src.scheduler import setup_schedule
setup_schedule()
print('✓ Scheduler configured successfully')
"

# Test analyzer
python -c "
from src.storage.database import AdDatabase, Ad
from src.analyzers.ad_analyzer import AdAnalyzer

db = AdDatabase()
all_ads = db.session.query(Ad).all()
df = db._to_dataframe(all_ads)

analyzer = AdAnalyzer(df)
print(analyzer.get_insights_summary())
"
```

---

## Monitoring & Troubleshooting

### AWS Console Monitoring

1. **EC2 Dashboard**: https://console.aws.amazon.com/ec2/
   - View instance status
   - Check CPU/Network graphs
   - Review system logs

2. **CloudWatch Dashboard**: https://console.aws.amazon.com/cloudwatch/
   - View metrics: `EC2 > Per-Instance Metrics`
   - Check logs: `/aws/ec2/metaads-feasibility`

### Common Issues & Solutions

#### Issue 1: "Permission denied (publickey)"

**Cause**: SSH key permissions or wrong key

**Solution:**
```bash
# Fix key permissions
chmod 400 ~/.ssh/metaads-test.pem

# Verify using correct key
aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=metaads-feasibility-test" \
  --query 'Reservations[0].Instances[0].KeyName'

# Try with verbose SSH
ssh -v -i ~/.ssh/metaads-test.pem ec2-user@$INSTANCE_IP
```

#### Issue 2: "Connection timed out"

**Cause**: Security group or instance not ready

**Solution:**
```bash
# Check instance status
aws ec2 describe-instance-status \
  --instance-ids $(terraform output -raw instance_id)

# Check security group
aws ec2 describe-security-groups \
  --group-ids $(terraform output -raw security_group_id)

# Try pinging instance
ping $INSTANCE_IP

# Check if port 22 is open
nc -zv $INSTANCE_IP 22
```

#### Issue 3: "Invalid access token" (Meta API)

**Cause**: Expired or incorrect token in .env

**Solution:**
```bash
# Verify .env file exists and has token
ssh -i ~/.ssh/metaads-test.pem ec2-user@$INSTANCE_IP "cat ~/metaAds/.env"

# Test token directly
curl "https://graph.facebook.com/v18.0/me?access_token=YOUR_TOKEN"

# Regenerate token:
# 1. Go to https://developers.facebook.com/tools/explorer/
# 2. Generate new token with 'ads_read' permission
# 3. Update .env file and re-upload
```

#### Issue 4: "Rate limit exceeded"

**Cause**: Too many API requests

**Solution:**
```bash
# Check rate limiter logs
tail -f ~/metaAds/logs/*.log

# Reduce request frequency in config
python -c "
from src.config import Config
print(f'Rate limit: {Config.API_RATE_LIMIT} requests/hour')
"

# Wait 1 hour for rate limit reset
```

#### Issue 5: "Database is locked"

**Cause**: Multiple processes accessing SQLite

**Solution:**
```bash
# Check for multiple Python processes
ps aux | grep python

# Kill stale processes
pkill -f python

# Restart test
cd ~/metaAds && source venv/bin/activate && python example_usage.py
```

### Viewing Logs

```bash
# Application logs
tail -f ~/metaAds/logs/*.log

# System logs
sudo journalctl -u cloud-init -f

# User data execution log
sudo cat /var/log/user-data.log

# Python errors
cat ~/metaAds/logs/error.log 2>/dev/null || echo "No errors logged"
```

### Resource Monitoring Commands

```bash
# CPU usage
top -bn1 | grep "Cpu(s)" | awk '{print "CPU Usage: " $2 + $4 "%"}'

# Memory usage
free -h

# Disk usage
df -h /

# Network connections
netstat -an | grep ESTABLISHED | wc -l

# Process list
ps aux | grep python

# Check if running out of memory
dmesg | grep -i "out of memory"
```

---

## Results Documentation

### Step 1: Collect Performance Metrics

Create a results file on the EC2 instance:

```bash
cd ~/metaAds
cat > feasibility_results.txt <<'EOF'
╔══════════════════════════════════════════════════════════════════════╗
║           MetaAds AWS Feasibility Test - Results                     ║
╚══════════════════════════════════════════════════════════════════════╝

Test Date: $(date)
Duration: [Record start-end time]
Region: $(curl -s http://169.254.169.254/latest/meta-data/placement/region)
Instance Type: $(curl -s http://169.254.169.254/latest/meta-data/instance-type)

═══════════════════════════════════════════════════════════════════════
TEST RESULTS
═══════════════════════════════════════════════════════════════════════

1. API Connectivity Test
   Status: [PASS/FAIL]
   Response Time: [X.XX seconds]
   Errors: [None / Description]

2. Data Collection Test
   Status: [PASS/FAIL]
   Ads Collected: [X ads]
   Time Taken: [X seconds]
   Average per Ad: [X seconds]

3. Database Storage Test
   Status: [PASS/FAIL]
   Database Size: [X MB]
   Write Speed: [X records/sec]

4. Full Pipeline Test
   Status: [PASS/FAIL]
   Total Time: [X seconds]
   Errors: [None / Description]

═══════════════════════════════════════════════════════════════════════
PERFORMANCE METRICS
═══════════════════════════════════════════════════════════════════════

CPU Usage:
  - Idle: [X%]
  - During Collection: [X%]
  - Peak: [X%]

Memory Usage:
  - Base: [X MB]
  - During Collection: [X MB]
  - Peak: [X MB]

Disk I/O:
  - Read Speed: [X MB/s]
  - Write Speed: [X MB/s]
  - Database Size: [X MB]

Network:
  - Latency to Meta API: [X ms]
  - Bandwidth Used: [X MB]
  - Successful Requests: [X]
  - Failed Requests: [X]

═══════════════════════════════════════════════════════════════════════
ISSUES ENCOUNTERED
═══════════════════════════════════════════════════════════════════════

[List any errors, warnings, or unexpected behavior]

═══════════════════════════════════════════════════════════════════════
RECOMMENDATIONS
═══════════════════════════════════════════════════════════════════════

Instance Sizing:
  - Current: t3.micro
  - Recommendation: [Keep / Upgrade to t3.small / etc.]
  - Reasoning: [Explain]

Storage:
  - Current: 20 GB EBS
  - Recommendation: [Keep / Increase to 30 GB / etc.]
  - Reasoning: [Explain]

Network:
  - Recommendation: [Any networking improvements]

═══════════════════════════════════════════════════════════════════════
GO/NO-GO DECISION
═══════════════════════════════════════════════════════════════════════

Decision: [GO / NO-GO / NEEDS INVESTIGATION]

Reasoning:
[Detailed explanation of decision]

Next Steps:
[List action items based on decision]

═══════════════════════════════════════════════════════════════════════
EOF

# Edit the file with actual results
vim feasibility_results.txt
```

### Step 2: Generate Database Statistics

```bash
python -c "
from src.storage.database import AdDatabase, Ad
from src.analyzers.ad_analyzer import AdAnalyzer
import pandas as pd

db = AdDatabase()

# Get statistics
stats = db.get_stats()
print('═══════════════════════════════════════════════════════════')
print('DATABASE STATISTICS')
print('═══════════════════════════════════════════════════════════')
print(f'Total ads: {stats[\"total_ads\"]}')
print(f'Active ads: {stats[\"active_ads\"]}')
print(f'Inactive ads: {stats[\"inactive_ads\"]}')
print(f'Unique pages: {stats[\"unique_pages\"]}')

# Get insights
all_ads = db.session.query(Ad).all()
if all_ads:
    df = db._to_dataframe(all_ads)
    analyzer = AdAnalyzer(df)
    print('\\n' + analyzer.get_insights_summary())
" > database_stats.txt

cat database_stats.txt
```

### Step 3: Download Results Locally

```bash
# From your local machine
INSTANCE_IP=$(terraform output -raw instance_public_ip)

# Download results files
scp -i ~/.ssh/metaads-test.pem \
  ec2-user@$INSTANCE_IP:~/metaAds/feasibility_results.txt \
  ./

scp -i ~/.ssh/metaads-test.pem \
  ec2-user@$INSTANCE_IP:~/metaAds/database_stats.txt \
  ./

# Download database for local analysis (optional)
scp -i ~/.ssh/metaads-test.pem \
  ec2-user@$INSTANCE_IP:~/metaAds/data/ads_intelligence.db \
  ./data/
```

### Step 4: Create Results Document

Save results to the feasibility docs:

```bash
cd /Users/emadruga/proj/metaAds/aws_feasibility/docs

# Create results document
cat > FEASIBILITY_RESULTS.md <<'EOF'
# MetaAds AWS Feasibility Test - Results

## Test Summary

**Date**: [DATE]
**Duration**: [DURATION]
**Tester**: [NAME]
**Region**: us-east-1
**Instance**: t3.micro

## Executive Summary

[2-3 sentences summarizing the test outcome]

## Test Results

### 1. API Connectivity ✅/❌
[Details]

### 2. Data Collection ✅/❌
[Details]

### 3. Database Performance ✅/❌
[Details]

### 4. Full Pipeline ✅/❌
[Details]

## Performance Metrics

[Paste metrics from feasibility_results.txt]

## Issues Encountered

[List any issues]

## Recommendations

[Recommendations based on test]

## Decision

**GO / NO-GO / INVESTIGATE FURTHER**

[Reasoning]

## Next Steps

[Action items]
EOF

# Edit with actual results
code FEASIBILITY_RESULTS.md  # or vim, nano, etc.
```

---

## Cleanup

### Option 1: Destroy All Resources

**To completely remove everything:**

```bash
cd /Users/emadruga/proj/metaAds/aws_feasibility/terraform

# Review what will be destroyed
terraform plan -destroy

# Destroy all resources
terraform destroy

# Confirm when prompted
# Enter a value: yes
```

**Expected output:**
```
Destroy complete! Resources: 10 destroyed.
```

### Option 2: Stop Instance (Keep for Later)

**To stop instance but keep data:**

```bash
# Stop instance
aws ec2 stop-instances \
  --instance-ids $(terraform output -raw instance_id)

# Verify stopped
aws ec2 describe-instances \
  --instance-ids $(terraform output -raw instance_id) \
  --query 'Reservations[0].Instances[0].State.Name'

# Output: "stopping" or "stopped"
```

**To restart later:**

```bash
# Start instance
aws ec2 start-instances \
  --instance-ids $(terraform output -raw instance_id)

# Wait for running state
aws ec2 wait instance-running \
  --instance-ids $(terraform output -raw instance_id)

# Get new IP (if not using Elastic IP)
aws ec2 describe-instances \
  --instance-ids $(terraform output -raw instance_id) \
  --query 'Reservations[0].Instances[0].PublicIpAddress'
```

### Option 3: Keep Running (Monitor Costs)

If keeping instance running, set up billing alerts:

```bash
# Set up AWS billing alert (via AWS Console)
# 1. Go to CloudWatch
# 2. Create alarm for EstimatedCharges
# 3. Set threshold: $10
# 4. Add SNS notification to your email
```

### Cleanup Checklist

After testing is complete:

```bash
# 1. Download important files
scp -i ~/.ssh/metaads-test.pem -r \
  ec2-user@$INSTANCE_IP:~/metaAds/data/ \
  ./local_backup/

# 2. Save results documents
cp feasibility_results.txt ../docs/
cp database_stats.txt ../docs/

# 3. Verify backups
ls -la ./local_backup/

# 4. Destroy Terraform resources
cd terraform/
terraform destroy

# 5. Remove local SSH key (optional)
# rm ~/.ssh/metaads-test.pem

# 6. Delete AWS key pair (optional)
aws ec2 delete-key-pair --key-name metaads-test
```

---

## Appendix

### A. Useful Commands Reference

```bash
# ============================================================================
# Terraform Commands
# ============================================================================
terraform init              # Initialize Terraform
terraform plan              # Preview changes
terraform apply             # Apply changes
terraform destroy           # Destroy all resources
terraform output            # Show outputs
terraform state list        # List resources
terraform fmt               # Format code
terraform validate          # Validate syntax

# ============================================================================
# AWS CLI Commands
# ============================================================================
# EC2
aws ec2 describe-instances
aws ec2 start-instances --instance-ids i-xxx
aws ec2 stop-instances --instance-ids i-xxx
aws ec2 terminate-instances --instance-ids i-xxx

# SSH Key Pairs
aws ec2 describe-key-pairs
aws ec2 create-key-pair --key-name xxx
aws ec2 delete-key-pair --key-name xxx

# Security Groups
aws ec2 describe-security-groups
aws ec2 authorize-security-group-ingress --group-id sg-xxx --protocol tcp --port 22 --cidr x.x.x.x/32

# CloudWatch
aws logs tail /aws/ec2/metaads-feasibility --follow

# ============================================================================
# Instance Commands (via SSH)
# ============================================================================
# System
top                         # CPU/memory monitor
htop                        # Better top
df -h                       # Disk usage
free -h                     # Memory usage
uptime                      # System uptime
dmesg                       # Kernel messages

# Application
cd ~/metaAds
source venv/bin/activate
python test_api.py
python example_usage.py
tail -f logs/*.log

# Troubleshooting
sudo cat /var/log/user-data.log
sudo journalctl -u cloud-init
ps aux | grep python
netstat -tuln
```

### B. Cost Breakdown

| Resource | Type | Hourly | Daily | Monthly | Free Tier |
|----------|------|--------|-------|---------|-----------|
| EC2 t3.micro | Compute | $0.0104 | $0.25 | $7.50 | 750 hrs/month |
| EBS 20GB | Storage | $0.0011 | $0.03 | $2.00 | 30 GB/month |
| Data Transfer | Network | Variable | ~$0.01 | ~$0.50 | 100 GB/month |
| **Total** | | **~$0.01** | **~$0.29** | **~$10** | **$0** |

### C. Troubleshooting Decision Tree

```
Issue encountered?
├─ Cannot SSH
│  ├─ Check security group allows your IP
│  ├─ Verify key permissions (chmod 400)
│  └─ Confirm instance is running
│
├─ API test fails
│  ├─ Verify .env file exists
│  ├─ Check token validity
│  └─ Test network connectivity
│
├─ High CPU usage
│  ├─ Check for runaway processes
│  ├─ Review application logs
│  └─ Consider larger instance
│
└─ Database errors
   ├─ Check disk space
   ├─ Verify permissions
   └─ Kill duplicate processes
```

### D. Additional Resources

- **Terraform AWS Provider**: https://registry.terraform.io/providers/hashicorp/aws/latest/docs
- **AWS EC2 Documentation**: https://docs.aws.amazon.com/ec2/
- **Meta Ad Library API**: https://developers.facebook.com/docs/graph-api/reference/ads_archive
- **AWS Free Tier**: https://aws.amazon.com/free/
- **Terraform Best Practices**: https://www.terraform.io/docs/cloud/guides/recommended-practices/

---

## Questions & Support

### Common Questions

**Q: How much will this cost?**
A: Less than $1 for a 1-2 hour test, or $0 if using AWS Free Tier.

**Q: Can I use a different AWS region?**
A: Yes, just change `aws_region` in terraform.tfvars.

**Q: What if I don't have an SSH key pair?**
A: Follow the [SSH Key Pair Creation](#ssh-key-pair-creation) section.

**Q: Can I test with a private GitHub repo?**
A: Yes, but you'll need to configure SSH keys or use a personal access token.

**Q: How do I get a Meta API access token?**
A: Visit https://developers.facebook.com/tools/explorer/ and generate a token with `ads_read` permission.

### Getting Help

1. Check [FEASIBILITY_PLAN.md](FEASIBILITY_PLAN.md) for detailed architecture
2. Review [Terraform README](../terraform/README.md) for configuration help
3. Check AWS CloudWatch logs for errors
4. Review application logs on instance

---

**Document Version**: 1.0
**Last Updated**: 2026-02-21
**Tested On**: Amazon Linux 2023, Terraform 1.7.0, AWS CLI 2.15.0

---

## ✅ Quick Start Checklist

Use this checklist to track your progress:

- [ ] Install AWS CLI
- [ ] Install Terraform
- [ ] Configure AWS credentials
- [ ] Create SSH key pair
- [ ] Clone/fork repository
- [ ] Configure terraform.tfvars
- [ ] Run terraform init
- [ ] Run terraform plan
- [ ] Run terraform apply
- [ ] Wait for user data completion
- [ ] Copy .env file to instance
- [ ] SSH into instance
- [ ] Run API connectivity test
- [ ] Run data collection test
- [ ] Run full pipeline test
- [ ] Monitor performance
- [ ] Document results
- [ ] Make go/no-go decision
- [ ] Clean up resources

**Good luck with your feasibility test! 🚀**
