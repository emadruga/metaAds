#!/bin/bash
# ============================================================================
# MetaAds AWS Feasibility Test - Pre-Deployment Validation Script
# ============================================================================
# Purpose: Verify all prerequisites are met before running terraform apply
# Usage: ./validate_setup.sh
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0
WARNINGS=0

echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║           MetaAds Feasibility Test - Setup Validation               ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo ""

# ============================================================================
# Helper Functions
# ============================================================================

pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASSED++))
}

fail() {
    echo -e "${RED}✗${NC} $1"
    ((FAILED++))
}

warn() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((WARNINGS++))
}

info() {
    echo -e "  $1"
}

# ============================================================================
# Check 1: Required Tools
# ============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1. Checking Required Tools"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# AWS CLI
if command -v aws &> /dev/null; then
    AWS_VERSION=$(aws --version 2>&1 | cut -d' ' -f1)
    pass "AWS CLI installed ($AWS_VERSION)"
else
    fail "AWS CLI not installed"
    info "Install: brew install awscli  (macOS)"
    info "         https://aws.amazon.com/cli/  (other)"
fi

# Terraform
if command -v terraform &> /dev/null; then
    TF_VERSION=$(terraform version | head -n1)
    pass "Terraform installed ($TF_VERSION)"
else
    fail "Terraform not installed"
    info "Install: brew install terraform  (macOS)"
    info "         https://www.terraform.io/downloads  (other)"
fi

# Git
if command -v git &> /dev/null; then
    GIT_VERSION=$(git --version)
    pass "Git installed ($GIT_VERSION)"
else
    fail "Git not installed"
    info "Install: brew install git  (macOS)"
fi

echo ""

# ============================================================================
# Check 2: AWS Configuration
# ============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2. Checking AWS Configuration"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# AWS Credentials
if aws sts get-caller-identity &> /dev/null; then
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    USER_ARN=$(aws sts get-caller-identity --query Arn --output text)
    pass "AWS credentials configured"
    info "Account: $ACCOUNT_ID"
    info "User: $USER_ARN"
else
    fail "AWS credentials not configured"
    info "Run: aws configure"
fi

# AWS Region
AWS_REGION=$(aws configure get region || echo "not-set")
if [ "$AWS_REGION" != "not-set" ]; then
    pass "AWS region configured: $AWS_REGION"
else
    warn "AWS region not configured (will use us-east-1 default)"
    info "Run: aws configure set region us-east-1"
fi

echo ""

# ============================================================================
# Check 3: SSH Key Pair
# ============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3. Checking SSH Key Pairs"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if terraform.tfvars exists
if [ -f "terraform.tfvars" ]; then
    pass "terraform.tfvars file exists"

    # Extract key_name from terraform.tfvars
    KEY_NAME=$(grep -E '^key_name\s*=' terraform.tfvars | sed 's/.*=\s*"\(.*\)".*/\1/' || echo "")

    if [ -n "$KEY_NAME" ]; then
        info "Configured key: $KEY_NAME"

        # Check if key exists in AWS
        if aws ec2 describe-key-pairs --key-names "$KEY_NAME" --region "${AWS_REGION:-us-east-1}" &> /dev/null; then
            pass "SSH key pair '$KEY_NAME' exists in AWS"
        else
            fail "SSH key pair '$KEY_NAME' not found in AWS"
            info "Create: aws ec2 create-key-pair --key-name $KEY_NAME --query 'KeyMaterial' --output text > ~/.ssh/$KEY_NAME.pem"
            info "        chmod 400 ~/.ssh/$KEY_NAME.pem"
        fi

        # Check if local key file exists
        if [ -f "$HOME/.ssh/$KEY_NAME.pem" ]; then
            pass "Local SSH key file exists: ~/.ssh/$KEY_NAME.pem"

            # Check permissions
            PERMS=$(stat -f "%OLp" "$HOME/.ssh/$KEY_NAME.pem" 2>/dev/null || stat -c "%a" "$HOME/.ssh/$KEY_NAME.pem" 2>/dev/null)
            if [ "$PERMS" = "400" ] || [ "$PERMS" = "600" ]; then
                pass "SSH key permissions correct ($PERMS)"
            else
                warn "SSH key permissions should be 400 (currently: $PERMS)"
                info "Fix: chmod 400 ~/.ssh/$KEY_NAME.pem"
            fi
        else
            warn "Local SSH key file not found: ~/.ssh/$KEY_NAME.pem"
            info "If you just created the key, ensure it's saved to this location"
        fi
    else
        warn "key_name not configured in terraform.tfvars"
    fi
else
    fail "terraform.tfvars file not found"
    info "Create: cp terraform.tfvars.example terraform.tfvars"
    info "        vim terraform.tfvars"
fi

echo ""

# ============================================================================
# Check 4: Terraform Configuration
# ============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4. Checking Terraform Configuration"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if terraform files exist
REQUIRED_FILES=("main.tf" "variables.tf" "outputs.tf" "user_data.sh")
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        pass "$file exists"
    else
        fail "$file not found"
    fi
done

# Check if .terraform directory exists (initialized)
if [ -d ".terraform" ]; then
    pass "Terraform initialized (.terraform/ exists)"
else
    warn "Terraform not initialized"
    info "Run: terraform init"
fi

# Validate Terraform syntax (if initialized)
if [ -d ".terraform" ]; then
    if terraform validate &> /dev/null; then
        pass "Terraform configuration valid"
    else
        fail "Terraform configuration has errors"
        info "Run: terraform validate"
    fi
fi

echo ""

# ============================================================================
# Check 5: Application Prerequisites
# ============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5. Checking Application Prerequisites"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check for .env file in project root
if [ -f "../../.env" ]; then
    pass ".env file exists"

    # Check if it has Meta API token
    if grep -q "FB_ACCESS_TOKEN" "../../.env"; then
        pass ".env contains FB_ACCESS_TOKEN"
    else
        warn ".env missing FB_ACCESS_TOKEN"
        info "Add: FB_ACCESS_TOKEN=your_token_here"
    fi
else
    warn ".env file not found in project root"
    info "Create: cp ../../.env.example ../../.env"
    info "        vim ../../.env"
fi

# Check GitHub repo URL in terraform.tfvars
if [ -f "terraform.tfvars" ]; then
    REPO_URL=$(grep -E '^github_repo_url\s*=' terraform.tfvars | grep -o 'https://.*\.git' || echo "")
    if [ -n "$REPO_URL" ]; then
        if echo "$REPO_URL" | grep -q "yourusername"; then
            warn "GitHub repo URL still has placeholder 'yourusername'"
            info "Update: github_repo_url in terraform.tfvars"
        else
            pass "GitHub repo URL configured"
            info "Repo: $REPO_URL"
        fi
    fi
fi

echo ""

# ============================================================================
# Check 6: Network & Connectivity
# ============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "6. Checking Network & Connectivity"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check internet connectivity
if curl -s --max-time 5 https://www.google.com > /dev/null; then
    pass "Internet connectivity working"
else
    fail "No internet connectivity"
fi

# Check AWS connectivity
if curl -s --max-time 5 https://aws.amazon.com > /dev/null; then
    pass "AWS endpoints reachable"
else
    warn "AWS endpoints not reachable (may be network issue)"
fi

# Check Meta API connectivity
if curl -s --max-time 5 https://graph.facebook.com > /dev/null; then
    pass "Meta API endpoints reachable"
else
    warn "Meta API endpoints not reachable (may be network issue)"
fi

# Get public IP (for security group configuration)
PUBLIC_IP=$(curl -s --max-time 5 https://api.ipify.org || echo "unknown")
if [ "$PUBLIC_IP" != "unknown" ]; then
    pass "Public IP detected: $PUBLIC_IP"
    info "Use this in allowed_ssh_cidr: [\"$PUBLIC_IP/32\"]"
else
    warn "Could not detect public IP"
fi

echo ""

# ============================================================================
# Summary
# ============================================================================

echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║                         Validation Summary                           ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo ""
echo -e "  ${GREEN}Passed:${NC}   $PASSED"
echo -e "  ${YELLOW}Warnings:${NC} $WARNINGS"
echo -e "  ${RED}Failed:${NC}   $FAILED"
echo ""

if [ $FAILED -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed! You're ready to deploy.${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Review terraform.tfvars one more time"
    echo "  2. Run: terraform plan"
    echo "  3. Run: terraform apply"
    echo ""
elif [ $FAILED -eq 0 ]; then
    echo -e "${YELLOW}⚠ Some warnings found. Review and fix if needed.${NC}"
    echo ""
    echo "You can proceed with deployment, but review warnings above."
    echo ""
else
    echo -e "${RED}✗ Some checks failed. Please fix the issues above before deploying.${NC}"
    echo ""
    echo "Fix the failed checks and run this script again:"
    echo "  ./validate_setup.sh"
    echo ""
    exit 1
fi

echo "╚══════════════════════════════════════════════════════════════════════╝"
