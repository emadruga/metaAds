#!/usr/bin/env python3
"""
Script para recalcular days_active de todos os ads no database do backend

Útil após coletas onde o campo não foi atualizado corretamente
"""

import sqlite3
from datetime import datetime
from dateutil import parser
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_date(date_str):
    """Parse date string em diferentes formatos"""
    if not date_str:
        return None
    try:
        dt = parser.parse(date_str)
        # Remove timezone info para evitar conflito
        return dt.replace(tzinfo=None)
    except:
        return None


def recalculate_all_days_active():
    """
    Recalcular days_active para todos os ads no database
    """
    logger.info("Iniciando recálculo de days_active...")

    conn = sqlite3.connect('backend/data/ads_intelligence.db')
    cursor = conn.cursor()

    # Buscar todos os ads
    cursor.execute("""
        SELECT id, meta_ad_id, page_name, start_date, end_date, is_active, days_active
        FROM ads
    """)

    all_ads = cursor.fetchall()

    if not all_ads:
        logger.warning("Nenhum ad encontrado no database")
        return

    logger.info(f"Encontrados {len(all_ads)} ads para recalcular")

    updated_count = 0
    errors = 0

    for ad in all_ads:
        ad_id, meta_ad_id, page_name, start_date_str, end_date_str, is_active, old_days_active = ad

        # Parse dates
        start_date = parse_date(start_date_str)
        if not start_date:
            logger.warning(f"Ad {meta_ad_id} sem start_date válida, pulando...")
            errors += 1
            continue

        # Calcular days_active
        end_date = parse_date(end_date_str) if end_date_str else datetime.now()
        delta = end_date - start_date
        new_days_active = delta.days

        # Atualizar se mudou
        if old_days_active != new_days_active:
            cursor.execute("""
                UPDATE ads
                SET days_active = ?, updated_at = ?
                WHERE id = ?
            """, (new_days_active, datetime.now().isoformat(), ad_id))

            logger.debug(
                f"Ad {meta_ad_id} ({page_name}): "
                f"{old_days_active or 0} → {new_days_active} dias"
            )
            updated_count += 1

    # Commit de todas as mudanças
    conn.commit()

    logger.info(f"✅ Recálculo concluído!")
    logger.info(f"   Total de ads: {len(all_ads)}")
    logger.info(f"   Ads atualizados: {updated_count}")
    logger.info(f"   Ads sem mudança: {len(all_ads) - updated_count - errors}")
    logger.info(f"   Erros: {errors}")

    # Mostrar alguns exemplos de ads ativos
    logger.info("\n📊 Top 10 ads mais longevos (ativos):")
    cursor.execute("""
        SELECT page_name, headline, days_active, start_date
        FROM ads
        WHERE is_active = 1
        ORDER BY days_active DESC
        LIMIT 10
    """)

    for i, (page, headline, days, start) in enumerate(cursor.fetchall(), 1):
        headline_short = (headline or 'Sem headline')[:50]
        logger.info(
            f"  {i}. {page}: {days} dias - \"{headline_short}...\""
        )

    # Estatísticas por status
    cursor.execute("""
        SELECT
            is_active,
            COUNT(*) as total,
            AVG(days_active) as avg_days,
            MAX(days_active) as max_days
        FROM ads
        GROUP BY is_active
    """)

    logger.info("\n📈 Estatísticas por status:")
    for is_active, total, avg_days, max_days in cursor.fetchall():
        status = "ATIVOS" if is_active else "INATIVOS"
        logger.info(
            f"  {status}: {total} ads | "
            f"Média: {avg_days:.1f} dias | "
            f"Máximo: {max_days} dias"
        )

    conn.close()


if __name__ == '__main__':
    try:
        recalculate_all_days_active()
    except Exception as e:
        logger.error(f"❌ Erro ao recalcular: {e}", exc_info=True)
        import sys
        sys.exit(1)
