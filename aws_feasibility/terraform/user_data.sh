#!/bin/bash
# ============================================================================
# MetaAds AWS Feasibility Test - EC2 User Data Script
# ============================================================================
# Purpose: Automated setup of MetaAds application on EC2 instance
# Execution: Runs once at instance first boot
# Duration: ~5-10 minutes
# ============================================================================

# Don't exit on error - continue even if some steps fail
# set -e  # Disabled to handle package conflicts gracefully
set -o pipefail  # Catch errors in pipes

# ============================================================================
# Configuration
# ============================================================================
GITHUB_REPO="${github_repo_url}"
GITHUB_BRANCH="${github_branch}"
APP_DIR="/home/ec2-user/metaAds"
LOG_FILE="/var/log/user-data.log"
SETUP_MARKER="/home/ec2-user/setup_complete.txt"

# ============================================================================
# Logging Setup
# ============================================================================
exec > >(tee -a $LOG_FILE)
exec 2>&1

echo "============================================================================"
echo "MetaAds Feasibility Test - Instance Setup Starting"
echo "Timestamp: $(date)"
echo "============================================================================"

# ============================================================================
# System Update
# ============================================================================
echo "[Step 1/10] Updating system packages..."
# Use --skip-broken to avoid curl package conflicts
dnf update -y --skip-broken || echo "Warning: Some packages skipped due to conflicts"

# ============================================================================
# Install System Dependencies
# ============================================================================
echo "[Step 2/10] Installing system dependencies..."
# Install packages individually to avoid conflicts, skip problematic ones
dnf install -y --skip-broken \
    python3.12 \
    python3.12-pip \
    python3.12-devel \
    git \
    gcc \
    make \
    openssl-devel \
    bzip2-devel \
    libffi-devel \
    zlib-devel \
    wget \
    htop \
    vim

# curl is usually pre-installed, verify it exists
if ! command -v curl &> /dev/null; then
    echo "Warning: curl not found, attempting to install..."
    dnf install -y curl || echo "Could not install curl, but this is non-critical"
fi

# Verify critical packages are installed
echo "Verifying critical packages..."
CRITICAL_MISSING=0

if ! command -v python3.12 &> /dev/null; then
    echo "ERROR: Python 3.12 not installed!"
    CRITICAL_MISSING=1
fi

if ! command -v git &> /dev/null; then
    echo "ERROR: Git not installed!"
    CRITICAL_MISSING=1
fi

if [ $CRITICAL_MISSING -eq 1 ]; then
    echo "CRITICAL: Required packages missing. Attempting alternative installation..."
    # Try one more time with different approach
    dnf install -y python3.12 git || {
        echo "FATAL: Cannot install critical packages. Setup will fail."
        exit 1
    }
fi

echo "✓ All critical packages verified"

# Set Python 3.12 as default
alternatives --set python3 /usr/bin/python3.12 || {
    echo "Warning: Could not set Python 3.12 as default"
    # Create symlink as fallback
    ln -sf /usr/bin/python3.12 /usr/local/bin/python3 || true
}

# ============================================================================
# Create Application Directory
# ============================================================================
echo "[Step 3/10] Creating application directory..."
mkdir -p $APP_DIR
chown ec2-user:ec2-user $APP_DIR

# ============================================================================
# Clone Repository
# ============================================================================
echo "[Step 4/10] Cloning GitHub repository..."
su - ec2-user -c "
    cd ~
    if [ -d '$APP_DIR/.git' ]; then
        echo 'Repository already exists, pulling latest changes...'
        cd $APP_DIR
        git pull origin $GITHUB_BRANCH || echo 'Warning: Could not pull latest changes'
    else
        echo 'Cloning repository...'
        # Try up to 3 times with increasing delays
        for i in 1 2 3; do
            if git clone -b $GITHUB_BRANCH $GITHUB_REPO $APP_DIR; then
                echo 'Repository cloned successfully'
                break
            else
                echo \"Attempt \$i failed, retrying in \$((i*5)) seconds...\"
                sleep \$((i*5))
                if [ \$i -eq 3 ]; then
                    echo 'FATAL: Could not clone repository after 3 attempts'
                    exit 1
                fi
            fi
        done
    fi
"

# ============================================================================
# Create Virtual Environment
# ============================================================================
echo "[Step 5/10] Creating Python virtual environment..."
su - ec2-user -c "
    cd $APP_DIR
    python3.12 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip setuptools wheel
"

# ============================================================================
# Install Python Dependencies
# ============================================================================
echo "[Step 6/10] Installing Python dependencies..."
su - ec2-user -c "
    cd $APP_DIR
    source venv/bin/activate
    if [ -f requirements.txt ]; then
        echo 'Installing Python packages from requirements.txt...'
        # Install with retries and skip broken packages
        pip install -r requirements.txt --no-cache-dir || {
            echo 'Warning: Some packages failed to install, trying individually...'
            # Try installing critical packages individually
            pip install requests pandas sqlalchemy python-dotenv || {
                echo 'ERROR: Could not install critical Python packages'
                exit 1
            }
            echo 'Critical packages installed, continuing...'
        }
    else
        echo 'WARNING: requirements.txt not found, installing core packages...'
        pip install requests pandas sqlalchemy python-dotenv
    fi

    # Verify critical packages
    python -c 'import requests, pandas, sqlalchemy' && echo '✓ Core packages verified' || {
        echo 'ERROR: Core Python packages not available'
        exit 1
    }
"

# ============================================================================
# Install Playwright Browsers (if needed)
# ============================================================================
echo "[Step 7/10] Installing Playwright browsers..."
su - ec2-user -c "
    cd $APP_DIR
    source venv/bin/activate
    playwright install chromium || echo 'Playwright install skipped (not critical)'
"

# ============================================================================
# Create Directory Structure
# ============================================================================
echo "[Step 8/10] Creating application directory structure..."
su - ec2-user -c "
    cd $APP_DIR
    mkdir -p data logs reports
    chmod 755 data logs reports
"

# ============================================================================
# Copy Feasibility Test Script
# ============================================================================
echo "[Step 8.5/10] Copying feasibility test script..."
su - ec2-user -c "
    cd $APP_DIR
    if [ -f aws_feasibility/terraform/final_feasibility.py ]; then
        cp aws_feasibility/terraform/final_feasibility.py final_feasibility.py
        chmod +x final_feasibility.py
        echo '✓ Feasibility test script copied to ~/metaAds/final_feasibility.py'
    else
        echo 'WARNING: final_feasibility.py not found in repository'
    fi
"

# ============================================================================
# Set File Permissions
# ============================================================================
echo "[Step 9/10] Setting file permissions..."
chown -R ec2-user:ec2-user $APP_DIR
chmod -R 755 $APP_DIR

# Ensure .env will have correct permissions when copied
su - ec2-user -c "
    cd $APP_DIR
    touch .env
    chmod 600 .env
"

# ============================================================================
# Create Setup Completion Marker
# ============================================================================
echo "[Step 10/10] Creating setup completion marker..."
su - ec2-user -c "
    cat > $SETUP_MARKER <<EOF
╔══════════════════════════════════════════════════════════════════════╗
║           MetaAds Feasibility Test - Setup Complete                  ║
╚══════════════════════════════════════════════════════════════════════╝

✅ Setup completed successfully at: $(date)

📋 Installation Summary:
├─ Python: $(python3 --version)
├─ Git: $(git --version)
├─ Application Directory: $APP_DIR
├─ Virtual Environment: $APP_DIR/venv
└─ Log File: $LOG_FILE

🚀 Next Steps:

1. Copy your .env file with credentials:
   scp -i ~/.ssh/your-key.pem .env ec2-user@\$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):~/metaAds/

2. SSH into the instance:
   ssh -i ~/.ssh/your-key.pem ec2-user@\$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)

3. Activate virtual environment:
   cd ~/metaAds && source venv/bin/activate

4. Verify .env file:
   ls -la .env

5. Run API test:
   python test_api.py

6. Run comprehensive feasibility test:
   python final_feasibility.py

7. Run example usage (alternative):
   python example_usage.py

📚 Application Structure:
$APP_DIR/
├── src/                  # Source code
│   ├── collectors/       # API collectors
│   ├── processors/       # Data parsers
│   ├── storage/          # Database layer
│   └── analyzers/        # Analysis modules
├── data/                 # Database storage
├── logs/                 # Application logs
├── reports/              # Generated reports
├── venv/                 # Python virtual environment
├── requirements.txt      # Python dependencies
├── test_api.py          # API connectivity test
├── final_feasibility.py # Comprehensive feasibility test
└── example_usage.py     # Full pipeline test

🔍 Troubleshooting:

View setup log:
  sudo cat /var/log/user-data.log

Check system resources:
  htop  # or: top
  df -h
  free -m

View application logs:
  tail -f ~/metaAds/logs/*.log

╚══════════════════════════════════════════════════════════════════════╝
EOF
"

# ============================================================================
# Final System Checks
# ============================================================================
echo ""
echo "============================================================================"
echo "Running final system checks..."
echo "============================================================================"

echo "✓ Python version: $(python3 --version)"
echo "✓ Pip version: $(pip3 --version)"
echo "✓ Git version: $(git --version)"
echo "✓ Disk usage: $(df -h / | tail -1 | awk '{print $5 " used"}')"
echo "✓ Memory: $(free -h | grep Mem | awk '{print $3 "/" $2 " used"}')"

# ============================================================================
# Setup Complete
# ============================================================================
echo ""
echo "============================================================================"
echo "MetaAds Instance Setup Complete!"
echo "Completed at: $(date)"
echo "============================================================================"
echo ""

# Verify setup success
SETUP_SUCCESS=1

# Check Python
if ! python3 --version &> /dev/null; then
    echo "⚠ WARNING: Python not properly configured"
    SETUP_SUCCESS=0
else
    echo "✓ Python: $(python3 --version)"
fi

# Check Git
if ! git --version &> /dev/null; then
    echo "⚠ WARNING: Git not properly configured"
    SETUP_SUCCESS=0
else
    echo "✓ Git: $(git --version)"
fi

# Check application directory
if [ -d "$APP_DIR" ]; then
    echo "✓ Application directory: $APP_DIR"
else
    echo "⚠ WARNING: Application directory not found"
    SETUP_SUCCESS=0
fi

# Check virtual environment
if [ -d "$APP_DIR/venv" ]; then
    echo "✓ Virtual environment: $APP_DIR/venv"
else
    echo "⚠ WARNING: Virtual environment not created"
    SETUP_SUCCESS=0
fi

# Check feasibility script
if [ -f "$APP_DIR/final_feasibility.py" ]; then
    echo "✓ Feasibility test script: Ready"
else
    echo "⚠ WARNING: Feasibility test script not found (may need manual copy)"
fi

echo ""
echo "Setup marker created at: $SETUP_MARKER"
echo "Full log available at: $LOG_FILE"
echo ""

if [ $SETUP_SUCCESS -eq 1 ]; then
    echo "✅ Instance is ready for testing!"
    echo "============================================================================"
    exit 0
else
    echo "⚠️  Setup completed with warnings. Check log for details."
    echo "============================================================================"
    exit 0  # Don't fail completely, allow manual fixes
fi
