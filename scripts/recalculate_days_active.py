#!/usr/bin/env python3
"""
Script para recalcular days_active de todos os ads no database

Útil após coletas onde o campo não foi atualizado corretamente
"""

import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from storage.database import AdDatabase, Ad
from datetime import datetime
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def recalculate_all_days_active():
    """
    Recalcular days_active para todos os ads no database
    """
    logger.info("Iniciando recálculo de days_active...")

    db = AdDatabase()

    # Buscar todos os ads
    all_ads = db.session.query(Ad).all()

    if not all_ads:
        logger.warning("Nenhum ad encontrado no database")
        return

    logger.info(f"Encontrados {len(all_ads)} ads para recalcular")

    updated_count = 0

    for ad in all_ads:
        if not ad.start_date:
            logger.warning(f"Ad {ad.ad_id} sem start_date, pulando...")
            continue

        # Calcular days_active
        end = ad.end_date or datetime.now()
        delta = end - ad.start_date
        new_days_active = delta.days

        # Atualizar se mudou
        if ad.days_active != new_days_active:
            old_days = ad.days_active or 0
            ad.days_active = new_days_active
            logger.debug(
                f"Ad {ad.ad_id} ({ad.page_name}): "
                f"{old_days} → {new_days_active} dias"
            )
            updated_count += 1

    # Commit de todas as mudanças
    db.session.commit()

    logger.info(f"✅ Recálculo concluído!")
    logger.info(f"   Total de ads: {len(all_ads)}")
    logger.info(f"   Ads atualizados: {updated_count}")
    logger.info(f"   Ads sem mudança: {len(all_ads) - updated_count}")

    # Mostrar alguns exemplos
    logger.info("\nExemplos de ads recalculados:")
    recent_active = db.session.query(Ad).filter(
        Ad.is_active == True
    ).order_by(Ad.days_active.desc()).limit(5).all()

    for ad in recent_active:
        logger.info(
            f"  • {ad.page_name}: {ad.days_active} dias - "
            f"{'ATIVO' if ad.is_active else 'INATIVO'}"
        )


if __name__ == '__main__':
    try:
        recalculate_all_days_active()
    except Exception as e:
        logger.error(f"❌ Erro ao recalcular: {e}", exc_info=True)
        sys.exit(1)
