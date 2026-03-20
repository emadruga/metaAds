# =============================================================================
# Competitors Scraper — Lambda Container Image
#
# Playwright + Chromium cannot fit inside a 250 MB ZIP Lambda.
# This image bundles them so the Lambda can run headless Chromium for
# scraping the Meta Ads Library when the Graph API returns insufficient data.
#
# Build & push:
#   bash aws_lambda_deploy/scripts/build_scraper_image.sh
# =============================================================================

FROM public.ecr.aws/lambda/python:3.12

# --------------------------------------------------------------------------
# System dependencies required by Chromium on Amazon Linux 2023
# playwright install-deps handles most of them; we pin the ones that may
# be missing from the base image.
# --------------------------------------------------------------------------
RUN dnf install -y \
    atk \
    cups-libs \
    gtk3 \
    libXcomposite \
    libXcursor \
    libXdamage \
    libXext \
    libXfixes \
    libXi \
    libXrandr \
    libXtst \
    libXScrnSaver \
    pango \
    alsa-lib \
    at-spi2-atk \
    nss \
    mesa-libgbm \
    && dnf clean all

# --------------------------------------------------------------------------
# Python dependencies
# --------------------------------------------------------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --------------------------------------------------------------------------
# Install Playwright Chromium browser
# PLAYWRIGHT_BROWSERS_PATH must be writable at runtime; /opt is safe in Lambda.
# --------------------------------------------------------------------------
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers
RUN playwright install chromium \
    && playwright install-deps chromium

# --------------------------------------------------------------------------
# Handler
# --------------------------------------------------------------------------
COPY handler.py ${LAMBDA_TASK_ROOT}/

CMD ["handler.handler"]
