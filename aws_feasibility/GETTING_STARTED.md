# Getting Started - MetaAds AWS Feasibility Test

## 🚀 3-Minute Quick Start

If you're experienced with AWS and Terraform, here's the fastest path:

```bash
# 1. Navigate to terraform directory
cd aws_feasibility/terraform

# 2. Configure your settings
cp terraform.tfvars.example terraform.tfvars
vim terraform.tfvars  # Update: key_name, github_repo_url, allowed_ssh_cidr

# 3. Deploy
terraform init
terraform apply

# 4. Wait ~5 minutes for setup, then copy .env
scp -i ~/.ssh/your-key.pem .env ec2-user@$(terraform output -raw instance_public_ip):~/metaAds/

# 5. Test
ssh -i ~/.ssh/your-key.pem ec2-user@$(terraform output -raw instance_public_ip)
cd metaAds && source venv/bin/activate && python test_api.py

# 6. Cleanup when done
terraform destroy
```

---

## 📚 Full Documentation

Choose your path based on your experience level:

### 🟢 Beginner (New to AWS/Terraform)
→ **Start here**: [QUICKSTART.md](docs/QUICKSTART.md)

This comprehensive guide includes:
- Prerequisites installation
- AWS account setup
- Step-by-step Terraform deployment
- Detailed testing procedures
- Troubleshooting help

**Time**: 90 minutes | **Difficulty**: Easy

---

### 🟡 Intermediate (Familiar with AWS)
→ **Start here**: [terraform/README.md](terraform/README.md)

Quick reference for:
- Terraform configuration
- Variable customization
- Resource descriptions
- Common commands

**Time**: 30 minutes | **Difficulty**: Medium

---

### 🔴 Advanced (DevOps/Infrastructure)
→ **Start here**: [FEASIBILITY_PLAN.md](docs/FEASIBILITY_PLAN.md)

Deep dive into:
- Architecture decisions
- Infrastructure design
- Security considerations
- Cost optimization

**Time**: 20 minutes read + 30 minutes deploy | **Difficulty**: Advanced

---

## 🎯 What You'll Accomplish

By the end of this test, you'll know:

✅ Does MetaAds work on AWS infrastructure?
✅ What are the actual costs and performance?
✅ Should we proceed with AWS deployment?
✅ What instance size is needed?
✅ Are there any blockers or issues?

---

## 📋 Prerequisites Quick Check

Before starting, verify you have:

```bash
# Check AWS CLI
aws --version
# Expected: aws-cli/2.x.x

# Check Terraform
terraform version
# Expected: Terraform v1.x.x

# Check AWS credentials
aws sts get-caller-identity
# Expected: JSON with your account info

# Check you have an SSH key pair in AWS
aws ec2 describe-key-pairs --region us-east-1
# Expected: List of your key pairs
```

**If any command fails**, see [QUICKSTART.md Prerequisites](docs/QUICKSTART.md#prerequisites).

---

## 💡 Key Files Reference

| File | Purpose | When to Use |
|------|---------|-------------|
| [README.md](README.md) | Overview & navigation | Start here |
| [GETTING_STARTED.md](GETTING_STARTED.md) | Quick paths (this file) | Choose your route |
| [docs/QUICKSTART.md](docs/QUICKSTART.md) | Step-by-step tutorial | Follow instructions |
| [docs/FEASIBILITY_PLAN.md](docs/FEASIBILITY_PLAN.md) | Detailed architecture | Understand design |
| [terraform/main.tf](terraform/main.tf) | Infrastructure code | Deploy resources |
| [terraform/README.md](terraform/README.md) | Terraform guide | Configuration help |

---

## ⚡ Most Common Issues

### Issue: "No SSH key pair"
```bash
# Create one:
aws ec2 create-key-pair --key-name metaads-test \
  --query 'KeyMaterial' --output text > ~/.ssh/metaads-test.pem
chmod 400 ~/.ssh/metaads-test.pem
```

### Issue: "Invalid access token"
```bash
# Get new token:
# 1. Visit: https://developers.facebook.com/tools/explorer/
# 2. Generate token with 'ads_read' permission
# 3. Update .env file
```

### Issue: "Terraform command not found"
```bash
# Install Terraform:
# macOS: brew install terraform
# Linux: Download from terraform.io
```

---

## 🎓 Learning Path

### Day 1: Understanding
1. Read [README.md](README.md) (5 min)
2. Read [FEASIBILITY_PLAN.md](docs/FEASIBILITY_PLAN.md) (20 min)
3. Review [terraform/main.tf](terraform/main.tf) (10 min)

### Day 2: Preparation
1. Install prerequisites (30 min)
2. Configure AWS credentials (10 min)
3. Create SSH key pair (5 min)

### Day 3: Deployment
1. Follow [QUICKSTART.md](docs/QUICKSTART.md) (60 min)
2. Run tests and validate (30 min)
3. Document results (15 min)

### Day 4: Decision
1. Review test results
2. Analyze costs and performance
3. Make go/no-go decision

---

## 💰 Cost Calculator

Estimate your test cost:

**Test Duration:**
- 1 hour: $0.01
- 4 hours: $0.04
- 8 hours: $0.08
- 24 hours: $0.25
- 1 week: $1.75

**Monthly (if kept running):**
- t3.micro + 20GB EBS: ~$9.50/month
- **FREE** with AWS Free Tier (first 12 months)

---

## 🤝 Getting Help

### Before Deploying
- Check [Prerequisites](docs/QUICKSTART.md#prerequisites)
- Review [FEASIBILITY_PLAN.md](docs/FEASIBILITY_PLAN.md)

### During Deployment
- See [Troubleshooting](docs/QUICKSTART.md#monitoring--troubleshooting)
- Check Terraform outputs
- Review user data logs

### After Testing
- Document in [FEASIBILITY_RESULTS.md](docs/FEASIBILITY_RESULTS.md)
- Review with team
- Make decision

---

## ✅ Success Checklist

Copy this checklist to track your progress:

```
Setup Phase:
□ AWS CLI installed and configured
□ Terraform installed
□ SSH key pair created in AWS
□ Repository cloned locally
□ .env file with Meta API token ready

Configuration Phase:
□ terraform.tfvars created and configured
□ Variables validated (key_name, repo URL)
□ Security group rules reviewed

Deployment Phase:
□ terraform init completed
□ terraform plan reviewed
□ terraform apply successful
□ Instance running and accessible

Testing Phase:
□ .env file copied to instance
□ API connectivity test passed
□ Data collection test passed
□ Full pipeline test passed
□ Performance metrics recorded

Completion Phase:
□ Results documented
□ Decision made (GO/NO-GO)
□ Resources cleaned up (terraform destroy)
□ Team notified
```

---

## 🎬 Ready to Begin?

### Path 1: "Just tell me what to do"
→ Open [QUICKSTART.md](docs/QUICKSTART.md) and follow every step

### Path 2: "I know AWS, show me the config"
→ Check [terraform/](terraform/) directory and deploy

### Path 3: "I want to understand everything first"
→ Read [FEASIBILITY_PLAN.md](docs/FEASIBILITY_PLAN.md) then [QUICKSTART.md](docs/QUICKSTART.md)

---

**Good luck! 🚀**

Questions? Check the [troubleshooting section](docs/QUICKSTART.md#monitoring--troubleshooting) or review the [FAQ](docs/QUICKSTART.md#questions--support).
