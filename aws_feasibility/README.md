# MetaAds AWS Feasibility Testing

## 📖 Overview

This directory contains everything needed to test the MetaAds data collection system on AWS infrastructure. The feasibility test validates that the application works correctly in a cloud environment before committing to a full production deployment.

## 🎯 Purpose

**Test Objective**: Validate MetaAds pipeline on AWS EC2 with minimal cost and effort.

**Timeline**: 60-90 minutes total
**Cost**: < $1 (or FREE with AWS Free Tier)

## 📁 Directory Structure

```
aws_feasibility/
├── README.md                    # This file - start here
├── docs/
│   ├── FEASIBILITY_PLAN.md      # Detailed test plan and architecture
│   ├── QUICKSTART.md            # Step-by-step tutorial (START HERE!)
│   └── FEASIBILITY_RESULTS.md   # Document results here (after testing)
└── terraform/
    ├── main.tf                  # Main infrastructure config
    ├── variables.tf             # Input variables
    ├── outputs.tf               # Output values
    ├── user_data.sh             # EC2 initialization script
    ├── terraform.tfvars.example # Example configuration
    ├── .gitignore               # Git ignore rules
    └── README.md                # Terraform usage guide
```

## 🚀 Quick Start

### 1. Read the Plan
First, understand what we're testing:
```bash
# Read the comprehensive feasibility plan
open docs/FEASIBILITY_PLAN.md
```

### 2. Follow the Tutorial
Then, follow the step-by-step guide:
```bash
# Follow the detailed quickstart guide
open docs/QUICKSTART.md
```

### 3. Deploy & Test
Execute the deployment:
```bash
cd terraform/
terraform init
terraform apply
# ... follow QUICKSTART.md steps
```

### 4. Document Results
After testing, record your findings:
```bash
# Edit the results document
vim docs/FEASIBILITY_RESULTS.md
```

## 📚 Documentation Guide

### For Different Users

**If you're a DevOps Engineer:**
- Start with: [terraform/README.md](terraform/README.md)
- Focus on: Infrastructure configuration and deployment

**If you're a Developer:**
- Start with: [QUICKSTART.md](docs/QUICKSTART.md)
- Focus on: Application testing and validation

**If you're a Manager/Decision Maker:**
- Start with: [FEASIBILITY_PLAN.md](docs/FEASIBILITY_PLAN.md)
- Focus on: Cost analysis and success metrics

**If you want to understand everything:**
1. Read [FEASIBILITY_PLAN.md](docs/FEASIBILITY_PLAN.md) - The "why"
2. Read [QUICKSTART.md](docs/QUICKSTART.md) - The "how"
3. Review [terraform/main.tf](terraform/main.tf) - The "what"

## 🎓 What Each Document Contains

### [docs/FEASIBILITY_PLAN.md](docs/FEASIBILITY_PLAN.md)
**Purpose**: Comprehensive test plan and architecture design

**Contains**:
- Objective and success criteria
- Infrastructure architecture
- Terraform design decisions
- Security considerations
- Cost analysis
- Testing protocol
- Decision framework

**Read if**: You want to understand WHY we're doing this test and WHAT we're testing.

**Length**: ~600 lines (20-30 minutes read)

---

### [docs/QUICKSTART.md](docs/QUICKSTART.md)
**Purpose**: Step-by-step deployment and testing tutorial

**Contains**:
- Prerequisites checklist
- AWS account setup
- SSH key creation
- Terraform configuration
- Deployment steps
- Testing procedures
- Troubleshooting guide
- Cleanup instructions

**Read if**: You want to EXECUTE the test right now.

**Length**: ~900 lines (15 minutes to read, 60-90 minutes to complete)

---

### [terraform/README.md](terraform/README.md)
**Purpose**: Terraform-specific usage guide

**Contains**:
- Terraform file explanations
- Configuration variables
- Resource descriptions
- Quick reference commands

**Read if**: You're familiar with Terraform and want quick reference.

**Length**: ~200 lines (5 minutes read)

---

## ✅ Prerequisites Checklist

Before starting, ensure you have:

### Software
- [ ] AWS CLI installed and configured
- [ ] Terraform >= 1.0 installed
- [ ] Git installed
- [ ] SSH client available

### Accounts & Credentials
- [ ] AWS account (Free Tier recommended)
- [ ] Meta Developer account
- [ ] Meta API access token

### AWS Setup
- [ ] SSH key pair created in AWS
- [ ] AWS credentials configured locally
- [ ] Sufficient IAM permissions (EC2, IAM, CloudWatch)

### Project Setup
- [ ] MetaAds repository cloned/forked
- [ ] `.env` file with Meta API token ready

## 🎯 Success Criteria

The test is successful if:

- ✅ Meta Ad Library API is accessible from AWS
- ✅ Data collection retrieves 50+ ads successfully
- ✅ Database storage works correctly
- ✅ No critical errors or exceptions
- ✅ Performance is acceptable (CPU < 50%, Memory < 500MB)

## 💰 Cost Estimate

| Scenario | Cost |
|----------|------|
| **1-2 hour test** | < $1 |
| **Full day test** | ~$2 |
| **One month (24/7)** | ~$10 |
| **With Free Tier** | $0 |

**Note**: Costs assume t3.micro instance + 20GB EBS storage in us-east-1.

## 🔄 Typical Test Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. PREPARATION (15 min)                                     │
│    └─ Install tools, configure AWS, create SSH keys        │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. DEPLOYMENT (10 min)                                      │
│    └─ Run terraform apply, wait for instance ready         │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. CONFIGURATION (5 min)                                    │
│    └─ Copy .env file, SSH into instance, verify setup      │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. TESTING (30 min)                                         │
│    └─ Run API test, collect data, validate pipeline        │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. ANALYSIS (15 min)                                        │
│    └─ Review metrics, document results, make decision      │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. CLEANUP (5 min)                                          │
│    └─ Download results, destroy resources                   │
└─────────────────────────────────────────────────────────────┘

Total Time: ~80 minutes
```

## 🛠 Infrastructure Components

The Terraform configuration creates:

| Resource | Purpose | Free Tier Eligible |
|----------|---------|-------------------|
| EC2 Instance (t3.micro) | Run MetaAds app | ✅ Yes (750 hrs/mo) |
| Security Group | Network access control | ✅ Yes |
| IAM Role | AWS service permissions | ✅ Yes |
| EBS Volume (20GB) | Data storage | ✅ Yes (30GB/mo) |
| CloudWatch Log Group | Centralized logging | ✅ Yes (5GB/mo) |
| Elastic IP (optional) | Persistent public IP | ⚠️ Charged when detached |

## 📊 Test Outputs

After testing, you'll have:

1. **Performance Metrics**
   - CPU usage patterns
   - Memory consumption
   - Disk I/O statistics
   - Network latency measurements

2. **Functionality Validation**
   - API connectivity confirmed
   - Data collection verified
   - Database integrity checked
   - Pipeline execution validated

3. **Cost Data**
   - Actual AWS costs incurred
   - Resource utilization patterns
   - Scaling recommendations

4. **Decision Recommendation**
   - Go/No-go for AWS deployment
   - Infrastructure sizing suggestions
   - Identified risks and mitigations

## 🚨 Common Issues & Quick Fixes

### "Permission denied (publickey)"
```bash
chmod 400 ~/.ssh/metaads-test.pem
```

### "Invalid access token"
```bash
# Regenerate token at: https://developers.facebook.com/tools/explorer/
# Update .env file and re-upload
```

### "Connection timed out"
```bash
# Check security group allows your IP
terraform output security_group_id
```

### "Resource already exists"
```bash
# Destroy and recreate
terraform destroy && terraform apply
```

## 🔗 Related Documentation

### Internal Project Docs
- [Main README](../../README.md) - Project overview
- [CLAUDE.md](../../CLAUDE.md) - Implementation guide
- [src/ documentation](../../src/) - Code documentation

### External Resources
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [AWS EC2 Documentation](https://docs.aws.amazon.com/ec2/)
- [Meta Ad Library API](https://developers.facebook.com/docs/graph-api/reference/ads_archive)
- [AWS Free Tier](https://aws.amazon.com/free/)

## 🎯 Next Steps After Testing

### If Test Succeeds (GO Decision)

1. **Immediate**:
   - Document results in FEASIBILITY_RESULTS.md
   - Share findings with team
   - Plan production deployment

2. **Short-term** (1-2 weeks):
   - Design production architecture
   - Implement CI/CD pipeline
   - Set up monitoring and alerting

3. **Long-term** (1-3 months):
   - Deploy to production
   - Scale based on usage
   - Optimize costs

### If Test Fails (NO-GO Decision)

1. **Investigate**:
   - Review error logs
   - Identify root causes
   - Test alternative configurations

2. **Consider Alternatives**:
   - Different AWS region
   - Different instance types
   - Alternative cloud providers
   - Hybrid deployment

3. **Re-test**:
   - Fix identified issues
   - Run modified test
   - Re-evaluate decision

## 📞 Support & Questions

### Before You Start
1. Read [FEASIBILITY_PLAN.md](docs/FEASIBILITY_PLAN.md)
2. Review [QUICKSTART.md](docs/QUICKSTART.md)
3. Check prerequisites checklist

### During Testing
1. Check [QUICKSTART.md Troubleshooting](docs/QUICKSTART.md#monitoring--troubleshooting)
2. Review CloudWatch logs
3. Check application logs on instance

### After Testing
1. Document results in FEASIBILITY_RESULTS.md
2. Review with team
3. Make go/no-go decision

## 📝 Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-21 | Initial release |

## 📄 License

This feasibility test infrastructure is part of the MetaAds project.

---

## 🎬 Ready to Start?

### Option 1: Quick Start (Experienced Users)
```bash
cd terraform/
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars
terraform init
terraform apply
# Follow outputs for next steps
```

### Option 2: Guided Tutorial (Recommended)
```bash
# Open the step-by-step guide
open docs/QUICKSTART.md
# Follow instructions carefully
```

### Option 3: Understand First (Thorough)
```bash
# Read the detailed plan
open docs/FEASIBILITY_PLAN.md
# Then follow the tutorial
open docs/QUICKSTART.md
```

---

**🚀 Good luck with your feasibility test!**

For questions or issues, refer to the [QUICKSTART.md troubleshooting section](docs/QUICKSTART.md#monitoring--troubleshooting).
