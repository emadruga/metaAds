# analyzers/advanced_analytics.py
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import pandas as pd
import numpy as np


class AdvancedAnalyzer:
    """
    Análises avançadas com ML
    """

    def cluster_ad_strategies(self, ads_df: pd.DataFrame, n_clusters: int = 5):
        """
        Agrupar ads por similaridade de estratégia usando clustering
        """

        # Combinar texto
        texts = ads_df['full_text'].fillna('')

        # TF-IDF vectorization
        vectorizer = TfidfVectorizer(max_features=100, stop_words='english')
        features = vectorizer.fit_transform(texts)

        # Clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        ads_df['cluster'] = kmeans.fit_predict(features)

        # Analisar cada cluster
        cluster_analysis = []

        for cluster_id in range(n_clusters):
            cluster_ads = ads_df[ads_df['cluster'] == cluster_id]

            # Top palavras do cluster
            cluster_texts = ' '.join(cluster_ads['full_text'].fillna(''))
            cluster_vec = vectorizer.transform([cluster_texts])
            top_features = np.argsort(cluster_vec.toarray()[0])[-10:]
            top_words = [vectorizer.get_feature_names_out()[i] for i in top_features]

            cluster_analysis.append({
                'cluster_id': cluster_id,
                'size': len(cluster_ads),
                'avg_days_active': cluster_ads['days_active'].mean(),
                'top_words': top_words,
                'common_cta': cluster_ads['cta_detected'].mode()[0] if len(cluster_ads) > 0 else None,
                'sample_pages': cluster_ads['page_name'].value_counts().head(3).to_dict()
            })

        return pd.DataFrame(cluster_analysis)

    def analyze_trends_over_time(self, ads_df: pd.DataFrame):
        """
        Analisar como estratégias mudam ao longo do tempo
        """

        ads_df['month'] = pd.to_datetime(ads_df['start_date']).dt.to_period('M')

        trends = ads_df.groupby('month').agg({
            'ad_id': 'count',
            'text_length': 'mean',
            'has_emoji': lambda x: (x.sum() / len(x)) * 100,
            'cta_detected': lambda x: x.mode()[0] if len(x.mode()) > 0 else None
        }).rename(columns={
            'ad_id': 'total_ads',
            'text_length': 'avg_text_length',
            'has_emoji': 'emoji_usage_%'
        })

        return trends
