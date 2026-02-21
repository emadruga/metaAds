# AWS Academy / Restricted Account Guide

## Overview

This guide is specifically for users with **restricted AWS permissions** (AWS Academy, AWS Educate, or limited IAM permissions). The standard Terraform configuration has been simplified to work without IAM role creation.

## What Changed?

### Removed Features (Due to Permission Restrictions)
- ❌ IAM Role creation (`aws_iam_role.metaads_ec2_role`)
- ❌ IAM Instance Profile (`iam_instance_profile`)
- ❌ CloudWatch Agent (requires IAM permissions)
- ❌ AWS Systems Manager (SSM) Session Manager

### Still Available
- ✅ EC2 Instance (t3.micro)
- ✅ Security Groups
- ✅ EBS Volumes (encrypted)
- ✅ User Data (automated setup)
- ✅ CloudWatch basic metrics (CPU, network)
- ✅ All MetaAds functionality

## Deployment Instructions

### 1. Configure Terraform

```bash
cd aws_feasibility/terraform

# Copy and edit configuration
cp terraform.tfvars.example terraform.tfvars
vim terraform.tfvars

# Required changes:
# - key_name: Your SSH key pair name
# - github_repo_url: Your repository URL
# - allowed_ssh_cidr: Your IP address
```

### 2. Deploy

```bash
# Initialize
terraform init

# Deploy (no approval needed for testing)
terraform apply -auto-approve
```

### 3. Wait for Setup

The user_data script takes **5-10 minutes** to complete:

```bash
# Check if ready (wait 5-10 minutes first)
ssh -i ~/.ssh/your-key.pem ec2-user@YOUR_IP "cat ~/setup_complete.txt"

# Watch setup progress
ssh -i ~/.ssh/your-key.pem ec2-user@YOUR_IP "sudo tail -f /var/log/user-data.log"
```

### 4. Copy .env File

```bash
cd /Users/emadruga/proj/metaAds
scp -i ~/.ssh/your-key.pem .env ec2-user@YOUR_IP:~/metaAds/
```

### 5. Test

```bash
# SSH into instance
ssh -i ~/.ssh/your-key.pem ec2-user@YOUR_IP

# Activate environment
cd ~/metaAds
source venv/bin/activate

# Run tests
python test_api.py
python example_usage.py
```

## Monitoring Without IAM

Since CloudWatch Agent requires IAM permissions, use these alternatives:

### System Logs

```bash
# View user data execution log
sudo cat /var/log/user-data.log

# Watch system logs
sudo journalctl -f

# Check cloud-init logs
sudo cat /var/log/cloud-init-output.log
```

### Application Logs

```bash
# Application logs
tail -f ~/metaAds/logs/*.log

# Database logs (if any)
ls -lh ~/metaAds/data/
```

### Resource Monitoring

```bash
# CPU and memory
top
# or
htop

# Disk usage
df -h

# Network connections
netstat -tuln

# Process list
ps aux | grep python
```

### AWS Console

Basic metrics are still available in the AWS Console:
- CPU Utilization
- Network In/Out
- Disk Read/Write
- Instance Status Checks

**View metrics:**
https://console.aws.amazon.com/ec2/v2/home?region=us-east-1#Instances

## Troubleshooting

### Issue: "Permission denied (publickey)"

```bash
# Check key permissions
chmod 400 ~/.ssh/your-key.pem

# Verify key name matches
aws ec2 describe-key-pairs --region us-east-1
```

### Issue: "Connection refused" or "No route to host"

```bash
# Wait for instance to fully boot
aws ec2 describe-instance-status --instance-ids YOUR_INSTANCE_ID

# Check security group allows your IP
terraform output security_group_id
```

### Issue: Setup not completing

```bash
# Check user data logs for errors
ssh -i ~/.ssh/your-key.pem ec2-user@YOUR_IP "sudo cat /var/log/user-data.log | grep -i error"

# Manual setup (if needed)
ssh -i ~/.ssh/your-key.pem ec2-user@YOUR_IP
sudo dnf install -y python3.12 git
# ... continue manual setup
```

### Issue: "No space left on device"

```bash
# Check disk usage
df -h

# If full, increase root_volume_size in terraform.tfvars
# Then recreate instance:
terraform destroy -auto-approve
terraform apply -auto-approve
```

## Limitations & Workarounds

### 1. Can't Create IAM Roles
**Limitation**: No IAM::CreateRole permission
**Workaround**: Removed IAM resources from configuration
**Impact**: CloudWatch Agent and SSM won't work
**Alternative**: Use local logs and SSH access

### 2. Can't Use Systems Manager
**Limitation**: No SSM Session Manager
**Workaround**: Use traditional SSH access
**Impact**: None - SSH works fine
**Alternative**: Keep using SSH key-based authentication

### 3. Can't Stream Logs to CloudWatch
**Limitation**: CloudWatch Agent needs IAM permissions
**Workaround**: View logs directly on instance via SSH
**Impact**: No centralized logging
**Alternative**: Use `sudo cat /var/log/user-data.log`

### 4. Limited CloudWatch Features
**Limitation**: Can't use custom CloudWatch metrics
**Workaround**: Use AWS Console for basic metrics
**Impact**: No advanced monitoring
**Alternative**: Monitor resources via `top`, `htop`, `df -h`

## What Still Works

✅ **Full Application Functionality**
- Meta Ad Library API calls
- Data collection
- Database operations
- All Python code

✅ **Basic AWS Features**
- EC2 instance creation
- Security groups
- EBS volumes
- Elastic IPs (optional)
- Basic CloudWatch metrics

✅ **Network Access**
- SSH access
- Outbound HTTPS (for API calls)
- Package downloads
- Git operations

## Cost Considerations

With restricted accounts (AWS Academy), you typically have:
- **$100 credit** (or similar)
- **Limited time** (semester/course duration)
- **No charges to personal credit card**

### Estimated Costs
- **This test**: < $0.50 (few hours)
- **Full day**: ~$0.25
- **One week**: ~$1.75

**Note**: AWS Academy credits cover these costs.

## Cleanup

```bash
# Destroy everything
cd aws_feasibility/terraform
terraform destroy -auto-approve

# Verify deletion
aws ec2 describe-instances --filters "Name=tag:Project,Values=MetaAds"
```

## Additional Resources

### AWS Academy Resources
- [AWS Academy Documentation](https://awsacademy.instructure.com)
- [AWS Free Tier](https://aws.amazon.com/free/)
- [EC2 Instance Types](https://aws.amazon.com/ec2/instance-types/)

### MetaAds Documentation
- [Main README](../../README.md)
- [FEASIBILITY_PLAN.md](FEASIBILITY_PLAN.md)
- [QUICKSTART.md](QUICKSTART.md)

### Terraform Documentation
- [AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [EC2 Resources](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/instance)

## FAQ

**Q: Why can't I create IAM roles?**
A: AWS Academy accounts have restricted permissions to prevent misuse and control costs.

**Q: Will my application still work?**
A: Yes! All MetaAds functionality works. Only AWS-specific features like CloudWatch Agent are affected.

**Q: Can I deploy to production like this?**
A: No - this is for testing only. Production deployments should use proper IAM roles.

**Q: How do I get more permissions?**
A: Contact your AWS Academy instructor or use a personal AWS account.

**Q: Is this secure?**
A: Yes - the simplified config is still secure. We use encrypted volumes, security groups, and SSH keys.

---

**Need Help?**

1. Check [QUICKSTART.md](QUICKSTART.md) troubleshooting section
2. Review AWS Console for error messages
3. Check instance logs: `sudo cat /var/log/user-data.log`
4. Ask your AWS Academy instructor

---

**Document Version**: 1.0
**Date**: 2026-02-21
**For**: AWS Academy / Restricted Accounts
