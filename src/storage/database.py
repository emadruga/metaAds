# storage/database.py
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from typing import List
import pandas as pd

Base = declarative_base()


class Ad(Base):
    __tablename__ = 'ads'

    # Identificação
    id = Column(Integer, primary_key=True, autoincrement=True)
    ad_id = Column(String(100), unique=True, index=True)
    page_name = Column(String(200), index=True)
    page_id = Column(String(100), index=True)

    # Datas
    start_date = Column(DateTime, index=True)
    end_date = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    days_active = Column(Integer)
    collected_at = Column(DateTime, default=datetime.now)

    # Plataformas
    platforms = Column(String(200))
    snapshot_url = Column(Text)

    # Conteúdo
    body = Column(Text)
    headline = Column(String(500))
    description = Column(Text)
    link_caption = Column(String(500))
    full_text = Column(Text)

    # Métricas de texto
    text_length = Column(Integer)
    has_emoji = Column(Boolean)
    has_hashtags = Column(Boolean)
    hashtags = Column(Text)  # JSON array as string
    mentions = Column(Text)  # JSON array as string
    cta_detected = Column(String(50), index=True)

    # Metadados
    search_keyword = Column(String(200), index=True)


class AdDatabase:
    """
    Interface para operações de database
    """

    def __init__(self, db_path: str = 'data/ads_intelligence.db'):
        self.engine = create_engine(f'sqlite:///{db_path}')
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def save_ads(self, ads_df: pd.DataFrame, search_keyword: str = None):
        """
        Salvar ads no database
        """
        ads_df['search_keyword'] = search_keyword
        ads_df['collected_at'] = datetime.now()

        # Converter para records
        for _, row in ads_df.iterrows():
            # Verificar se já existe
            existing = self.session.query(Ad).filter_by(ad_id=row['ad_id']).first()

            if existing:
                # Atualizar se mudou status
                if row.get('is_active') != existing.is_active:
                    existing.is_active = row['is_active']
                    existing.end_date = row.get('end_date')
            else:
                # Criar novo
                ad = Ad(**row.to_dict())
                self.session.add(ad)

        self.session.commit()

    def get_ads_by_keyword(self, keyword: str) -> pd.DataFrame:
        """Buscar ads por keyword"""
        ads = self.session.query(Ad).filter_by(search_keyword=keyword).all()
        return self._to_dataframe(ads)

    def get_ads_by_page(self, page_name: str) -> pd.DataFrame:
        """Buscar ads por página"""
        ads = self.session.query(Ad).filter_by(page_name=page_name).all()
        return self._to_dataframe(ads)

    def get_top_performers(self, min_days: int = 30) -> pd.DataFrame:
        """
        Buscar ads que rodaram por muito tempo (signal de performance)
        """
        ads = self.session.query(Ad).filter(Ad.days_active >= min_days).all()
        return self._to_dataframe(ads).sort_values('days_active', ascending=False)

    def get_active_ads(self) -> pd.DataFrame:
        """Buscar ads atualmente ativos"""
        ads = self.session.query(Ad).filter_by(is_active=True).all()
        return self._to_dataframe(ads)

    def _to_dataframe(self, ads: List[Ad]) -> pd.DataFrame:
        """Converter list de Ad objects para DataFrame"""
        if not ads:
            return pd.DataFrame()

        data = []
        for ad in ads:
            row = {c.name: getattr(ad, c.name) for c in ad.__table__.columns}
            data.append(row)

        return pd.DataFrame(data)

    def get_stats(self) -> dict:
        """Estatísticas gerais do database"""
        total = self.session.query(Ad).count()
        active = self.session.query(Ad).filter_by(is_active=True).count()
        pages = self.session.query(Ad.page_name).distinct().count()

        return {
            'total_ads': total,
            'active_ads': active,
            'unique_pages': pages,
            'inactive_ads': total - active
        }
