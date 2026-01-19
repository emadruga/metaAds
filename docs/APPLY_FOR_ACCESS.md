# How to Apply for Ad Library API Access

## Step 1: Go to the Ad Library API Portal

**Direct Link:** https://www.facebook.com/ads/library/api/

⚠️ **Important:** This is NOT the Graph API Explorer. It's a separate portal.

## Step 2: Choose Access Type

You'll see two options:

### Option A: Political and Issue Ads Only
- ✅ Easier approval
- ❌ Only political/social issue ads
- ❌ Won't work for commercial ads (your use case)

### Option B: All Ads (What You Need!)
- ✅ Access to ALL ad types
- ✅ Works for commercial ads analysis
- ❌ Requires verification process

**Click on "All Ads"** or **"Get Started"** under the All Ads section.

## Step 3: Complete the Application Form

You'll need to provide:

### Personal Information
- Full legal name
- Date of birth
- Government ID (upload)

### Business Information (if applicable)
- Business name
- Business address
- Tax ID (EIN, CNPJ, etc.)
- Business documents

### Use Case Description
Explain why you need access. Example:

```
I am developing a competitive intelligence tool to analyze
advertising strategies in the digital marketing space. This
tool will help businesses understand market trends and optimize
their advertising campaigns by studying publicly available ad
data from the Meta Ad Library.
```

### Expected Usage
- Number of API calls per day
- Types of ads you'll analyze
- Countries you'll focus on

## Step 4: Submit and Wait

After submitting:
- ✅ You'll receive a confirmation email
- ⏳ Review takes 1-14 days typically
- 📧 Meta will email you when approved (or if they need more info)

## Alternative: If You Can't Find the Form

If the link above doesn't show the application form:

### Try Method 1: Through Business Manager

1. Go to: https://business.facebook.com/
2. Click on **"Business Settings"**
3. Look for **"Data Sources"** or **"Ad Library API"** in the left menu
4. Click **"Request Access"**

### Try Method 2: Through Developer App Settings

1. Go to: https://developers.facebook.com/apps/
2. Select your app: **EWD Marketing API** (App ID: 25766891366325694)
3. Look for **"Add Product"** or **"Products"**
4. Find **"Ad Library API"** in the list
5. Click **"Set Up"** or **"Request Access"**

### Try Method 3: Direct Support

If you still can't find it:

1. Go to: https://developers.facebook.com/support/bugs/
2. Create a bug report asking: "How do I request Ad Library API access for App ID 25766891366325694?"

## What If the Page Says "Not Available"?

Some reasons and solutions:

### Reason 1: Location Restrictions
- Ad Library API might not be available in all countries yet
- Check if your region is supported

### Reason 2: Account Type Issues
- You might need a Business Manager account
- Create one at: https://business.facebook.com/

### Reason 3: App Status
- Your app must be in "Live" mode (not Development)
- Check app settings at: https://developers.facebook.com/apps/

## Quick Check: Current Status

Run this in your terminal to see your current permissions:

```bash
python test_api.py
```

Look for the error message:
- **Error 2332002** = Need Ad Library API access ← This is what you have
- **Error 200** = You have access! ✅

## Timeline

What to expect:

| Stage | Duration |
|-------|----------|
| Form submission | 5 minutes |
| Initial review | 1-3 days |
| Document verification | 3-7 days |
| Final approval | 1-3 days |
| **Total** | **~1-2 weeks** |

## After Approval

Once approved:

1. ✅ You'll receive confirmation email
2. ✅ Your app will have Ad Library API enabled
3. ✅ Run `python test_api.py` - should show Status 200
4. ✅ Run `python example_usage.py 1` - should collect real ads!

## Troubleshooting

### "I can't find the application form"

**Try this:**
1. Open incognito/private browser window
2. Go to: https://www.facebook.com/ads/library/api/
3. Make sure you're logged into Facebook
4. The form should appear

### "The page says I need business verification"

**This is normal!**
- Click "Start Verification"
- Follow the business verification process
- Submit required documents
- Wait for approval

### "I don't have a business"

**You can still apply!**
- Use your personal information
- Explain it's for research/development
- Some developers get approved for personal projects

## Need Help?

**Meta Developer Community:**
https://developers.facebook.com/community/

**Search for:** "Ad Library API access request"

**Support:**
https://developers.facebook.com/support/

---

## Summary

1. **Go to:** https://www.facebook.com/ads/library/api/
2. **Click:** "Get Started" under "All Ads"
3. **Fill out:** Application form
4. **Submit:** Documents and wait for approval
5. **Test:** Run `python test_api.py` after approval

**Timeline:** 1-2 weeks typically

---

Last updated: 2026-01-18
