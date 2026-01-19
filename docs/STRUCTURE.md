# Project Structure

## Overview

All code files are now organized under the `src/` directory for better project organization and maintainability.

## Directory Layout

```
metaAds/
├── src/                         # 🔹 All source code
│   ├── __init__.py
│   ├── config.py               # Configuration settings
│   ├── main.py                 # Main pipeline orchestrator
│   ├── scheduler.py            # Automated job scheduling
│   ├── alerts.py               # Alert system (Slack)
│   │
│   ├── collectors/             # 📥 Data collection
│   │   ├── __init__.py
│   │   └── meta_api_collector.py
│   │
│   ├── processors/             # ⚙️ Data processing
│   │   ├── __init__.py
│   │   └── ad_parser.py
│   │
│   ├── storage/                # 💾 Database layer
│   │   ├── __init__.py
│   │   └── database.py
│   │
│   └── analyzers/              # 📊 Analytics & insights
│       ├── __init__.py
│       ├── ad_analyzer.py
│       └── advanced_analytics.py
│
├── data/                        # SQLite database (auto-created)
├── reports/                     # Generated reports (auto-created)
├── logs/                        # System logs (auto-created)
│
├── example_usage.py            # Usage examples
├── requirements.txt            # Python dependencies
├── .env.example                # Environment template
├── .gitignore                  # Git ignore rules
│
├── README.md                   # Main documentation
├── QUICKSTART.md               # Quick start guide
├── PROJECT_SUMMARY.txt         # Project summary
└── Meta_Ads_Reverse_Engineering.md  # Complete guide
```

## Import Patterns

### From Code

All imports use the `src.` prefix:

```python
# Collectors
from src.collectors.meta_api_collector import MetaAdLibraryAPI

# Processors
from src.processors.ad_parser import AdParser

# Storage
from src.storage.database import AdDatabase, Ad

# Analyzers
from src.analyzers.ad_analyzer import AdAnalyzer
from src.analyzers.advanced_analytics import AdvancedAnalyzer

# Main modules
from src.main import AdIntelligencePipeline
from src.config import Config
```

### Running Modules

Use the `-m` flag when running modules:

```bash
# Run main pipeline
python -m src.main

# Run scheduler
python -m src.scheduler

# Run scheduler with immediate execution
python -m src.scheduler --run-now

# Test specific module
python -m src.collectors.meta_api_collector
```

### Running Examples

Examples remain at the root level for easy access:

```bash
python example_usage.py 1
python example_usage.py 2
python example_usage.py 3
```

## Benefits of This Structure

### 1. **Clean Separation**
- Clear distinction between source code and project files
- Configuration files at root level
- Code organized by functionality

### 2. **Professional Layout**
- Follows Python best practices
- Standard package structure
- Easy to understand and navigate

### 3. **Scalability**
- Easy to add new modules
- Clear module boundaries
- Supports future growth

### 4. **Maintainability**
- Related code grouped together
- Clear import paths
- Easy to refactor

### 5. **Deployment Ready**
- Clean package structure
- Easy to distribute
- Docker-friendly

## Module Descriptions

### collectors/
Handles data collection from external sources (Meta Ad Library API).

**Files:**
- `meta_api_collector.py` - API client with rate limiting

### processors/
Processes and transforms raw data into structured format.

**Files:**
- `ad_parser.py` - Parse ads and extract insights

### storage/
Manages data persistence and database operations.

**Files:**
- `database.py` - SQLAlchemy models and queries

### analyzers/
Performs analysis and generates insights from stored data.

**Files:**
- `ad_analyzer.py` - Pattern analysis and basic insights
- `advanced_analytics.py` - ML clustering and advanced analytics

### Root Level Modules

**config.py**
- Configuration settings
- Environment variables
- Constants

**main.py**
- Main pipeline orchestrator
- Coordinates all components
- Entry point for data collection

**scheduler.py**
- Automated job scheduling
- Daily/weekly/monthly tasks
- Background execution

**alerts.py**
- Alert system integration
- Slack notifications
- Event monitoring

## Adding New Modules

### 1. Create Module File

```bash
# Example: Adding a new exporter
touch src/exporters/csv_exporter.py
touch src/exporters/__init__.py
```

### 2. Update Imports

```python
# In your code
from src.exporters.csv_exporter import CSVExporter
```

### 3. Add to Documentation

Update relevant documentation files to include the new module.

## Best Practices

1. **Always use absolute imports from src/**
   ```python
   # Good
   from src.storage.database import Ad
   
   # Bad
   from storage.database import Ad
   ```

2. **Run from project root**
   ```bash
   # Good
   cd /path/to/metaAds
   python -m src.main
   
   # Bad
   cd /path/to/metaAds/src
   python main.py
   ```

3. **Keep examples at root level**
   - Easy for users to find
   - Simple execution
   - Clear entry points

4. **Maintain __init__.py files**
   - Makes directories proper Python packages
   - Enables relative imports
   - Supports package discovery

## Migration Notes

If updating from old structure:

1. **Update imports** - Add `src.` prefix
2. **Update run commands** - Use `-m` flag
3. **Update documentation** - Reference new paths
4. **Test thoroughly** - Verify all imports work

## Verification

Test that everything works:

```bash
# Test imports
python -c "from src.main import AdIntelligencePipeline; print('✓ Import OK')"

# Test examples
python example_usage.py 1

# Test modules
python -m src.collectors.meta_api_collector
```

---

**Last Updated:** 2026-01-18  
**Version:** 1.1  
**Status:** ✅ Production Ready
