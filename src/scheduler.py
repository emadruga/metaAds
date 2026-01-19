# src/scheduler.py
import schedule
import time
from src.main import AdIntelligencePipeline
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def daily_collection():
    """Job diário de coleta"""
    logger.info("=" * 50)
    logger.info("Iniciando coleta diária...")
    logger.info("=" * 50)

    try:
        pipeline = AdIntelligencePipeline()

        # Keywords para monitorar diariamente
        keywords = [
            'video editing ai',
            'viral content',
            'social media tools',
            'ai video editor'
        ]

        results = pipeline.collect_and_analyze(
            keywords=keywords,
            countries=['US'],
            limit_per_keyword=50
        )

        # Gerar relatório
        pipeline.generate_report(
            output_path=f'reports/daily_report_{datetime.now().strftime("%Y%m%d")}.txt'
        )

        logger.info("✅ Coleta diária concluída com sucesso")

    except Exception as e:
        logger.error(f"❌ Erro na coleta diária: {e}")


def weekly_competitor_analysis():
    """Job semanal de análise de competitors"""
    logger.info("=" * 50)
    logger.info("Iniciando análise semanal de competitors...")
    logger.info("=" * 50)

    try:
        pipeline = AdIntelligencePipeline()

        # Competitors para monitorar
        competitors = [
            'OpusClip',
            'Descript',
            'Captions.ai',
            'StoryShort.ai',
            'Kapwing'
        ]

        results = pipeline.analyze_competitors(competitors)

        if results:
            # Salvar análise comparativa
            comparison_df = results['comparison']
            comparison_df.to_csv(
                f'reports/competitor_comparison_{datetime.now().strftime("%Y%m%d")}.csv',
                index=False
            )

            logger.info("✅ Análise de competitors concluída com sucesso")

    except Exception as e:
        logger.error(f"❌ Erro na análise de competitors: {e}")


def monthly_deep_analysis():
    """Job mensal de análise profunda"""
    logger.info("=" * 50)
    logger.info("Iniciando análise mensal profunda...")
    logger.info("=" * 50)

    try:
        pipeline = AdIntelligencePipeline()
        from src.analyzers.advanced_analytics import AdvancedAnalyzer
        from src.storage.database import Ad

        # Buscar todos os dados do último mês
        all_ads = pipeline.db.session.query(Ad).all()
        df = pipeline.db._to_dataframe(all_ads)

        if len(df) > 0:
            # Análise avançada
            advanced = AdvancedAnalyzer()

            # Clustering
            clusters = advanced.cluster_ad_strategies(df, n_clusters=5)
            clusters.to_csv(
                f'reports/clusters_{datetime.now().strftime("%Y%m%d")}.csv',
                index=False
            )

            # Tendências temporais
            trends = advanced.analyze_trends_over_time(df)
            trends.to_csv(
                f'reports/trends_{datetime.now().strftime("%Y%m%d")}.csv'
            )

            logger.info("✅ Análise profunda concluída com sucesso")

    except Exception as e:
        logger.error(f"❌ Erro na análise profunda: {e}")


# Configurar agendamentos
def setup_schedule():
    """Configurar todos os jobs agendados"""

    # Coleta diária às 2h da manhã
    schedule.every().day.at("02:00").do(daily_collection)

    # Análise de competitors toda segunda às 3h
    schedule.every().monday.at("03:00").do(weekly_competitor_analysis)

    # Análise profunda todo dia 1 do mês às 4h
    schedule.every().day.at("04:00").do(monthly_deep_analysis)

    logger.info("Scheduler configurado:")
    logger.info("  - Coleta diária: 02:00")
    logger.info("  - Análise competitors: Segunda 03:00")
    logger.info("  - Análise profunda: 1º dia do mês 04:00")


# Executar manualmente (para testar)
def run_all_jobs_now():
    """Executar todos os jobs imediatamente (para testes)"""
    logger.info("Executando todos os jobs manualmente...")

    daily_collection()
    weekly_competitor_analysis()
    monthly_deep_analysis()

    logger.info("✅ Todos os jobs executados!")


if __name__ == '__main__':
    import sys

    # Criar diretórios necessários
    import os
    os.makedirs('logs', exist_ok=True)
    os.makedirs('reports', exist_ok=True)

    if len(sys.argv) > 1 and sys.argv[1] == '--run-now':
        # Executar tudo agora (para teste)
        run_all_jobs_now()
    else:
        # Modo scheduling normal
        setup_schedule()
        logger.info("⏰ Scheduler iniciado. Aguardando jobs agendados...")

        while True:
            schedule.run_pending()
            time.sleep(60)  # Check a cada minuto
