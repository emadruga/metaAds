# src/main.py
from src.collectors.meta_api_collector import MetaAdLibraryAPI
from src.processors.ad_parser import AdParser
from src.storage.database import AdDatabase
from src.analyzers.ad_analyzer import AdAnalyzer
from src.config import Config
import logging
from datetime import datetime
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AdIntelligencePipeline:
    """
    Pipeline completo de coleta e análise
    """

    def __init__(self):
        self.api = MetaAdLibraryAPI()
        self.parser = AdParser()
        self.db = AdDatabase()
        logger.info("Pipeline inicializado")

    def collect_and_analyze(
        self,
        keywords: list,
        countries: list = ['US'],
        platforms: list = ['instagram'],
        limit_per_keyword: int = 100
    ):
        """
        Executar pipeline completo para lista de keywords
        """

        all_results = {}

        for keyword in keywords:
            logger.info(f"Processando keyword: {keyword}")

            try:
                # 1. Coletar
                logger.info(f"  Coletando ads...")
                raw_ads = self.api.search_ads(
                    search_terms=keyword,
                    countries=countries,
                    platforms=platforms,
                    limit=limit_per_keyword
                )

                if not raw_ads:
                    logger.warning(f"  Nenhum ad encontrado para '{keyword}'")
                    continue

                logger.info(f"  {len(raw_ads)} ads coletados")

                # 2. Processar
                logger.info(f"  Processando ads...")
                parsed_df = self.parser.parse_batch(raw_ads)

                # 3. Salvar
                logger.info(f"  Salvando no database...")
                self.db.save_ads(parsed_df, search_keyword=keyword)

                # 4. Analisar
                logger.info(f"  Analisando padrões...")
                analyzer = AdAnalyzer(parsed_df)
                insights = analyzer.get_insights_summary()

                all_results[keyword] = {
                    'total_ads': len(parsed_df),
                    'insights': insights,
                    'top_performers': analyzer.get_top_performers(min_days=30)
                }

                logger.info(f"  ✓ Keyword '{keyword}' processada com sucesso")

            except Exception as e:
                logger.error(f"  ✗ Erro ao processar '{keyword}': {e}")
                continue

        return all_results

    def analyze_competitors(self, competitor_pages: list):
        """
        Análise focada em competitors específicos
        """

        all_ads = []

        for page in competitor_pages:
            logger.info(f"Coletando ads de {page}...")

            try:
                # Buscar por nome da página
                ads = self.api.search_ads(
                    search_terms=page,
                    limit=100
                )

                # Filtrar apenas ads da página específica
                ads = [ad for ad in ads if ad.get('page_name') == page]

                if ads:
                    parsed = self.parser.parse_batch(ads)
                    self.db.save_ads(parsed, search_keyword=f"competitor:{page}")
                    all_ads.append(parsed)
                    logger.info(f"  {len(ads)} ads de {page} coletados")

            except Exception as e:
                logger.error(f"  Erro ao processar {page}: {e}")

        if all_ads:
            combined_df = pd.concat(all_ads, ignore_index=True)
            analyzer = AdAnalyzer(combined_df)

            return {
                'comparison': analyzer.compare_competitors(competitor_pages),
                'insights': analyzer.get_insights_summary()
            }

        return None

    def generate_report(self, output_path: str = 'reports/intelligence_report.txt'):
        """
        Gerar relatório consolidado
        """

        logger.info("Gerando relatório...")

        # Buscar todos os ads do database
        from src.storage.database import Ad
        all_ads = self.db.session.query(Ad).all()
        df = self.db._to_dataframe(all_ads)

        if len(df) == 0:
            logger.warning("Nenhum dado disponível para relatório")
            return

        analyzer = AdAnalyzer(df)

        # Gerar relatório
        report = []
        report.append("=" * 80)
        report.append("RELATÓRIO DE INTELIGÊNCIA DE ADS")
        report.append(f"Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 80)
        report.append("")

        # Stats gerais
        stats = self.db.get_stats()
        report.append("ESTATÍSTICAS GERAIS")
        report.append(f"Total de ads: {stats['total_ads']}")
        report.append(f"Ads ativos: {stats['active_ads']}")
        report.append(f"Páginas únicas: {stats['unique_pages']}")
        report.append("")

        # Insights
        report.append(analyzer.get_insights_summary())
        report.append("")

        # Top performers
        report.append("TOP 10 ADS POR LONGEVIDADE")
        top = analyzer.get_top_performers(min_days=30, top_n=10)
        for i, (_, ad) in enumerate(top.iterrows(), 1):
            report.append(f"{i}. {ad['page_name']} - {ad['days_active']} dias")
            report.append(f"   Headline: {ad['headline']}")
            report.append(f"   CTA: {ad['cta_detected']}")
            report.append("")

        # Análise por página
        report.append("ANÁLISE POR PÁGINA")
        by_page = analyzer.analyze_by_page().head(10)
        report.append(by_page.to_string())
        report.append("")

        # Padrões de sucesso
        report.append("PADRÕES EM ADS DE SUCESSO (30+ dias)")
        patterns = analyzer.get_successful_patterns(min_days=30)
        for key, value in patterns.items():
            report.append(f"{key}: {value}")
        report.append("")

        report.append("=" * 80)

        # Salvar
        report_text = '\n'.join(report)

        import os
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_text)

        logger.info(f"Relatório salvo em: {output_path}")

        return report_text


# Script de execução principal
if __name__ == '__main__':
    pipeline = AdIntelligencePipeline()

    # Exemplo 1: Buscar por keywords (nicho)
    keywords = [
        'video editing ai',
        'viral videos',
        'content creation tools',
        'StoryShort.ai'
    ]

    results = pipeline.collect_and_analyze(
        keywords=keywords,
        countries=['US', 'BR'],
        platforms=['instagram'],
        limit_per_keyword=50
    )

    print("\nRESULTADOS POR KEYWORD:")
    for keyword, data in results.items():
        print(f"\n{keyword}:")
        print(f"  Total ads: {data['total_ads']}")
        print(data['insights'])

    # Exemplo 2: Análise de competitors
    competitors = [
        'OpusClip',
        'Descript',
        'Captions.ai',
        'StoryShort.ai'
    ]

    competitor_analysis = pipeline.analyze_competitors(competitors)

    if competitor_analysis:
        print("\nANÁLISE DE COMPETITORS:")
        print(competitor_analysis['comparison'])

    # Exemplo 3: Gerar relatório final
    report = pipeline.generate_report()
    print("\n✅ Relatório gerado com sucesso!")
