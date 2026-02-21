# ============================================================================
# MetaAds AWS Feasibility Test - Outputs (Simplified Version)
# ============================================================================

# ============================================================================
# EC2 Instance Information
# ============================================================================

output "instance_id" {
  description = "ID of the EC2 instance"
  value       = aws_instance.metaads.id
}

output "instance_public_ip" {
  description = "Public IP address of the EC2 instance"
  value       = var.use_elastic_ip ? aws_eip.metaads_eip[0].public_ip : aws_instance.metaads.public_ip
}

output "instance_private_ip" {
  description = "Private IP address of the EC2 instance"
  value       = aws_instance.metaads.private_ip
}

output "instance_state" {
  description = "Current state of the EC2 instance"
  value       = aws_instance.metaads.instance_state
}

output "instance_type" {
  description = "Instance type of the EC2 instance"
  value       = aws_instance.metaads.instance_type
}

output "availability_zone" {
  description = "Availability zone where the instance is running"
  value       = aws_instance.metaads.availability_zone
}

# ============================================================================
# Connection Information
# ============================================================================

output "ssh_connection_command" {
  description = "SSH command to connect to the instance"
  value       = "ssh -i ~/.ssh/${var.key_name}.pem ec2-user@${var.use_elastic_ip ? aws_eip.metaads_eip[0].public_ip : aws_instance.metaads.public_ip}"
}

output "scp_env_file_command" {
  description = "SCP command to copy .env file to the instance"
  value       = "scp -i ~/.ssh/${var.key_name}.pem .env ec2-user@${var.use_elastic_ip ? aws_eip.metaads_eip[0].public_ip : aws_instance.metaads.public_ip}:~/metaAds/"
}

# ============================================================================
# Network Information
# ============================================================================

output "security_group_id" {
  description = "ID of the security group"
  value       = aws_security_group.metaads_sg.id
}

output "vpc_id" {
  description = "VPC ID where the instance is running"
  value       = data.aws_vpc.default.id
}

output "subnet_id" {
  description = "Subnet ID where the instance is running"
  value       = aws_instance.metaads.subnet_id
}

# ============================================================================
# Resource Information
# ============================================================================

output "ami_id" {
  description = "AMI ID used for the instance"
  value       = aws_instance.metaads.ami
}

output "ami_name" {
  description = "Name of the AMI used"
  value       = data.aws_ami.amazon_linux_2023.name
}

output "root_volume_id" {
  description = "ID of the root EBS volume"
  value       = aws_instance.metaads.root_block_device[0].volume_id
}

# ============================================================================
# Cost Tracking
# ============================================================================

output "estimated_monthly_cost" {
  description = "Estimated monthly cost (USD) - rough estimate"
  value = format(
    "~$%s EC2 + ~$%.2f EBS = Total: ~$%.2f (FREE if using Free Tier)",
    var.instance_type == "t3.micro" ? "7.50" : "15.00",
    var.root_volume_size * 0.10,
    var.instance_type == "t3.micro" ? 7.50 + (var.root_volume_size * 0.10) : 15.00 + (var.root_volume_size * 0.10)
  )
}

# ============================================================================
# Quick Reference
# ============================================================================

output "quick_start_commands" {
  description = "Quick start commands for using the instance"
  value = <<-EOT
    ╔══════════════════════════════════════════════════════════════════════╗
    ║           MetaAds Feasibility Test - Quick Start Commands            ║
    ║                  (Simplified - No IAM Version)                       ║
    ╚══════════════════════════════════════════════════════════════════════╝

    📋 Instance Information:
    ├─ Instance ID: ${aws_instance.metaads.id}
    ├─ Public IP:   ${var.use_elastic_ip ? aws_eip.metaads_eip[0].public_ip : aws_instance.metaads.public_ip}
    └─ Region:      ${data.aws_region.current.name}

    🔑 Connect via SSH:
    ssh -i ~/.ssh/${var.key_name}.pem ec2-user@${var.use_elastic_ip ? aws_eip.metaads_eip[0].public_ip : aws_instance.metaads.public_ip}

    📤 Copy .env file:
    scp -i ~/.ssh/${var.key_name}.pem .env ec2-user@${var.use_elastic_ip ? aws_eip.metaads_eip[0].public_ip : aws_instance.metaads.public_ip}:~/metaAds/

    ✅ Verify setup completion:
    ssh -i ~/.ssh/${var.key_name}.pem ec2-user@${var.use_elastic_ip ? aws_eip.metaads_eip[0].public_ip : aws_instance.metaads.public_ip} "cat ~/setup_complete.txt"

    🚀 Start testing:
    cd ~/metaAds && source venv/bin/activate && python test_api.py

    📊 Monitor in AWS Console:
    https://console.aws.amazon.com/ec2/v2/home?region=${data.aws_region.current.name}#Instances:instanceId=${aws_instance.metaads.id}

    ⚠️  Note: IAM features disabled due to account restrictions
    ⚠️  System logs: sudo cat /var/log/user-data.log

    ╚══════════════════════════════════════════════════════════════════════╝
  EOT
}
