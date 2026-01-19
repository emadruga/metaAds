# How to Fix Ad Library API Access

## Problem

Error: `"Application does not have permission for this action"` (Error code: 10, subcode: 2332002)

This means your Facebook App doesn't have permission to access the Ad Library API.

## Solution: Enable Ad Library API Access

### Step 1: Access the Ad Library API Setup Page

1. Go to: **https://www.facebook.com/ads/library/api/**
2. Click **"Get Started"** or **"Request Access"**

### Step 2: Choose Your Access Type

You'll need to select what type of ads you want to access:

#### Option A: Political and Issue Ads (Easier to get approved)
- ✅ No business verification required initially
- ✅ Faster approval
- ❌ Limited to political/issue ads only

#### Option B: All Ads (Recommended for this project)
- ✅ Access to all ad types (commercial, political, etc.)
- ❌ Requires business verification
- ❌ Takes longer to approve

**For this project, we need "All Ads" access.**

### Step 3: Complete Business Verification

To get "All Ads" access, you must verify your business:

1. **Provide Business Information:**
   - Legal business name
   - Business address
   - Business website
   - Tax ID (EIN, CPF/CNPJ, etc.)

2. **Upload Documentation:**
   - Business license or registration
   - Tax documents
   - Utility bill showing business address
   - Or: Use your personal information if no business

3. **Confirm Your Identity:**
   - Upload government-issued ID
   - Selfie verification
   - Phone number verification

### Step 4: Link Your App to Ad Library API

After verification is approved:

1. Go to https://developers.facebook.com/apps/
2. Select your app (App ID: 25766891366325694)
3. In the left sidebar, find **"Ad Library API"**
4. Click **"Set Up"** or **"Enable"**
5. Accept terms and conditions
6. Your app should now have access

### Step 5: Verify Access

Run this test:

```bash
python test_api.py
```

You should see success in test #3 (ads_archive endpoint).

## Alternative: Use Personal Access (Temporary)

If you just want to test quickly without business verification:

### Option 1: Use Meta's Ad Library Search Tool (No API)

Instead of API, use web scraping on:
- https://www.facebook.com/ads/library/

This works immediately but:
- ❌ Slower than API
- ❌ Rate limits
- ❌ Requires browser automation (Playwright/Selenium)

### Option 2: Request Limited Access

Some developers get temporary access for research:

1. Go to: https://www.facebook.com/ads/library/api/
2. Select **"Research"** as purpose
3. Provide:
   - Research description
   - Academic affiliation (if any)
   - Expected usage volume
4. Wait for approval (can take days/weeks)

## What This Means for Your Project

### Current Status:
- ✅ Your access token is valid
- ✅ Your app is configured correctly
- ❌ **Ad Library API access is NOT enabled**

### You Need To:

1. **Complete business verification** (1-2 weeks process)
2. **Enable Ad Library API** for your app
3. **Wait for approval** from Meta

### While Waiting:

You can:
1. ✅ Continue developing the code (it's all ready)
2. ✅ Test with mock data
3. ✅ Setup the database structure
4. ✅ Build the analysis pipeline
5. ❌ Cannot collect real ad data yet

## Timeline

- **Business Verification:** 1-14 days
- **API Access Approval:** 1-7 days after verification
- **Total:** ~2-3 weeks typically

## Need It Faster?

### Workaround 1: Web Scraping

Use Playwright to scrape the Ad Library website:

```python
from playwright.sync_api import sync_playwright

# This works without API access!
# See examples in web scraping tutorials
```

### Workaround 2: Use Existing Dataset

Download historical ad data from:
- https://www.facebook.com/ads/library/report/
- Kaggle datasets
- Academic research datasets

### Workaround 3: Partner with Verified Developer

If you know someone who already has Ad Library API access:
- Use their app/token temporarily
- They must add you as a developer to their app

## Quick Check: Do You Have Access?

Run this command to check your current status:

```bash
python -c "
import requests
from src.config import Config

url = f'{Config.FB_BASE_URL}/ads_archive'
params = {
    'access_token': Config.FB_ACCESS_TOKEN,
    'search_terms': 'test',
    'ad_reached_countries': 'US'
}

response = requests.get(url, params=params)
if response.status_code == 200:
    print('✅ YOU HAVE ACCESS!')
elif '2332002' in response.text:
    print('❌ NO ACCESS - Need to enable Ad Library API')
    print('   Go to: https://www.facebook.com/ads/library/api/')
else:
    print(f'⚠️  Other error: {response.status_code}')
    print(response.text[:200])
"
```

## Resources

- **Ad Library API Docs:** https://developers.facebook.com/docs/ad-library-api/
- **Get Started Guide:** https://www.facebook.com/business/help/2405092116183307
- **Business Verification:** https://www.facebook.com/business/help/2058515294227817
- **API Access Request:** https://www.facebook.com/ads/library/api/

## Support

If you're stuck:
1. Check Meta Business Help Center
2. Post in Facebook Developer Community
3. Contact Meta Support (if you have business manager)

---

**TL;DR:** Your app needs Ad Library API access. Go to https://www.facebook.com/ads/library/api/ and complete the verification process. This will take 1-3 weeks.
