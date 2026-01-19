# Meta Ads Intelligence System

Sistema completo de automação para análise competitiva de estratégias de marketing pago no Instagram através da Meta Ad Library.

## 🎯 Funcionalidades

- ✅ Coleta automatizada de ads via Meta Ad Library API
- ✅ Processamento e análise de texto (CTAs, hashtags, emojis)
- ✅ Armazenamento estruturado em SQLite
- ✅ Análise de padrões e insights
- ✅ Identificação de top performers
- ✅ Comparação de estratégias de competitors
- ✅ Scheduling automático (diário/semanal/mensal)
- ✅ Sistema de alertas via Slack
- ✅ Clustering com Machine Learning
- ✅ Relatórios detalhados

## 📋 Pré-requisitos

- Python 3.9+
- Facebook Developer Account
- Meta API Access Token

## 🚀 Setup Rápido

### 1. Instalar dependências

```bash
pip install -r requirements.txt
```

### 2. Configurar credenciais

Copie o arquivo de exemplo e adicione suas credenciais:

```bash
cp .env.example .env
```

Edite o arquivo `.env` e adicione seu token:

```
FB_ACCESS_TOKEN=seu_token_aqui
```

### 3. Como obter o Facebook Access Token

1. Acesse: https://developers.facebook.com/apps
2. Crie um novo app (tipo: Business)
3. Adicione o produto "Marketing API"
4. Vá para Graph API Explorer
5. Selecione as permissões: `ads_read`, `pages_read_engagement`
6. Gere um token de longa duração (60 dias)
7. Copie o token para o arquivo `.env`

## 📖 Uso Básico

### Exemplo 1: Coleta Simples

```python
from src.collectors.meta_api_collector import MetaAdLibraryAPI

api = MetaAdLibraryAPI()

# Buscar ads
ads = api.search_ads(
    search_terms='video editing ai',
    countries=['US'],
    platforms=['instagram'],
    limit=50
)

print(f"Encontrados {len(ads)} ads")
```

### Exemplo 2: Pipeline Completo

```python
from src.main import AdIntelligencePipeline

pipeline = AdIntelligencePipeline()

# Analisar keywords
keywords = ['video editing ai', 'viral videos', 'ai tools']
results = pipeline.collect_and_analyze(
    keywords=keywords,
    countries=['US', 'BR'],
    limit_per_keyword=50
)

# Gerar relatório
pipeline.generate_report()
```

### Exemplo 3: Análise de Competitors

```python
from src.main import AdIntelligencePipeline

pipeline = AdIntelligencePipeline()

# Analisar competitors
competitors = ['OpusClip', 'Descript', 'Captions.ai']
results = pipeline.analyze_competitors(competitors)

print(results['comparison'])
```

### Executar Exemplos Prontos

```bash
# Ver todos os exemplos disponíveis
python example_usage.py

# Executar exemplo específico
python example_usage.py 1  # Coleta básica
python example_usage.py 2  # Pipeline completo
python example_usage.py 3  # Análise de competitors
python example_usage.py 4  # Análise e insights
python example_usage.py 5  # Buscar por nicho
```

## 🤖 Automação

### Scheduler (Execução Agendada)

```bash
# Executar scheduler (modo contínuo)
python -m src.scheduler

# Executar todos os jobs imediatamente (teste)
python -m src.scheduler --run-now
```

**Agendamentos padrão:**
- Coleta diária: 02:00
- Análise de competitors: Segunda 03:00
- Análise profunda: 1º dia do mês 04:00

### Alertas

Configure alertas via Slack editando o arquivo `.env`:

```
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

## 📁 Estrutura do Projeto

```
metaAds/
├── src/                # Source code
│   ├── collectors/     # Módulos de coleta de dados
│   │   └── meta_api_collector.py
│   ├── processors/     # Processamento de dados
│   │   └── ad_parser.py
│   ├── storage/        # Armazenamento
│   │   └── database.py
│   ├── analyzers/      # Análise e insights
│   │   ├── ad_analyzer.py
│   │   └── advanced_analytics.py
│   ├── config.py       # Configurações
│   ├── main.py         # Pipeline principal
│   ├── scheduler.py    # Automação
│   └── alerts.py       # Sistema de alertas
├── data/               # Database SQLite
├── reports/            # Relatórios gerados
├── logs/               # Logs do sistema
├── example_usage.py    # Exemplos práticos
└── requirements.txt    # Dependências
```

## 📊 Análises Disponíveis

### Básicas
- Top performers (ads com maior longevidade)
- Distribuição de CTAs
- Padrões de texto (comprimento, emojis, hashtags)
- Palavras mais frequentes
- Análise por página/advertiser

### Avançadas
- Clustering de estratégias similares (ML)
- Análise temporal de tendências
- Comparação de competitors
- Identificação de marketing angles

## 🔍 Queries Úteis

### Buscar Top Performers

```python
from src.storage.database import AdDatabase

db = AdDatabase()
top = db.get_top_performers(min_days=30)
print(top.head())
```

### Buscar Ads Ativos

```python
active = db.get_active_ads()
print(f"Total de ads ativos: {len(active)}")
```

### Estatísticas do Database

```python
stats = db.get_stats()
print(stats)
```

## 📈 Casos de Uso

### 1. Validar Nicho de Produto

```python
keywords = ['ai video editor', 'video automation', 'content creation ai']
results = pipeline.collect_and_analyze(keywords, limit_per_keyword=100)

# Se > 50 ads ativos = nicho viável
```

### 2. Monitorar Competitors

```python
competitors = ['Competitor1', 'Competitor2', 'Competitor3']
analysis = pipeline.analyze_competitors(competitors)

# Comparar: total_ads, avg_days_active, CTAs, etc
```

### 3. Descobrir Marketing Angles

```python
from src.analyzers.ad_analyzer import AdAnalyzer

analyzer = AdAnalyzer(df)
patterns = analyzer.get_successful_patterns(min_days=30)

print(patterns['sample_headlines'])
```

## ⚠️ Limitações

- Rate limit: ~200 requests/hora
- Dados públicos limitados (sem métricas de performance exatas)
- Inferências baseadas em longevidade dos ads
- Access token expira a cada 60 dias

## 🔧 Troubleshooting

### "Invalid access token"
Token expirado. Gere um novo no Graph API Explorer.

### "Rate limit exceeded"
Aguarde 1 hora ou implemente múltiplos tokens.

### "Database locked"
SQLite não suporta múltiplos writers. Use PostgreSQL para produção.

## 📚 Documentação Adicional

- [Meta Ad Library](https://www.facebook.com/ads/library)
- [Graph API Docs](https://developers.facebook.com/docs/graph-api)
- [Marketing API](https://developers.facebook.com/docs/marketing-apis)

## 🛠️ Desenvolvimento

### Testes

```bash
# Executar coleta de teste
python -m src.collectors.meta_api_collector

# Testar pipeline completo
python -m src.main
```

### Adicionar novo módulo

1. Crie o arquivo em `src/collectors/`, `src/processors/`, `src/analyzers/` ou `src/storage/`
2. Importe no `src/main.py`
3. Adicione exemplos em `example_usage.py`

## 📝 Roadmap

- [ ] Análise de imagens com computer vision
- [ ] Predição de performance com ML
- [ ] Dashboard web interativo
- [ ] API REST
- [ ] Suporte a PostgreSQL
- [ ] Multi-tenancy

## 📄 Licença

Este projeto é de código aberto para fins educacionais.

## 🤝 Contribuições

Contribuições são bem-vindas! Abra uma issue ou pull request.

---

**Desenvolvido para análise competitiva e inteligência de marketing** 🚀
