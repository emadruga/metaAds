# MetaAds AWS Feasibility Test - Terraform Infrastructure

This directory contains Terraform configuration files to deploy a minimal AWS infrastructure for testing the MetaAds data collection system.

## 📁 Directory Structure

```
terraform/
├── main.tf                      # Main infrastructure configuration
├── variables.tf                 # Input variable definitions
├── outputs.tf                   # Output value definitions
├── user_data.sh                 # EC2 initialization script
├── terraform.tfvars.example     # Example variable values
├── .gitignore                   # Git ignore rules
└── README.md                    # This file
```

## 🚀 Quick Start

See the comprehensive [QUICKSTART.md](../docs/QUICKSTART.md) guide for detailed step-by-step instructions.

### Prerequisites

1. AWS CLI installed and configured
2. Terraform >= 1.0 installed
3. SSH key pair created in AWS
4. GitHub repository accessible

### Basic Usage

```bash
# 1. Configure variables
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values

# 2. Initialize Terraform
terraform init

# 3. Preview changes
terraform plan

# 4. Deploy infrastructure
terraform apply

# 5. Get connection details
terraform output quick_start_commands
```

## 📋 What Gets Created

- **EC2 Instance**: t3.micro (Free Tier eligible)
- **Security Group**: SSH access only
- **IAM Role**: For CloudWatch and SSM access
- **EBS Volume**: 20 GB encrypted root volume
- **CloudWatch Log Group**: For future logging
- **Optional Elastic IP**: Persistent public IP

## 💰 Cost Estimate

- **Free Tier**: $0/month (first 12 months)
- **Regular**: ~$9.50/month (EC2 + EBS)
- **Test Duration**: <$1 (1-2 hours)

## 🔧 Configuration Variables

Key variables you need to configure in `terraform.tfvars`:

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `key_name` | ✅ Yes | SSH key pair name | `"metaads-test"` |
| `github_repo_url` | ✅ Yes | Your repo URL | `"https://github.com/user/metaAds.git"` |
| `aws_region` | No | AWS region | `"us-east-1"` (default) |
| `instance_type` | No | EC2 instance type | `"t3.micro"` (default) |
| `allowed_ssh_cidr` | No | SSH access IPs | `["0.0.0.0/0"]` (default) |

## 📤 Outputs

After successful deployment, Terraform provides:

- Instance public IP address
- SSH connection command
- SCP command for .env file
- AWS Console links
- Resource IDs

## 🔒 Security Notes

1. **SSH Access**: Restrict `allowed_ssh_cidr` to your IP
2. **Secrets**: Never commit `terraform.tfvars` or `.env` files
3. **Keys**: Store SSH keys securely, never in version control
4. **Tokens**: Meta API tokens go in `.env`, not user data

## 🧹 Cleanup

To remove all resources:

```bash
terraform destroy
```

To stop instance without destroying:

```bash
aws ec2 stop-instances --instance-ids $(terraform output -raw instance_id)
```

## 📚 Additional Resources

- [FEASIBILITY_PLAN.md](../docs/FEASIBILITY_PLAN.md) - Detailed plan
- [QUICKSTART.md](../docs/QUICKSTART.md) - Step-by-step guide
- [Terraform Documentation](https://www.terraform.io/docs)
- [AWS EC2 Documentation](https://docs.aws.amazon.com/ec2/)

## ⚠️ Troubleshooting

### Issue: "Invalid key pair"
**Solution**: Ensure key pair exists in your AWS region:
```bash
aws ec2 describe-key-pairs --region us-east-1
```

### Issue: "Insufficient permissions"
**Solution**: Ensure your AWS credentials have EC2/IAM/VPC permissions.

### Issue: "Instance not responding"
**Solution**: Check user data logs:
```bash
ssh -i ~/.ssh/key.pem ec2-user@<ip> "sudo cat /var/log/user-data.log"
```

## 📞 Support

For issues or questions:
1. Check [QUICKSTART.md](../docs/QUICKSTART.md) troubleshooting section
2. Review Terraform plan output
3. Check AWS Console for resource status
4. Review CloudWatch logs

## 🎯 Next Steps

After successful deployment:

1. Copy `.env` file to instance
2. Run connectivity tests
3. Collect sample data
4. Document results
5. Make go/no-go decision

---

**Version**: 1.0
**Last Updated**: 2026-02-21
**Maintainer**: MetaAds Team
