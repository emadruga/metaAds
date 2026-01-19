# Quick Start Guide

## Setup (5 minutos)

### 1. Criar arquivo .env

```bash
cp .env.example .env
```

Edite `.env` e adicione seu Facebook Access Token:

```
FB_ACCESS_TOKEN=seu_token_aqui
```

**Como obter o token:**
1. Acesse: https://developers.facebook.com/apps
2. Crie novo app → Business
3. Adicione "Marketing API"
4. Graph API Explorer → Gerar Token
5. Permissões: `ads_read`, `pages_read_engagement`
6. Copie o token

### 2. Testar instalação

```bash
python example_usage.py 1
```

Se funcionar, você verá uma lista de ads coletados!

## Uso Básico

### Coletar e Analisar por Keyword

```python
from src.main import AdIntelligencePipeline

pipeline = AdIntelligencePipeline()

# Buscar ads sobre um nicho
results = pipeline.collect_and_analyze(
    keywords=['video editing ai', 'viral videos'],
    countries=['US'],
    limit_per_keyword=50
)

# Gerar relatório
pipeline.generate_report('reports/my_report.txt')
```

### Analisar Competitors

```python
from src.main import AdIntelligencePipeline

pipeline = AdIntelligencePipeline()

# Lista de competitors
competitors = ['OpusClip', 'Descript', 'Captions.ai']

# Analisar
results = pipeline.analyze_competitors(competitors)

# Ver comparação
print(results['comparison'])
```

### Ver Insights do Database

```python
from src.storage.database import AdDatabase, Ad
from src.analyzers.ad_analyzer import AdAnalyzer

db = AdDatabase()

# Buscar todos os ads
all_ads = db.session.query(Ad).all()
df = db._to_dataframe(all_ads)

# Analisar
analyzer = AdAnalyzer(df)

# Ver insights
print(analyzer.get_insights_summary())

# Top performers
top = analyzer.get_top_performers(min_days=30)
print(top)
```

## Exemplos Prontos

Execute os exemplos incluídos:

```bash
# Coleta básica
python example_usage.py 1

# Pipeline completo
python example_usage.py 2

# Análise de competitors
python example_usage.py 3

# Análise e insights
python example_usage.py 4

# Buscar por nicho
python example_usage.py 5
```

## Automação

Para rodar coletas automáticas:

```bash
# Testar (roda tudo agora)
python -m src.scheduler --run-now

# Modo contínuo (roda em horários agendados)
python -m src.scheduler
```

**Agendamentos:**
- Diário: 02:00
- Semanal (Segunda): 03:00
- Mensal: 04:00

## Estrutura Básica

```
metaAds/
├── src/                # Source code
│   ├── collectors/     # Coleta de dados via API
│   ├── processors/     # Processamento de texto
│   ├── storage/        # Database SQLite
│   ├── analyzers/      # Análise e insights
│   ├── config.py       # Configurações
│   ├── main.py         # Pipeline principal
│   ├── scheduler.py    # Automação
│   └── alerts.py       # Sistema de alertas
├── data/               # Database (criado automaticamente)
├── reports/            # Relatórios (criado automaticamente)
├── logs/               # Logs (criado automaticamente)
└── example_usage.py    # Exemplos
```

## Troubleshooting Rápido

### Erro: "Invalid access token"
→ Token expirado ou inválido. Gere novo token no Graph API Explorer.

### Erro: "Rate limit exceeded"
→ Aguarde 1 hora ou reduza quantidade de requests.

### Erro: "No module named 'src'"
→ Execute sempre do diretório raiz do projeto

### Nenhum dado no database
→ Execute primeiro: `python example_usage.py 2`

## Próximos Passos

1. **Coletar dados do seu nicho**: Edite `src/main.py` com suas keywords
2. **Analisar competitors**: Liste seus competitors principais
3. **Configurar alertas**: Adicione Slack webhook no `.env`
4. **Agendar execução**: Configure o `src/scheduler.py` para rodar diariamente

## Recursos

- 📖 Documentação completa: `Meta_Ads_Reverse_Engineering.md`
- 📋 README detalhado: `README.md`
- 💬 Graph API Explorer: https://developers.facebook.com/tools/explorer/
- 📚 Meta Ad Library: https://www.facebook.com/ads/library

## Dúvidas Frequentes

**P: Preciso pagar pela API?**
R: Não, a Meta Ad Library API é gratuita.

**P: Quantos ads posso coletar?**
R: Limite de ~200 requests/hora (cada request retorna até 100 ads).

**P: Os dados são em tempo real?**
R: Sim, são atualizados constantemente pela Meta.

**P: Posso usar para Facebook também?**
R: Sim, basta mudar `platforms=['facebook']` ao coletar.

**P: Token expira?**
R: Sim, a cada 60 dias. Você precisará renovar.

---

**Boa sorte com sua análise competitiva!** 🚀
