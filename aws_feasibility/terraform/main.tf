# ============================================================================
# MetaAds AWS Feasibility Test - Simplified (No IAM Requirements)
# ============================================================================
# Purpose: Deploy minimal EC2 infrastructure WITHOUT IAM role creation
# Use this version for restricted AWS permissions (Academy/Lab accounts)
# ============================================================================

terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# ============================================================================
# Provider Configuration
# ============================================================================

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "MetaAds"
      Environment = var.environment
      ManagedBy   = "Terraform"
      Purpose     = "Feasibility-Test"
      CreatedBy   = "MetaAds-Team"
    }
  }
}

# ============================================================================
# Data Sources
# ============================================================================

# Get latest Amazon Linux 2023 AMI
data "aws_ami" "amazon_linux_2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  filter {
    name   = "architecture"
    values = ["x86_64"]
  }
}

# Get current AWS region
data "aws_region" "current" {}

# Get default VPC (simplicity for feasibility test)
data "aws_vpc" "default" {
  default = true
}

# Get default subnets
data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# ============================================================================
# Security Group
# ============================================================================

resource "aws_security_group" "metaads_sg" {
  name        = "metaads-feasibility-sg"
  description = "Security group for MetaAds feasibility test - SSH access only"
  vpc_id      = data.aws_vpc.default.id

  # SSH access
  ingress {
    description = "SSH from allowed IPs"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.allowed_ssh_cidr
  }

  # Allow all outbound traffic (for API calls, package downloads)
  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "metaads-feasibility-sg"
  }
}

# ============================================================================
# EC2 Instance (WITHOUT IAM instance profile)
# ============================================================================

resource "aws_instance" "metaads" {
  ami           = data.aws_ami.amazon_linux_2023.id
  instance_type = var.instance_type
  key_name      = var.key_name

  # Networking
  subnet_id                   = element(data.aws_subnets.default.ids, 0)
  vpc_security_group_ids      = [aws_security_group.metaads_sg.id]
  associate_public_ip_address = true

  # NO IAM instance profile (removed due to restricted permissions)

  # Storage
  root_block_device {
    volume_type           = "gp3"
    volume_size           = var.root_volume_size
    delete_on_termination = true
    encrypted             = true

    tags = {
      Name = "metaads-feasibility-root-volume"
    }
  }

  # User data script (automated setup)
  user_data = templatefile("${path.module}/user_data.sh", {
    github_repo_url = var.github_repo_url
    github_branch   = var.github_branch
  })

  # Metadata options (security best practice)
  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required" # IMDSv2 required
    http_put_response_hop_limit = 1
  }

  tags = {
    Name = "metaads-feasibility-test"
  }
}

# ============================================================================
# Elastic IP (Optional)
# ============================================================================

resource "aws_eip" "metaads_eip" {
  count    = var.use_elastic_ip ? 1 : 0
  domain   = "vpc"
  instance = aws_instance.metaads.id

  tags = {
    Name = "metaads-feasibility-eip"
  }
}
