# alerts.py
import requests
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class AlertSystem:
    """
    Sistema de alertas via Slack, email, etc
    """

    def __init__(self, slack_webhook_url: str = None):
        self.slack_webhook = slack_webhook_url

    def send_slack_alert(self, message: str, channel: str = None):
        """Enviar alerta para Slack"""
        if not self.slack_webhook:
            logger.warning("Slack webhook não configurado")
            return

        payload = {
            'text': message,
            'channel': channel
        }

        try:
            response = requests.post(self.slack_webhook, json=payload, timeout=10)
            response.raise_for_status()
            logger.info("✅ Alerta enviado para Slack")
        except Exception as e:
            logger.error(f"❌ Erro ao enviar para Slack: {e}")

    def alert_new_competitor_ads(self, new_ads: List[Dict]):
        """Alertar sobre novos ads de competitors"""
        if not new_ads:
            return

        message = f"*{len(new_ads)} novos ads detectados!*\n\n"

        for ad in new_ads[:5]:  # Primeiros 5
            message += f"• *{ad['page']}*: {ad['headline']}\n"

        if len(new_ads) > 5:
            message += f"\n_...e mais {len(new_ads) - 5} ads_"

        self.send_slack_alert(message)

    def alert_high_performing_ad(self, ad: Dict):
        """Alertar sobre ad com alta performance"""
        message = (
            f"*Ad de alta performance detectado!*\n\n"
            f"*Página:* {ad['page_name']}\n"
            f"*Dias ativo:* {ad['days_active']}\n"
            f"*Headline:* {ad['headline']}\n"
            f"*CTA:* {ad['cta_detected']}\n\n"
            f"_Este ad está ativo há mais de {ad['days_active']} dias_"
        )

        self.send_slack_alert(message)


# Integração com pipeline
def monitor_with_alerts():
    """Monitoramento com sistema de alertas"""
    from src.main import AdIntelligencePipeline

    pipeline = AdIntelligencePipeline()
    alerts = AlertSystem(slack_webhook_url='YOUR_WEBHOOK_URL')

    # Monitorar competitors
    competitors = ['OpusClip', 'Descript', 'StoryShort.ai']

    # Detectar novos ads
    new_ads = []
    for page in competitors:
        ads = pipeline.api.search_ads(page, limit=50)

        for ad in ads:
            # Verificar se é novo (menos de 7 dias)
            from datetime import datetime, timedelta
            start = datetime.fromisoformat(ad['ad_delivery_start_time'].replace('Z', '+00:00'))
            if (datetime.now() - start).days <= 7:
                new_ads.append({
                    'page': ad['page_name'],
                    'headline': ad.get('ad_creative_link_titles', [''])[0],
                    'ad_id': ad['id']
                })

    # Enviar alertas
    if new_ads:
        alerts.alert_new_competitor_ads(new_ads)

    # Buscar high performers
    from src.storage.database import Ad
    high_performers = pipeline.db.session.query(Ad).filter(
        Ad.days_active >= 60,
        Ad.is_active == True
    ).all()

    for ad in high_performers[:3]:  # Top 3
        alerts.alert_high_performing_ad({
            'page_name': ad.page_name,
            'days_active': ad.days_active,
            'headline': ad.headline,
            'cta_detected': ad.cta_detected
        })
