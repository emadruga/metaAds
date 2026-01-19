#!/usr/bin/env python
"""
Test alternative methods to access Meta Ad Library
"""
import requests
from src.config import Config

def test_alternatives():
    """Test different approaches to access ad data"""
    print("=" * 60)
    print("Testing Alternative API Approaches")
    print("=" * 60)

    # Approach 1: Try with ad_type parameter
    print("\n1. Testing with ad_type parameter...")
    url = f"{Config.FB_BASE_URL}/ads_archive"
    params = {
        'access_token': Config.FB_ACCESS_TOKEN,
        'search_terms': 'coffee',
        'ad_reached_countries': ['US'],
        'ad_type': 'POLITICAL_AND_ISSUE_ADS',  # Try political ads first
        'fields': 'id',
        'limit': 1
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"   Error: {e}")

    # Approach 2: Try ALL ad types
    print("\n2. Testing with ad_type=ALL...")
    params['ad_type'] = 'ALL'

    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"   Error: {e}")

    # Approach 3: Remove publisher_platforms
    print("\n3. Testing without publisher_platforms...")
    params = {
        'access_token': Config.FB_ACCESS_TOKEN,
        'search_terms': 'test',
        'ad_reached_countries': ['US'],
        'ad_active_status': 'ALL',
        'fields': 'id',
        'limit': 1
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"   Error: {e}")

    # Approach 4: Check if we need a Page Access Token instead
    print("\n4. Checking token type requirements...")
    print("   Current token type: User Access Token")
    print("   Note: Ad Library might require Page Access Token for some queries")

    # Approach 5: Test with minimal params
    print("\n5. Testing with absolute minimum params...")
    params = {
        'access_token': Config.FB_ACCESS_TOKEN,
        'search_terms': 'nike',
        'ad_reached_countries': 'US'
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ SUCCESS! Found {len(data.get('data', []))} ads")
            if data.get('data'):
                print(f"   Sample ad ID: {data['data'][0].get('id')}")
        else:
            print(f"   Response: {response.text[:300]}")
    except Exception as e:
        print(f"   Error: {e}")

    print("\n" + "=" * 60)
    print("DIAGNOSIS:")
    print("=" * 60)
    print("""
The ads_archive endpoint is returning 500 errors, which typically means:

1. API Endpoint Deprecated or Changed:
   - Meta frequently changes their API
   - The ads_archive endpoint might have new requirements
   - Check: https://developers.facebook.com/docs/graph-api/changelog/

2. App Configuration Issue:
   - Your app might not have "Ad Library API" access enabled
   - Go to: https://developers.facebook.com/apps/
   - Check app settings and enable "Ad Library API"

3. Access Restrictions:
   - Some ad data requires special permissions
   - Might need to verify your business or identity
   - Check: https://www.facebook.com/ads/library/api/

4. Temporary API Issues:
   - Meta APIs sometimes have temporary outages
   - Try again in a few minutes

RECOMMENDED ACTIONS:
1. Visit https://www.facebook.com/ads/library/ directly
2. Try searching for ads manually
3. Check if you can access the Web UI
4. If Web UI works but API doesn't, contact Meta support
""")

if __name__ == '__main__':
    test_alternatives()
