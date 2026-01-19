# processors/ad_parser.py
import re
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd


class AdParser:
    """
    Parser para extrair insights estruturados de ads
    """

    CTA_PATTERNS = [
        'learn more', 'sign up', 'get started', 'try free',
        'download', 'shop now', 'book now', 'subscribe',
        'join now', 'apply now', 'contact us', 'see more'
    ]

    def parse_ad(self, ad_data: Dict) -> Dict:
        """
        Converte dados brutos da API em formato estruturado
        """

        parsed = {
            'ad_id': ad_data.get('id'),
            'page_name': ad_data.get('page_name'),
            'page_id': ad_data.get('page_id'),
            'start_date': self._parse_date(ad_data.get('ad_delivery_start_time')),
            'end_date': self._parse_date(ad_data.get('ad_delivery_stop_time')),
            'is_active': ad_data.get('ad_delivery_stop_time') is None,
            'platforms': ','.join(ad_data.get('platforms', [])),
            'snapshot_url': ad_data.get('ad_snapshot_url'),

            # Texto
            'body': self._extract_text(ad_data, 'ad_creative_bodies'),
            'headline': self._extract_text(ad_data, 'ad_creative_link_titles'),
            'description': self._extract_text(ad_data, 'ad_creative_link_descriptions'),
            'link_caption': self._extract_text(ad_data, 'ad_creative_link_captions'),

            # Campos derivados
            'full_text': None,
            'text_length': 0,
            'has_emoji': False,
            'has_hashtags': False,
            'hashtags': [],
            'mentions': [],
            'cta_detected': None,
            'days_active': None,
        }

        # Combinar todo o texto
        full_text = ' '.join(filter(None, [
            parsed['body'],
            parsed['headline'],
            parsed['description'],
            parsed['link_caption']
        ]))

        parsed['full_text'] = full_text
        parsed['text_length'] = len(full_text)

        # Análise de texto
        parsed['has_emoji'] = self._contains_emoji(full_text)
        parsed['hashtags'] = self._extract_hashtags(full_text)
        parsed['has_hashtags'] = len(parsed['hashtags']) > 0
        parsed['mentions'] = self._extract_mentions(full_text)
        parsed['cta_detected'] = self._detect_cta(full_text)

        # Calcular dias ativo
        if parsed['start_date']:
            end = parsed['end_date'] or datetime.now()
            delta = end - parsed['start_date']
            parsed['days_active'] = delta.days

        return parsed

    def _extract_text(self, ad_data: Dict, field: str) -> Optional[str]:
        """Extrair primeiro item de array de texto"""
        value = ad_data.get(field, [])
        if isinstance(value, list) and len(value) > 0:
            return value[0]
        return None

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Converter string ISO para datetime"""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except:
            return None

    def _contains_emoji(self, text: str) -> bool:
        """Detectar presença de emojis"""
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map
            "\U0001F1E0-\U0001F1FF"  # flags
            "]+",
            flags=re.UNICODE
        )
        return bool(emoji_pattern.search(text))

    def _extract_hashtags(self, text: str) -> List[str]:
        """Extrair hashtags"""
        return re.findall(r'#\w+', text)

    def _extract_mentions(self, text: str) -> List[str]:
        """Extrair mentions (@username)"""
        return re.findall(r'@\w+', text)

    def _detect_cta(self, text: str) -> Optional[str]:
        """Detectar CTA no texto"""
        text_lower = text.lower()
        for cta in self.CTA_PATTERNS:
            if cta in text_lower:
                return cta
        return None

    def parse_batch(self, ads: List[Dict]) -> pd.DataFrame:
        """
        Processar múltiplos ads e retornar DataFrame
        """
        parsed_ads = [self.parse_ad(ad) for ad in ads]
        return pd.DataFrame(parsed_ads)
