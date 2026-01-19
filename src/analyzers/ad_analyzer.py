# analyzers/ad_analyzer.py
import pandas as pd
from collections import Counter
from typing import Dict, List
import re


class AdAnalyzer:
    """
    Análise de padrões e insights de ads
    """

    def __init__(self, ads_df: pd.DataFrame):
        self.df = ads_df

    def get_top_performers(self, min_days: int = 30, top_n: int = 10) -> pd.DataFrame:
        """
        Ads com maior longevidade (provável bom performance)
        """
        top = self.df[self.df['days_active'] >= min_days].nlargest(top_n, 'days_active')

        return top[['page_name', 'days_active', 'body', 'headline', 'cta_detected']]

    def analyze_cta_distribution(self) -> pd.Series:
        """
        Distribuição de CTAs utilizados
        """
        return self.df['cta_detected'].value_counts()

    def analyze_text_patterns(self) -> Dict:
        """
        Análise de padrões de texto
        """
        return {
            'avg_text_length': self.df['text_length'].mean(),
            'median_text_length': self.df['text_length'].median(),
            'emoji_usage': (self.df['has_emoji'].sum() / len(self.df)) * 100,
            'hashtag_usage': (self.df['has_hashtags'].sum() / len(self.df)) * 100,
        }

    def get_most_common_words(self, top_n: int = 50, min_length: int = 4) -> List[tuple]:
        """
        Palavras mais frequentes nos ads
        """
        # Combinar todo o texto
        all_text = ' '.join(self.df['full_text'].dropna().astype(str))

        # Tokenizar
        words = re.findall(r'\b\w+\b', all_text.lower())

        # Filtrar stopwords comuns e palavras curtas
        stopwords = {'the', 'and', 'for', 'you', 'your', 'with', 'this',
                     'that', 'from', 'are', 'our', 'can', 'get', 'now'}
        words = [w for w in words if len(w) >= min_length and w not in stopwords]

        # Contar
        return Counter(words).most_common(top_n)

    def analyze_by_page(self) -> pd.DataFrame:
        """
        Métricas agregadas por página
        """
        return self.df.groupby('page_name').agg({
            'ad_id': 'count',
            'days_active': 'mean',
            'is_active': 'sum',
            'text_length': 'mean',
            'has_emoji': 'sum'
        }).rename(columns={
            'ad_id': 'total_ads',
            'days_active': 'avg_days_active',
            'is_active': 'active_ads',
            'text_length': 'avg_text_length',
            'has_emoji': 'ads_with_emoji'
        }).sort_values('total_ads', ascending=False)

    def get_successful_patterns(self, min_days: int = 30) -> Dict:
        """
        Identificar padrões em ads de sucesso
        """
        successful = self.df[self.df['days_active'] >= min_days]

        if len(successful) == 0:
            return {}

        return {
            'common_ctas': successful['cta_detected'].value_counts().head(5).to_dict(),
            'avg_text_length': successful['text_length'].mean(),
            'emoji_usage_rate': (successful['has_emoji'].sum() / len(successful)) * 100,
            'hashtag_usage_rate': (successful['has_hashtags'].sum() / len(successful)) * 100,
            'sample_headlines': successful['headline'].dropna().head(5).tolist()
        }

    def compare_competitors(self, pages: List[str]) -> pd.DataFrame:
        """
        Comparar estratégias de competitors
        """
        comparison = []

        for page in pages:
            page_ads = self.df[self.df['page_name'] == page]

            if len(page_ads) == 0:
                continue

            comparison.append({
                'page': page,
                'total_ads': len(page_ads),
                'active_ads': page_ads['is_active'].sum(),
                'avg_days_active': page_ads['days_active'].mean(),
                'most_common_cta': page_ads['cta_detected'].mode()[0] if len(page_ads['cta_detected'].mode()) > 0 else None,
                'emoji_usage_%': (page_ads['has_emoji'].sum() / len(page_ads)) * 100,
                'avg_text_length': page_ads['text_length'].mean()
            })

        return pd.DataFrame(comparison).sort_values('total_ads', ascending=False)

    def get_insights_summary(self) -> str:
        """
        Gerar resumo textual de insights
        """
        insights = []

        # Total ads
        insights.append(f"Total de {len(self.df)} ads coletados")

        # Top performers
        top = self.get_top_performers(min_days=30, top_n=3)
        if len(top) > 0:
            insights.append(f"\nTop 3 ads mais longevos:")
            for _, ad in top.iterrows():
                headline = ad['headline'][:50] if ad['headline'] else 'Sem headline'
                insights.append(f"  • {ad['page_name']}: {ad['days_active']} dias - '{headline}...'")

        # CTAs
        ctas = self.analyze_cta_distribution()
        if len(ctas) > 0:
            insights.append(f"\nCTAs mais usados:")
            for cta, count in ctas.head(3).items():
                insights.append(f"  • {cta}: {count} ads ({count/len(self.df)*100:.1f}%)")

        # Padrões de texto
        patterns = self.analyze_text_patterns()
        insights.append(f"\nPadrões de texto:")
        insights.append(f"  • Comprimento médio: {patterns['avg_text_length']:.0f} caracteres")
        insights.append(f"  • Uso de emoji: {patterns['emoji_usage']:.1f}% dos ads")
        insights.append(f"  • Uso de hashtags: {patterns['hashtag_usage']:.1f}% dos ads")

        # Palavras comuns
        words = self.get_most_common_words(top_n=10)
        insights.append(f"\nPalavras mais comuns:")
        insights.append(f"  {', '.join([w[0] for w in words[:10]])}")

        return '\n'.join(insights)
