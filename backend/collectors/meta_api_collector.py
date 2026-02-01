"""
Meta Ad Library API Collector

Client for the Meta Ad Library API that handles:
- Search by keywords
- Search by page ID
- Pagination
- Rate limiting
"""
import requests
import time
from typing import List, Dict, Optional
from app.config import Config


class MetaAdLibraryAPI:
    """
    Client for Meta Ad Library API
    """

    def __init__(self, access_token: str = None):
        self.access_token = access_token or Config.FB_ACCESS_TOKEN
        self.base_url = Config.FB_BASE_URL
        self.rate_limiter = RateLimiter(Config.API_RATE_LIMIT)

    def search_ads(
        self,
        search_terms: str,
        countries: List[str] = ['US'],
        ad_active_status: str = 'ALL',
        ad_reached_countries: List[str] = None,
        platforms: List[str] = ['instagram'],
        fields: List[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Search ads in the Ad Library.

        Args:
            search_terms: Keywords to search
            countries: List of country codes (ISO 2-letter)
            ad_active_status: 'ACTIVE', 'INACTIVE', 'ALL'
            platforms: 'facebook', 'instagram', 'messenger', 'audience_network'
            fields: Fields to return
            limit: Maximum ads to return

        Returns:
            List of dictionaries with ad data
        """

        if fields is None:
            fields = [
                'id',
                'ad_creative_bodies',
                'ad_creative_link_captions',
                'ad_creative_link_titles',
                'ad_creative_link_descriptions',
                'ad_delivery_start_time',
                'ad_delivery_stop_time',
                'ad_snapshot_url',
                'page_name',
                'page_id',
                'platforms',
                'publisher_platforms'
            ]

        params = {
            'access_token': self.access_token,
            'search_terms': search_terms,
            'ad_reached_countries': ','.join(countries),
            'ad_active_status': ad_active_status,
            'fields': ','.join(fields),
            'limit': min(limit, 100)  # API max is 100 per page
        }

        if platforms:
            params['publisher_platforms'] = ','.join(platforms)

        all_ads = []
        url = f"{self.base_url}/ads_archive"

        while len(all_ads) < limit:
            # Rate limiting
            self.rate_limiter.wait_if_needed()

            try:
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()

                ads = data.get('data', [])
                all_ads.extend(ads)

                # Pagination
                if 'paging' in data and 'next' in data['paging']:
                    url = data['paging']['next']
                    params = {}  # Next URL already has all params
                else:
                    break

            except requests.exceptions.RequestException as e:
                print(f"Request error: {e}")
                break

        return all_ads[:limit]

    def get_ads_by_page(
        self,
        page_id: str,
        fields: List[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Get all ads from a specific page.
        """

        if fields is None:
            fields = self._get_default_fields()

        params = {
            'access_token': self.access_token,
            'fields': ','.join(fields),
            'limit': min(limit, 100)
        }

        url = f"{self.base_url}/{page_id}/ads_archive"

        all_ads = []

        while len(all_ads) < limit:
            self.rate_limiter.wait_if_needed()

            try:
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()

                ads = data.get('data', [])
                all_ads.extend(ads)

                if 'paging' in data and 'next' in data['paging']:
                    url = data['paging']['next']
                    params = {}
                else:
                    break

            except requests.exceptions.RequestException as e:
                print(f"Error: {e}")
                break

        return all_ads[:limit]

    def _get_default_fields(self) -> List[str]:
        return [
            'id', 'ad_creative_bodies', 'ad_creative_link_captions',
            'ad_creative_link_titles', 'ad_delivery_start_time',
            'ad_snapshot_url', 'page_name', 'platforms'
        ]


class RateLimiter:
    """
    Rate limiting control for API calls.
    """

    def __init__(self, max_requests_per_hour: int):
        self.max_requests = max_requests_per_hour
        self.requests = []

    def wait_if_needed(self):
        now = time.time()

        # Remove old requests (more than 1h)
        self.requests = [r for r in self.requests if now - r < 3600]

        if len(self.requests) >= self.max_requests:
            # Calculate wait time
            oldest = self.requests[0]
            wait_time = 3600 - (now - oldest) + 1
            print(f"Rate limit reached. Waiting {wait_time:.0f}s...")
            time.sleep(wait_time)
            self.requests = []

        self.requests.append(now)


# Example usage
if __name__ == '__main__':
    api = MetaAdLibraryAPI()

    # Search ads for "video editing ai"
    ads = api.search_ads(
        search_terms='video editing ai',
        countries=['US', 'BR'],
        platforms=['instagram'],
        limit=50
    )

    print(f"Found {len(ads)} ads")
    for ad in ads[:3]:
        print(f"\nPage: {ad.get('page_name')}")
        print(f"Text: {ad.get('ad_creative_bodies', [''])[0][:100]}...")
