# ============================================================================
# MetaAds AWS Feasibility Test - Variables
# ============================================================================

# ============================================================================
# AWS Configuration
# ============================================================================

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"

  validation {
    condition     = can(regex("^[a-z]{2}-[a-z]+-[0-9]{1}$", var.aws_region))
    error_message = "AWS region must be valid format (e.g., us-east-1)."
  }
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "feasibility-test"

  validation {
    condition     = contains(["feasibility-test", "dev", "staging", "production"], var.environment)
    error_message = "Environment must be feasibility-test, dev, staging, or production."
  }
}

# ============================================================================
# EC2 Configuration
# ============================================================================

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"

  validation {
    condition     = can(regex("^t[2-4]\\.", var.instance_type))
    error_message = "Instance type must be a T-series instance (t2, t3, or t4)."
  }
}

variable "key_name" {
  description = "Name of the SSH key pair (must already exist in AWS)"
  type        = string

  validation {
    condition     = length(var.key_name) > 0
    error_message = "SSH key name is required."
  }
}

variable "root_volume_size" {
  description = "Size of the root EBS volume in GB"
  type        = number
  default     = 20

  validation {
    condition     = var.root_volume_size >= 8 && var.root_volume_size <= 100
    error_message = "Root volume size must be between 8 and 100 GB."
  }
}

# ============================================================================
# Network Configuration
# ============================================================================

variable "allowed_ssh_cidr" {
  description = "List of CIDR blocks allowed to SSH into the instance"
  type        = list(string)
  default     = ["0.0.0.0/0"]

  validation {
    condition = alltrue([
      for cidr in var.allowed_ssh_cidr : can(cidrhost(cidr, 0))
    ])
    error_message = "All elements must be valid CIDR blocks."
  }
}

variable "use_elastic_ip" {
  description = "Whether to allocate and associate an Elastic IP"
  type        = bool
  default     = false
}

# ============================================================================
# Application Configuration
# ============================================================================

variable "github_repo_url" {
  description = "GitHub repository URL to clone"
  type        = string
  default     = "https://github.com/yourusername/metaAds.git"

  validation {
    condition     = can(regex("^https://github\\.com/", var.github_repo_url))
    error_message = "GitHub URL must start with https://github.com/."
  }
}

variable "github_branch" {
  description = "Git branch to checkout"
  type        = string
  default     = "main"
}

# ============================================================================
# Monitoring Configuration
# ============================================================================

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 7

  validation {
    condition     = contains([1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180], var.log_retention_days)
    error_message = "Log retention must be one of: 1, 3, 5, 7, 14, 30, 60, 90, 120, 150, or 180 days."
  }
}

variable "enable_monitoring" {
  description = "Enable CloudWatch monitoring and alarms"
  type        = bool
  default     = true
}

# ============================================================================
# Tags
# ============================================================================

variable "additional_tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default     = {}
}
