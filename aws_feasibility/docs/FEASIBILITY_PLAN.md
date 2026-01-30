# MetaAds AWS Feasibility Test Plan

## Document Purpose

This document outlines the feasibility study for running the MetaAds data collection system on AWS infrastructure, specifically testing whether the existing codebase works effectively in a cloud environment before committing to a full production deployment.

---

## Objective

**Primary Goal**: Validate that the MetaAds data collection pipeline works correctly on AWS EC2 with minimal modifications.

**Success Criteria**:
- ✅ Meta Ad Library API connectivity from AWS works
- ✅ Data collection module successfully retrieves ads
- ✅ Database storage (SQLite) functions properly on EBS
- ✅ Performance is acceptable (response times, throughput)
- ✅ No unexpected networking/security issues
- ✅ Resource usage (CPU/Memory) is within expected bounds

**Timeline**: 1-2 hours for complete test

**Budget**: $0-1 (using Free Tier or minimal instance hours)

---

## What We're Testing

### 1. **Core Data Collection Pipeline**
```
Meta Ad Library API → Collector → Parser → SQLite Database
```

**Components to validate**:
- `src/collectors/meta_api_collector.py` - API calls from AWS
- `src/processors/ad_parser.py` - Data processing
- `src/storage/database.py` - SQLite on EBS storage
- `test_api.py` - API connectivity verification
- `example_usage.py` - End-to-end pipeline test

### 2. **Infrastructure Requirements**
- Network connectivity to Meta API endpoints
- Outbound HTTPS (port 443) access
- SSH access for management
- Sufficient compute resources (CPU/Memory)
- Storage performance for SQLite database

### 3. **Key Questions to Answer**
1. Does the Meta API accept requests from AWS IP ranges?
2. Are there any latency issues compared to local development?
3. Does SQLite perform adequately on EBS volumes?
4. What's the actual resource consumption pattern?
5. Are there any AWS-specific errors or limitations?

---

## Test Methodology

### Phase 1: Infrastructure Setup (via Terraform)
- Launch minimal EC2 instance (t3.micro)
- Configure security groups (SSH only)
- Provision EBS volume for data storage
- Setup basic CloudWatch monitoring

### Phase 2: Application Deployment (automated via user_data)
- Clone GitHub repository
- Install Python 3.12 and dependencies
- Setup virtual environment
- Prepare directory structure

### Phase 3: Manual Configuration
- Copy `.env` file with credentials (manual/secure)
- Verify environment variables

### Phase 4: Testing & Validation
- Run `test_api.py` - verify API connectivity
- Run `example_usage.py` - test data collection
- Collect sample dataset (50-100 ads)
- Monitor resource usage
- Check database integrity

### Phase 5: Results Analysis
- Document performance metrics
- Identify any issues or limitations
- Make go/no-go decision for full deployment

---

## Terraform Infrastructure Design

### File Structure
```
aws_feasibility/
├── terraform/
│   ├── main.tf           # Main infrastructure resources
│   ├── variables.tf      # Input variables
│   ├── outputs.tf        # Output values (IP address, etc)
│   ├── user_data.sh      # EC2 initialization script
│   ├── terraform.tfvars  # Variable values (gitignored)
│   └── README.md         # Terraform usage instructions
└── docs/
    ├── FEASIBILITY_PLAN.md      # This document
    └── FEASIBILITY_RESULTS.md   # Test results (to be created)
```

### Terraform Resources

#### 1. **Security Group** (`aws_security_group.metaads_sg`)
**Purpose**: Control network access to EC2 instance

**Ingress Rules**:
- Port 22 (SSH) - restricted to your IP or VPN CIDR
  - Configurable via variable `allowed_ssh_cidr`
  - Default: `["0.0.0.0/0"]` (change this for production!)

**Egress Rules**:
- All outbound traffic allowed (for API calls, package downloads)

**Why**: Minimal security posture for testing while allowing necessary access.

---

#### 2. **EC2 Instance** (`aws_instance.metaads`)
**Purpose**: Run the MetaAds application

**Specifications**:
- **AMI**: Latest Amazon Linux 2023 (auto-selected via data source)
- **Instance Type**: `t3.micro` (default, configurable)
  - 2 vCPUs, 1 GB RAM
  - Free Tier eligible (750 hours/month)
  - Cost: ~$0.01/hour if not on Free Tier
- **Storage**: 8-20 GB EBS volume (gp3, encrypted)
- **Key Pair**: User-provided SSH key (must exist in AWS)

**Why**: Minimal cost, sufficient for testing, Free Tier eligible.

---

#### 3. **User Data Script** (`user_data.sh`)
**Purpose**: Automated setup after instance launch

**Tasks performed**:
1. System updates (`yum update`)
2. Install dependencies:
   - Python 3.12
   - Git
   - pip
3. Clone repository from GitHub
4. Create virtual environment
5. Install Python packages from `requirements.txt`
6. Create necessary directories (`data/`, `logs/`, `reports/`)
7. Set proper permissions
8. Create setup marker file

**Why**: Fully automated deployment - instance is ready to use immediately after launch.

---

#### 4. **Elastic IP** (`aws_eip.metaads_eip`) - OPTIONAL
**Purpose**: Persistent public IP address

**Configuration**:
- Controlled by variable `use_elastic_ip` (default: `false`)
- Useful if you need consistent IP for:
  - SSH access from whitelisted IPs
  - DNS configuration
  - IP-based monitoring

**Cost**: FREE while attached to running instance, $0.005/hour if detached

**Why**: Optional - most tests don't need this, but available if required.

---

#### 5. **CloudWatch Log Group** (`aws_cloudwatch_log_group.metaads_logs`)
**Purpose**: Centralized log storage (future use)

**Configuration**:
- Log group: `/aws/ec2/metaads`
- Retention: Configurable (default: 7 days)
- Optional CloudWatch agent can stream application logs here

**Why**: Prepared for future monitoring, minimal cost for short-term testing.

---

### Configuration Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `aws_region` | string | `us-east-1` | AWS region for deployment |
| `instance_type` | string | `t3.micro` | EC2 instance type |
| `key_name` | string | **REQUIRED** | SSH key pair name (must exist) |
| `allowed_ssh_cidr` | list(string) | `["0.0.0.0/0"]` | CIDR blocks for SSH access |
| `github_repo_url` | string | `https://github.com/yourusername/metaAds.git` | Repository URL |
| `github_branch` | string | `main` | Branch to clone |
| `root_volume_size` | number | `20` | Root EBS volume size (GB) |
| `use_elastic_ip` | bool | `false` | Whether to allocate Elastic IP |
| `log_retention_days` | number | `7` | CloudWatch log retention |
| `environment` | string | `feasibility-test` | Environment tag |

---

## User Data Script Design

### Script Flow
```bash
#!/bin/bash
# Executed at instance first boot

1. Log all output to /var/log/user-data.log
2. Update system packages
3. Install Python 3.12, git, development tools
4. Create application user (optional) or use ec2-user
5. Clone repository to /home/ec2-user/metaAds
6. Create Python virtual environment
7. Install dependencies from requirements.txt
8. Create directory structure (data/, logs/, reports/)
9. Set file permissions
10. Create marker file: /home/ec2-user/setup_complete.txt
```

### Why User Data vs Manual Setup?
- **Automation**: Repeatable, consistent deployments
- **Speed**: Instance ready in 5-10 minutes after launch
- **Documentation**: Setup process is code (Infrastructure as Code)
- **Testing**: Can tear down and rebuild easily

### What's NOT in User Data?
- **`.env` file**: Contains secrets (FB_ACCESS_TOKEN), must be copied manually
- **SSH keys**: Security best practice
- **Application execution**: We want manual control for testing

---

## Security Considerations

### Secrets Management
**Problem**: `.env` file contains sensitive API tokens

**Solution for Feasibility Test**:
1. `.env` file is gitignored (not in repository)
2. User manually copies `.env` to EC2 after launch
3. Transfer via SCP:
   ```bash
   scp -i your-key.pem .env ec2-user@<instance-ip>:~/metaAds/
   ```

**Future Production Options**:
- AWS Systems Manager Parameter Store
- AWS Secrets Manager
- Environment variables via Terraform (encrypted)

### SSH Access
**Feasibility Test**:
- Allow SSH from anywhere (`0.0.0.0/0`) or your IP
- Use SSH key pair for authentication

**Production**:
- Restrict to bastion host or VPN CIDR
- Consider AWS Systems Manager Session Manager (no SSH needed)

### API Keys
- Meta API token stored in `.env` file
- File permissions: `600` (readable only by owner)
- Never commit to version control

---

## Cost Analysis

### Feasibility Test (1-2 hours)
- **EC2 t3.micro**: $0.02 (Free Tier: $0)
- **EBS storage (20 GB)**: $0.01
- **Data transfer**: Negligible
- **CloudWatch logs**: Negligible
- **Total**: < $0.05 or FREE (Free Tier)

### Monthly Cost (if kept running)
- **EC2 t3.micro**: $7.50/month (Free Tier: $0)
- **EBS storage (20 GB)**: $2.00/month
- **CloudWatch logs (basic)**: $0.50/month
- **Total**: $10/month or $0/month (Free Tier)

### Cost Optimization
- Use Reserved Instances for long-term (save 40-60%)
- Use Spot Instances for non-critical workloads (save 70-90%)
- Schedule instance stop/start (only pay for hours used)

---

## Testing Protocol

### Step 1: Terraform Deployment
```bash
cd aws_feasibility/terraform

# Initialize Terraform
terraform init

# Review planned changes
terraform plan

# Apply configuration
terraform apply

# Note the instance IP from output
```

### Step 2: Copy Environment File
```bash
# From local machine
scp -i ~/.ssh/your-key.pem .env ec2-user@<instance-ip>:~/metaAds/
```

### Step 3: SSH and Verify Setup
```bash
ssh -i ~/.ssh/your-key.pem ec2-user@<instance-ip>

# Check setup completion
cat ~/setup_complete.txt

# Activate virtual environment
cd ~/metaAds
source venv/bin/activate

# Verify .env file
ls -la .env
```

### Step 4: Run Tests
```bash
# Test 1: API connectivity
python test_api.py

# Test 2: Basic data collection
python example_usage.py

# Test 3: Collect sample dataset
python -c "
from src.collectors.meta_api_collector import MetaAdLibraryAPI
api = MetaAdLibraryAPI()
ads = api.search_ads('video editing ai', limit=50)
print(f'Collected {len(ads)} ads')
"

# Test 4: Full pipeline
python -c "
from src.main import AdIntelligencePipeline
pipeline = AdIntelligencePipeline()
results = pipeline.collect_and_analyze(['video editing ai'], limit_per_keyword=20)
print(f'Pipeline results: {list(results.keys())}')
"
```

### Step 5: Monitor Resources
```bash
# Check CPU and memory usage
top

# Check disk usage
df -h

# Check database size
ls -lh data/*.db

# Check logs
tail -f logs/*.log
```

### Step 6: Document Results
Record findings in `aws_feasibility/docs/FEASIBILITY_RESULTS.md`:
- API connectivity: Success/Failure
- Response times: Average, Min, Max
- Resource usage: CPU %, Memory usage
- Disk I/O: SQLite performance
- Errors encountered: List any issues
- Recommendations: Go/No-go decision

---

## Success Metrics

### Must Pass (Go/No-Go)
- [ ] API connectivity works from AWS
- [ ] Can collect at least 50 ads successfully
- [ ] No critical errors or exceptions
- [ ] Database writes succeed
- [ ] Data integrity is maintained

### Performance Targets (Nice to Have)
- [ ] API response time < 3 seconds per request
- [ ] Memory usage < 500 MB
- [ ] CPU usage < 50% during collection
- [ ] Collect 100 ads in < 10 minutes
- [ ] Database queries < 100ms

### Issues That Need Investigation
- Intermittent API timeouts
- High memory usage
- Slow database writes
- Network errors
- Rate limiting issues

---

## Decision Tree After Testing

```
Test Results
    │
    ├─ All Tests Pass
    │   └─> ✅ PROCEED with AWS deployment
    │       Options:
    │       A. Keep EC2 approach (simple, proven)
    │       B. Explore Lambda for serverless
    │       C. Add RDS for better database
    │
    ├─ Minor Issues
    │   └─> ⚠️  INVESTIGATE & FIX
    │       - Adjust instance type
    │       - Optimize code
    │       - Retry with fixes
    │
    └─ Major Failures
        └─> ❌ RECONSIDER approach
            - API blocked from AWS IPs?
            - Architecture mismatch?
            - Alternative solutions needed?
```

---

## Next Steps After Feasibility

### If Successful → Production Deployment
1. **Infrastructure Improvements**:
   - Auto Scaling Group for redundancy
   - Application Load Balancer (if needed)
   - RDS PostgreSQL instead of SQLite
   - S3 for data backups
   - CloudWatch alarms and dashboards

2. **Security Hardening**:
   - Secrets Manager for credentials
   - IAM roles for AWS service access
   - VPC with private subnets
   - Security group restrictions
   - Regular security updates

3. **Operational Excellence**:
   - Automated backups
   - Monitoring and alerting
   - Log aggregation
   - Disaster recovery plan
   - Cost optimization

### If Unsuccessful → Alternative Paths
1. **Investigate Issues**:
   - Work with AWS support
   - Review Meta API documentation
   - Test from different regions

2. **Consider Alternatives**:
   - Different cloud provider (GCP, Azure)
   - Hybrid approach (local + cloud)
   - Managed services (Zapier, n8n)

---

## Rollback Plan

If testing goes wrong, easy cleanup:

```bash
# Destroy all resources
cd aws_feasibility/terraform
terraform destroy -auto-approve

# Or just stop instance (to preserve data)
aws ec2 stop-instances --instance-ids <instance-id>
```

**Recovery**:
- Terraform state allows complete recreation
- No manual cleanup needed
- All resources tagged for easy identification

---

## Terraform Best Practices Applied

1. **Variables**: All configurable values externalized
2. **Outputs**: Important values (IP, ID) exported
3. **Tagging**: All resources tagged (Project, Environment)
4. **Security**: Encryption enabled on EBS volumes
5. **Documentation**: Inline comments in code
6. **State Management**: Local state for feasibility (remote for production)
7. **Modularity**: Organized, reusable code structure

---

## Timeline

| Phase | Duration | Activity |
|-------|----------|----------|
| Preparation | 15 min | Write Terraform code, configure variables |
| Deployment | 10 min | Run `terraform apply`, wait for instance |
| Configuration | 5 min | Copy `.env`, verify setup |
| Testing | 30 min | Run test suite, collect sample data |
| Analysis | 15 min | Review results, document findings |
| **Total** | **75 min** | Complete feasibility study |

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| API blocked from AWS IPs | Low | High | Test from multiple regions |
| Unexpected AWS costs | Low | Low | Set billing alerts, use Free Tier |
| Instance setup fails | Low | Low | User data logs, manual fallback |
| .env file lost/exposed | Medium | High | Secure transfer via SCP, proper permissions |
| Poor performance | Low | Medium | Right-size instance, optimize code |

---

## Conclusion

This feasibility test provides a **low-risk, low-cost way** to validate the MetaAds system on AWS infrastructure before committing to a full production deployment.

**Key Benefits**:
- ✅ Infrastructure as Code (repeatable)
- ✅ Automated setup (minimal manual work)
- ✅ Real-world testing (actual AWS environment)
- ✅ Fast feedback (results in 1-2 hours)
- ✅ Low cost (< $1 or free)
- ✅ Easy cleanup (one command)

**Expected Outcome**:
Clear go/no-go decision on AWS deployment with empirical data to support the choice.

---

## Appendix: Useful Commands

### Terraform
```bash
# Initialize
terraform init

# Plan (preview changes)
terraform plan

# Apply (create resources)
terraform apply

# Show current state
terraform show

# Get outputs
terraform output

# Destroy everything
terraform destroy
```

### AWS CLI
```bash
# List instances
aws ec2 describe-instances --filters "Name=tag:Project,Values=MetaAds"

# Connect to instance
aws ec2-instance-connect ssh --instance-id <id>

# Get instance public IP
aws ec2 describe-instances --instance-ids <id> --query 'Reservations[0].Instances[0].PublicIpAddress'
```

### EC2 Instance
```bash
# Check user data execution log
sudo cat /var/log/user-data.log

# Check system logs
sudo journalctl -u cloud-final

# Monitor resources
htop  # if installed
top
free -h
df -h
```

---

**Document Version**: 1.0
**Date**: 2026-01-30
**Author**: MetaAds Team
**Status**: Ready for Implementation
