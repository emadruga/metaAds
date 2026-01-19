#!/usr/bin/env python
"""
Diagnostic script to determine if you have Ad Library API access
"""
import requests
from src.config import Config

def diagnose_ad_library_access():
    print("=" * 70)
    print("AD LIBRARY API ACCESS DIAGNOSTIC")
    print("=" * 70)

    # Test 1: Verify token
    print("\n[1/5] Verifying access token...")
    url = f"{Config.FB_BASE_URL}/me"
    params = {'access_token': Config.FB_ACCESS_TOKEN, 'fields': 'id,name'}

    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"    ✓ Token valid for user: {data.get('name', 'Unknown')}")
        else:
            print(f"    ✗ Token invalid: {response.text}")
            return
    except Exception as e:
        print(f"    ✗ Error: {e}")
        return

    # Test 2: Check token scopes
    print("\n[2/5] Checking token permissions...")
    url = f"{Config.FB_BASE_URL}/debug_token"
    params = {
        'input_token': Config.FB_ACCESS_TOKEN,
        'access_token': Config.FB_ACCESS_TOKEN
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json().get('data', {})
            scopes = data.get('scopes', [])
            print(f"    Token scopes: {', '.join(scopes)}")

            required_scopes = ['ads_read', 'pages_read_engagement']
            has_all = all(scope in scopes for scope in required_scopes)

            if has_all:
                print(f"    ✓ Has required scopes: {required_scopes}")
            else:
                print(f"    ⚠ Missing scopes. You have: {scopes}")
                print(f"       Required: {required_scopes}")
    except Exception as e:
        print(f"    ✗ Error: {e}")

    # Test 3: Test different ads_archive variations
    print("\n[3/5] Testing ads_archive endpoint variations...")

    test_cases = [
        {
            'name': 'Minimal params (no platforms)',
            'params': {
                'access_token': Config.FB_ACCESS_TOKEN,
                'search_terms': 'facebook',
                'ad_reached_countries': 'US',
                'fields': 'id',
                'limit': 1
            }
        },
        {
            'name': 'With ad_active_status',
            'params': {
                'access_token': Config.FB_ACCESS_TOKEN,
                'search_terms': 'facebook',
                'ad_reached_countries': 'US',
                'ad_active_status': 'ACTIVE',
                'fields': 'id',
                'limit': 1
            }
        },
        {
            'name': 'With publisher_platforms',
            'params': {
                'access_token': Config.FB_ACCESS_TOKEN,
                'search_terms': 'facebook',
                'ad_reached_countries': 'US',
                'ad_active_status': 'ALL',
                'publisher_platforms': 'facebook',
                'fields': 'id',
                'limit': 1
            }
        }
    ]

    success_count = 0
    for i, test in enumerate(test_cases):
        url = f"{Config.FB_BASE_URL}/ads_archive"
        try:
            response = requests.get(url, params=test['params'], timeout=10)

            if response.status_code == 200:
                print(f"    ✓ Test {i+1}: {test['name']} - SUCCESS")
                success_count += 1
            else:
                error_data = response.json().get('error', {})
                error_code = error_data.get('code', 'N/A')
                error_msg = error_data.get('message', 'Unknown')
                error_subcode = error_data.get('error_subcode', 'N/A')

                print(f"    ✗ Test {i+1}: {test['name']}")
                print(f"       Status: {response.status_code}")
                print(f"       Error Code: {error_code}")
                print(f"       Error Subcode: {error_subcode}")
                print(f"       Message: {error_msg}")
        except Exception as e:
            print(f"    ✗ Test {i+1}: {test['name']} - Exception: {e}")

    # Test 4: Check app info
    print("\n[4/5] Checking app configuration...")
    url = f"{Config.FB_BASE_URL}/debug_token"
    params = {
        'input_token': Config.FB_ACCESS_TOKEN,
        'access_token': Config.FB_ACCESS_TOKEN
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json().get('data', {})
            app_id = data.get('app_id', 'N/A')
            print(f"    App ID: {app_id}")
            print(f"    App URL: https://developers.facebook.com/apps/{app_id}/")
    except:
        pass

    # Test 5: Diagnosis
    print("\n[5/5] DIAGNOSIS:")
    print("=" * 70)

    if success_count > 0:
        print("\n✓ Ad Library API is WORKING!")
        print("  You have access to the Ad Library API.")
    else:
        print("\n✗ Ad Library API access is NOT enabled")
        print("\nMost likely cause:")
        print("  • Your app has business verification")
        print("  • BUT Ad Library API access is not yet enabled")
        print("\nThis is a SEPARATE approval process!")

        print("\n" + "=" * 70)
        print("SOLUTION: Request Ad Library API Access")
        print("=" * 70)

        print("\nOption 1: Through your app dashboard")
        print("  1. Go to: https://developers.facebook.com/apps/")
        print("  2. Select your app: 'EWD Marketing API'")
        print("  3. Look for 'Ad Library API' in the sidebar or Products")
        print("  4. Click 'Request Access' or 'Get Started'")
        print("  5. Fill out the form explaining your use case")

        print("\nOption 2: Through the Ad Library API portal")
        print("  1. Go to: https://www.facebook.com/ads/library/api/")
        print("  2. Click 'Apply for access' or 'Get Started'")
        print("  3. Select 'Access to all ads' (not just political)")
        print("  4. Complete the application form")

        print("\nOption 3: Through Business Manager")
        print("  1. Go to: https://business.facebook.com/")
        print("  2. Click 'Business Settings'")
        print("  3. Look for 'Ad Library API' or 'Data Sources'")
        print("  4. Request access")

        print("\nWhat to include in your application:")
        print("  • Purpose: Competitive intelligence and market research")
        print("  • Use case: Analyzing advertising trends and strategies")
        print("  • Expected volume: ~200 API calls per day")
        print("  • Geographic focus: US, BR")

        print("\nExpected timeline:")
        print("  • Application review: 1-2 weeks")
        print("  • You'll receive email when approved")

        print("\nAfter approval:")
        print("  • Run this diagnostic script again")
        print("  • You should see ✓ for all tests")
        print("  • Then run: python example_usage.py 1")

    print("\n" + "=" * 70)

if __name__ == '__main__':
    diagnose_ad_library_access()
