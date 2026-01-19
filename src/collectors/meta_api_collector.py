# src/collectors/meta_api_collector.py
import requests
import time
from typing import List, Dict, Optional
from src.config import Config


class MetaAdLibraryAPI:
    """
    Cliente para Meta Ad Library API
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
        Buscar ads na Ad Library

        Args:
            search_terms: Palavras-chave para buscar
            countries: Lista de códigos de país (ISO 2-letter)
            ad_active_status: 'ACTIVE', 'INACTIVE', 'ALL'
            platforms: 'facebook', 'instagram', 'messenger', 'audience_network'
            fields: Campos a retornar
            limit: Máximo de ads a retornar

        Returns:
            Lista de dicionários com dados dos ads
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
                    params = {}  # Next URL já tem todos os params
                else:
                    break

            except requests.exceptions.RequestException as e:
                print(f"Erro na requisição: {e}")
                break

        return all_ads[:limit]

    def get_ads_by_page(
        self,
        page_id: str,
        fields: List[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Buscar todos os ads de uma página específica
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
                print(f"Erro: {e}")
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
    Controle de rate limiting para API
    """

    def __init__(self, max_requests_per_hour: int):
        self.max_requests = max_requests_per_hour
        self.requests = []

    def wait_if_needed(self):
        now = time.time()

        # Remover requests antigas (mais de 1h)
        self.requests = [r for r in self.requests if now - r < 3600]

        if len(self.requests) >= self.max_requests:
            # Calcular quanto tempo esperar
            oldest = self.requests[0]
            wait_time = 3600 - (now - oldest) + 1
            print(f"Rate limit atingido. Aguardando {wait_time:.0f}s...")
            time.sleep(wait_time)
            self.requests = []

        self.requests.append(now)


# Exemplo de uso
if __name__ == '__main__':
    api = MetaAdLibraryAPI()

    # Buscar ads sobre "video editing ai"
    ads = api.search_ads(
        search_terms='video editing ai',
        countries=['US', 'BR'],
        platforms=['instagram'],
        limit=50
    )

    print(f"Encontrados {len(ads)} ads")
    for ad in ads[:3]:
        print(f"\nPágina: {ad.get('page_name')}")
        print(f"Texto: {ad.get('ad_creative_bodies', [''])[0][:100]}...")
