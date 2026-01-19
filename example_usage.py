# example_usage.py
"""
Exemplos práticos de uso do sistema
"""
from src.collectors.meta_api_collector import MetaAdLibraryAPI
from src.processors.ad_parser import AdParser
from src.storage.database import AdDatabase
from src.analyzers.ad_analyzer import AdAnalyzer
import pandas as pd


def example_1_basic_collection():
    """Exemplo 1: Coleta básica de ads"""
    print("\n" + "="*60)
    print("EXEMPLO 1: Coleta Básica")
    print("="*60)

    api = MetaAdLibraryAPI()

    # Buscar ads sobre "video editing ai"
    ads = api.search_ads(
        search_terms='video editing ai',
        countries=['US'],
        platforms=['instagram'],
        limit=10
    )

    print(f"\nEncontrados {len(ads)} ads")
    for i, ad in enumerate(ads[:3], 1):
        print(f"\n{i}. Página: {ad.get('page_name')}")
        body = ad.get('ad_creative_bodies', [''])[0][:100] if ad.get('ad_creative_bodies') else 'N/A'
        print(f"   Texto: {body}...")


def example_2_complete_pipeline():
    """Exemplo 2: Pipeline completo (Coleta + Processamento + Storage)"""
    print("\n" + "="*60)
    print("EXEMPLO 2: Pipeline Completo")
    print("="*60)

    # 1. Coletar
    api = MetaAdLibraryAPI()
    raw_ads = api.search_ads(
        search_terms='ai video editor',
        countries=['US'],
        limit=20
    )

    print(f"\n1. Coletados: {len(raw_ads)} ads")

    # 2. Processar
    parser = AdParser()
    parsed_df = parser.parse_batch(raw_ads)

    print(f"2. Processados: {len(parsed_df)} ads")
    print(f"\nCTAs detectados:")
    print(parsed_df['cta_detected'].value_counts())

    # 3. Salvar
    db = AdDatabase()
    db.save_ads(parsed_df, search_keyword='ai video editor')

    print(f"\n3. Salvos no database!")

    # 4. Consultar
    stats = db.get_stats()
    print(f"\n4. Estatísticas do Database:")
    print(f"   Total: {stats['total_ads']}")
    print(f"   Ativos: {stats['active_ads']}")
    print(f"   Páginas únicas: {stats['unique_pages']}")


def example_3_competitor_analysis():
    """Exemplo 3: Análise de Competitors"""
    print("\n" + "="*60)
    print("EXEMPLO 3: Análise de Competitors")
    print("="*60)

    api = MetaAdLibraryAPI()
    parser = AdParser()
    db = AdDatabase()

    competitors = ['OpusClip', 'Descript']
    all_competitor_ads = []

    for competitor in competitors:
        ads = api.search_ads(
            search_terms=competitor,
            limit=10
        )
        all_competitor_ads.extend(ads)
        print(f"\n{competitor}: {len(ads)} ads encontrados")

    if all_competitor_ads:
        parsed_df = parser.parse_batch(all_competitor_ads)
        analyzer = AdAnalyzer(parsed_df)

        print("\n\nComparação de Competitors:")
        comparison = analyzer.compare_competitors(competitors)
        print(comparison)


def example_4_analysis_and_insights():
    """Exemplo 4: Análise e Insights"""
    print("\n" + "="*60)
    print("EXEMPLO 4: Análise e Insights")
    print("="*60)

    db = AdDatabase()

    # Buscar ads do database
    from src.storage.database import Ad
    all_ads = db.session.query(Ad).all()
    df = db._to_dataframe(all_ads)

    if len(df) == 0:
        print("\nNenhum dado disponível. Execute primeiro os exemplos 1 ou 2.")
        return

    analyzer = AdAnalyzer(df)

    # Insights resumidos
    print("\n" + analyzer.get_insights_summary())

    # Top performers
    print("\n\nTop 5 Ads por Longevidade:")
    top = analyzer.get_top_performers(min_days=10, top_n=5)
    for i, (_, ad) in enumerate(top.iterrows(), 1):
        print(f"\n{i}. {ad['page_name']}")
        print(f"   Dias ativo: {ad['days_active']}")
        print(f"   Headline: {ad['headline'][:60]}..." if ad['headline'] else "   Headline: N/A")
        print(f"   CTA: {ad['cta_detected']}")


def example_5_search_competitors():
    """Exemplo 5: Buscar por Nicho"""
    print("\n" + "="*60)
    print("EXEMPLO 5: Buscar por Nicho")
    print("="*60)

    api = MetaAdLibraryAPI()

    niche_ads = api.search_ads(
        search_terms='social media tools',
        countries=['US', 'BR'],
        ad_active_status='ACTIVE',  # Apenas ativos
        limit=15
    )

    print(f"\nTotal de ads ativos no nicho: {len(niche_ads)}")

    # Agrupar por página
    from collections import Counter
    pages = Counter([ad.get('page_name') for ad in niche_ads])

    print("\nTop 5 Páginas com mais ads:")
    for page, count in pages.most_common(5):
        print(f"  {page}: {count} ads")


if __name__ == '__main__':
    print("\n" + "="*60)
    print("EXEMPLOS DE USO - Meta Ads Intelligence System")
    print("="*60)

    import sys

    if len(sys.argv) > 1:
        example_num = sys.argv[1]
        if example_num == '1':
            example_1_basic_collection()
        elif example_num == '2':
            example_2_complete_pipeline()
        elif example_num == '3':
            example_3_competitor_analysis()
        elif example_num == '4':
            example_4_analysis_and_insights()
        elif example_num == '5':
            example_5_search_competitors()
        else:
            print("\nUso: python example_usage.py [1-5]")
    else:
        print("\nExecutando todos os exemplos...\n")
        print("NOTA: Certifique-se de ter configurado FB_ACCESS_TOKEN no arquivo .env")
        print("\nPara executar exemplos individuais:")
        print("  python example_usage.py 1  - Coleta básica")
        print("  python example_usage.py 2  - Pipeline completo")
        print("  python example_usage.py 3  - Análise de competitors")
        print("  python example_usage.py 4  - Análise e insights")
        print("  python example_usage.py 5  - Buscar por nicho")

        # Execute o exemplo básico se nenhum argumento foi fornecido
        try:
            example_1_basic_collection()
        except Exception as e:
            print(f"\nErro: {e}")
            print("\nVerifique se você configurou o FB_ACCESS_TOKEN no arquivo .env")
