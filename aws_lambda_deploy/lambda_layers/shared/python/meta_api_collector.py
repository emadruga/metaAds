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


class MetaAdLibraryAPI:
    """
    Client for Meta Ad Library API
    """

    def __init__(self, access_token: str = None):
        self.access_token = access_token or ""
        self.base_url = "https://graph.facebook.com/v24.0"
        self.rate_limiter = RateLimiter(200)

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
        max_retries = 3
        retry_delay = 2  # Start with 2 seconds
        requests_made = 0  # Count actual HTTP requests for rate-limit tracking

        while len(all_ads) < limit:
            # Rate limiting
            self.rate_limiter.wait_if_needed()

            for attempt in range(max_retries):
                try:
                    response = requests.get(url, params=params, timeout=30)
                    requests_made += 1
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

                    # Success - break retry loop
                    break

                except requests.exceptions.HTTPError as e:
                    # Check if it's a 500 error that we should retry
                    if e.response is not None and e.response.status_code == 500:
                        error_body = e.response.text[:500] if e.response.text else 'No error body'

                        if attempt < max_retries - 1:
                            # Retry with exponential backoff
                            wait_time = retry_delay * (2 ** attempt)
                            print(f"Meta API 500 error (attempt {attempt + 1}/{max_retries}). Retrying in {wait_time}s... | Body: {error_body}")
                            time.sleep(wait_time)
                            continue
                        else:
                            # Final attempt failed - raise user-friendly error
                            print(f"Meta API 500 error after {max_retries} attempts | Body: {error_body}")
                            raise Exception("Meta Ad Library is temporarily unavailable. Please try again in a few minutes.")
                    elif e.response is not None and e.response.status_code == 400:
                        # Check for rate limit error code 613
                        try:
                            body = e.response.json()
                            code = body.get("error", {}).get("code")
                            if code == 613:
                                raise Exception("Meta API rate limit exceeded. Too many requests this hour. Try again later.")
                        except (ValueError, AttributeError):
                            pass
                        print(f"Request error: Status 400 | Body: {e.response.text[:500]}")
                        raise Exception("Meta API error: 400")
                    else:
                        # Non-500 error - don't retry, just log and raise
                        if hasattr(e, 'response') and e.response is not None:
                            print(f"Request error: Status {e.response.status_code} | Body: {e.response.text[:500]}")
                        raise Exception(f"Meta API error: {e.response.status_code if e.response else 'Unknown'}")

                except requests.exceptions.RequestException as e:
                    # Network error or timeout - log and raise user-friendly error
                    print(f"Network error: {type(e).__name__} - {str(e)[:200]}")
                    raise Exception("Network error connecting to Meta Ad Library. Please check your connection and try again.")

        return all_ads[:limit], requests_made

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
        max_retries = 3
        retry_delay = 2

        while len(all_ads) < limit:
            self.rate_limiter.wait_if_needed()

            for attempt in range(max_retries):
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

                    # Success - break retry loop
                    break

                except requests.exceptions.HTTPError as e:
                    if e.response is not None and e.response.status_code == 500:
                        error_body = e.response.text[:500] if e.response.text else 'No error body'

                        if attempt < max_retries - 1:
                            wait_time = retry_delay * (2 ** attempt)
                            print(f"Meta API 500 error (attempt {attempt + 1}/{max_retries}). Retrying in {wait_time}s... | Body: {error_body}")
                            time.sleep(wait_time)
                            continue
                        else:
                            print(f"Meta API 500 error after {max_retries} attempts | Body: {error_body}")
                            raise Exception("Meta Ad Library is temporarily unavailable. Please try again in a few minutes.")
                    else:
                        if hasattr(e, 'response') and e.response is not None:
                            print(f"Request error: Status {e.response.status_code} | Body: {e.response.text[:500]}")
                        raise Exception(f"Meta API error: {e.response.status_code if e.response else 'Unknown'}")

                except requests.exceptions.RequestException as e:
                    print(f"Network error: {type(e).__name__} - {str(e)[:200]}")
                    raise Exception("Network error connecting to Meta Ad Library. Please check your connection and try again.")

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
