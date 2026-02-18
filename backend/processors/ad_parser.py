"""
Ad Parser - Extract structured insights from raw ad data.

Converts raw API responses into structured format for storage and analysis.
"""
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional
import pandas as pd


class AdParser:
    """
    Parser for extracting structured insights from ads.
    """

    CTA_PATTERNS = [
        'learn more', 'sign up', 'get started', 'try free',
        'download', 'shop now', 'book now', 'subscribe',
        'join now', 'apply now', 'contact us', 'see more'
    ]

    def parse_ad(self, ad_data: Dict) -> Dict:
        """
        Convert raw API data to structured format.

        Args:
            ad_data: Raw ad data from Meta API

        Returns:
            Dictionary with parsed and enriched ad data
        """

        # Get platforms - try both fields, prefer publisher_platforms
        platforms = ad_data.get('publisher_platforms') or ad_data.get('platforms', [])
        if not platforms:
            # If still empty, log warning and use empty list
            print(f"[PARSER WARNING] No platforms found for ad {ad_data.get('id')}")

        parsed = {
            'ad_id': ad_data.get('id'),
            'page_name': ad_data.get('page_name'),
            'page_id': ad_data.get('page_id'),
            'start_date': self._parse_date_to_iso(ad_data.get('ad_delivery_start_time')),
            'end_date': self._parse_date_to_iso(ad_data.get('ad_delivery_stop_time')),
            'is_active': ad_data.get('ad_delivery_stop_time') is None,
            'platforms': platforms if isinstance(platforms, list) else [platforms] if platforms else [],
            'snapshot_url': ad_data.get('ad_snapshot_url'),

            # Text fields
            'body': self._extract_text(ad_data, 'ad_creative_bodies'),
            'headline': self._extract_text(ad_data, 'ad_creative_link_titles'),
            'description': self._extract_text(ad_data, 'ad_creative_link_descriptions'),
            'link_caption': self._extract_text(ad_data, 'ad_creative_link_captions'),

            # Derived fields
            'full_text': None,
            'text_length': 0,
            'has_emoji': False,
            'has_hashtags': False,
            'hashtags': [],
            'mentions': [],
            'cta_detected': None,
            'days_active': 0,
        }

        # Combine all text (including page_name for search)
        full_text = ' '.join(filter(None, [
            parsed['page_name'],
            parsed['body'],
            parsed['headline'],
            parsed['description'],
            parsed['link_caption']
        ]))

        parsed['full_text'] = full_text
        parsed['text_length'] = len(full_text)

        # Text analysis
        parsed['has_emoji'] = self._contains_emoji(full_text)
        parsed['hashtags'] = self._extract_hashtags(full_text)
        parsed['has_hashtags'] = len(parsed['hashtags']) > 0
        parsed['mentions'] = self._extract_mentions(full_text)
        parsed['cta_detected'] = self._detect_cta(full_text)

        # Calculate days active
        start = self._parse_date(ad_data.get('ad_delivery_start_time'))
        if start:
            end = self._parse_date(ad_data.get('ad_delivery_stop_time'))
            if not end:
                # If no end date, ad is still active - use current time (timezone-aware)
                end = datetime.now(timezone.utc)
            # Ensure both datetimes are timezone-aware for subtraction
            if start.tzinfo is None:
                start = start.replace(tzinfo=timezone.utc)
            if end.tzinfo is None:
                end = end.replace(tzinfo=timezone.utc)
            delta = end - start
            parsed['days_active'] = max(0, delta.days)

        return parsed

    def _extract_text(self, ad_data: Dict, field: str) -> Optional[str]:
        """Extract first item from text array."""
        value = ad_data.get(field, [])
        if isinstance(value, list) and len(value) > 0:
            return value[0]
        return None

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Convert ISO string to timezone-aware datetime."""
        if not date_str:
            return None
        try:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            # Ensure timezone-aware
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            return None

    def _parse_date_to_iso(self, date_str: Optional[str]) -> Optional[str]:
        """Convert date string to ISO8601 format."""
        if not date_str:
            return None
        try:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%dT%H:%M:%SZ')
        except Exception:
            return None

    def _contains_emoji(self, text: str) -> bool:
        """Detect presence of emojis."""
        if not text:
            return False
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
        """Extract hashtags from text."""
        if not text:
            return []
        return re.findall(r'#\w+', text)

    def _extract_mentions(self, text: str) -> List[str]:
        """Extract mentions (@username) from text."""
        if not text:
            return []
        return re.findall(r'@\w+', text)

    def _detect_cta(self, text: str) -> Optional[str]:
        """Detect CTA in text."""
        if not text:
            return None
        text_lower = text.lower()
        for cta in self.CTA_PATTERNS:
            if cta in text_lower:
                return cta
        return None

    def parse_batch(self, ads: List[Dict]) -> pd.DataFrame:
        """
        Process multiple ads and return DataFrame.

        Args:
            ads: List of raw ad data

        Returns:
            DataFrame with parsed ads
        """
        parsed_ads = [self.parse_ad(ad) for ad in ads]
        return pd.DataFrame(parsed_ads)
