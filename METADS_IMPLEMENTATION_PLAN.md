# MetAds Implementation Plan

## Project Overview

**MetAds** is a competitive intelligence tool for analyzing Meta (Facebook/Instagram) ads. It enables users to search, filter, and analyze ads from the Meta Ad Library to identify winning patterns and competitor strategies.

**Key Concept: Niches** - Users organize their research into separate "niches" (analysis projects), each containing its own collection of ads, saved items, and search history. Examples:
- "Video Editing Apps" niche
- "CRMs (Pipedrive, HubSpot)" niche
- "Presidential Election 2026" niche

### Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | Vue 3 (Composition API) + Vite + Vue Router + Pinia |
| **Backend** | Flask (Python 3.9+) + Flask-CORS + SQLAlchemy |
| **Database** | SQLite (local development) |
| **Data Collection** | Meta Ad Library API + custom collectors/parsers |

### Architecture

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│  Meta Ad        │      │  Flask Backend  │      │  Vue Frontend   │
│  Library API    │ ───► │  (REST API)     │ ◄─── │  (SPA)          │
└─────────────────┘      └────────┬────────┘      └─────────────────┘
        │                         │                        │
        │                ┌────────▼────────┐               │
        │                │    SQLite       │               │
        │                │    Database     │               │
        │                └─────────────────┘               │
        │                         ▲                        │
        │                         │                        │
        └─────────────────────────┘                        │
              Data Collection Pipeline                     │
                      (per niche)                          │
                                                           │
                      localhost:5000 ◄─────────────────────┘
                      localhost:5173 (Vite dev server)
```

### Data Organization with Niches

```
┌─────────────────────────────────────────────────────────────────┐
│                         NICHES                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐ │
│  │ Video Editing    │  │ CRMs             │  │ Election 2026  │ │
│  │ Apps             │  │ (Pipedrive...)   │  │                │ │
│  ├──────────────────┤  ├──────────────────┤  ├────────────────┤ │
│  │ Keywords:        │  │ Keywords:        │  │ Keywords:      │ │
│  │ - video editing  │  │ - pipedrive      │  │ - vote 2026    │ │
│  │ - ai video       │  │ - hubspot crm    │  │ - election     │ │
│  │ - opus clip      │  │ - salesforce     │  │ - candidate    │ │
│  ├──────────────────┤  ├──────────────────┤  ├────────────────┤ │
│  │ Ads: 342         │  │ Ads: 187         │  │ Ads: 89        │ │
│  │ Saved: 24        │  │ Saved: 12        │  │ Saved: 8       │ │
│  │ Pages: 45        │  │ Pages: 23        │  │ Pages: 31      │ │
│  └──────────────────┘  └──────────────────┘  └────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Foundation & Database

**Duration:** Days 1-3

### Day 1: Project Structure & Dependencies

#### Tasks

- [ ] Create project folder structure
- [ ] Set up Python virtual environment
- [ ] Install backend dependencies
- [ ] Initialize Vue project with Vite
- [ ] Configure ESLint, Prettier for frontend

#### Folder Structure

```
metaAds/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── niche.py          # NEW
│   │   │   ├── ad.py
│   │   │   ├── saved_ad.py
│   │   │   └── page.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── niches.py         # NEW
│   │   │   ├── ads.py
│   │   │   └── saved.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── niche_service.py  # NEW
│   │   │   ├── ad_service.py
│   │   │   └── variant_service.py
│   │   └── utils/
│   │       └── __init__.py
│   ├── collectors/
│   │   ├── __init__.py
│   │   └── meta_api_collector.py
│   ├── processors/
│   │   ├── __init__.py
│   │   └── ad_parser.py
│   ├── migrations/
│   ├── tests/
│   ├── requirements.txt
│   ├── run.py
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── assets/
│   │   ├── components/
│   │   │   ├── common/
│   │   │   ├── niches/           # NEW
│   │   │   ├── search/
│   │   │   ├── results/
│   │   │   └── detail/
│   │   ├── composables/
│   │   ├── router/
│   │   ├── stores/
│   │   ├── views/
│   │   ├── App.vue
│   │   └── main.js
│   ├── public/
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
├── data/
│   └── ads_intelligence.db
├── docs/
├── .gitignore
└── README.md
```

#### Deliverables

- `backend/requirements.txt`
- `frontend/package.json`
- Working folder structure

---

### Day 2: Database Models

#### Tasks

- [ ] Define SQLAlchemy models with UUID primary keys
- [ ] Create database initialization script
- [ ] Set up Flask-Migrate for migrations
- [ ] Write seed script with sample data (including sample niches)
- [ ] Implement UUID generation utilities

#### Database Design Principles

The schema is designed to be **DynamoDB-compatible** for future cloud migration:

| Principle | Implementation |
|-----------|----------------|
| **UUIDs for all IDs** | No auto-increment; use `uuid4()` for portability |
| **No foreign keys** | Denormalized data; relationships via matching UUIDs |
| **Composite keys ready** | PK + SK pattern (niche_id + entity_id) |
| **Denormalization** | Embed related data to avoid JOINs |
| **Native lists** | Store as JSON in SQLite, native Lists in DynamoDB |
| **ISO8601 dates** | String format for cross-database compatibility |

#### Database Schema

```
┌─────────────────────────────────────────────────────────────────┐
│                           niches                                 │
├─────────────────────────────────────────────────────────────────┤
│ PK: niche_id        UUID (partition key)                        │
│ SK: "METADATA"      (sort key - constant for main record)       │
│ ─────────────────────────────────────────────────────────────── │
│ niche_id            UUID PRIMARY KEY                            │
│ slug                VARCHAR(200) UNIQUE INDEX                   │
│ name                VARCHAR(200)                                │
│ description         TEXT                                        │
│ color               VARCHAR(7) (hex color for UI)               │
│ icon                VARCHAR(50) (emoji or icon name)            │
│ keywords            JSON (list of search keywords)              │
│ countries           JSON (list of country codes)                │
│ platforms           JSON (list of platforms)                    │
│ is_active           BOOLEAN DEFAULT TRUE                        │
│ created_at          VARCHAR(30) ISO8601                         │
│ updated_at          VARCHAR(30) ISO8601                         │
│                                                                  │
│ Index: slug-index (slug → niche_id)                             │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                            ads                                   │
│         (includes denormalized saved_ads data)                   │
├─────────────────────────────────────────────────────────────────┤
│ PK: niche_id        UUID (partition key)                        │
│ SK: meta_ad_id      "AD#<meta_ad_id>" (sort key)                │
│ ─────────────────────────────────────────────────────────────── │
│ id                  UUID PRIMARY KEY (internal unique ID)       │
│ niche_id            UUID INDEX                                  │
│ meta_ad_id          VARCHAR(100) (original Meta Ad Library ID)  │
│                                                                  │
│ -- Page info (denormalized from pages table) --                 │
│ page_id             VARCHAR(100) INDEX                          │
│ page_name           VARCHAR(200)                                │
│ page_verified       BOOLEAN                                     │
│ is_competitor_page  BOOLEAN DEFAULT FALSE                       │
│                                                                  │
│ -- Ad timing --                                                 │
│ start_date          VARCHAR(30) ISO8601 INDEX                   │
│ end_date            VARCHAR(30) ISO8601 (nullable)              │
│ is_active           BOOLEAN INDEX                               │
│ days_active         INTEGER                                     │
│                                                                  │
│ -- Ad content --                                                │
│ platforms           JSON (list of platforms)                    │
│ snapshot_url        TEXT                                        │
│ thumbnail_url       TEXT                                        │
│ body                TEXT                                        │
│ headline            VARCHAR(500)                                │
│ description         TEXT                                        │
│ link_caption        VARCHAR(500)                                │
│ full_text           TEXT                                        │
│ cta_detected        VARCHAR(50) INDEX                           │
│ landing_url         TEXT                                        │
│                                                                  │
│ -- Text analysis --                                             │
│ text_length         INTEGER                                     │
│ has_emoji           BOOLEAN                                     │
│ has_hashtags        BOOLEAN                                     │
│ hashtags            JSON (list of hashtags)                     │
│ mentions            JSON (list of mentions)                     │
│                                                                  │
│ -- Collection metadata --                                       │
│ country_codes       JSON (list of country codes)                │
│ search_keyword      VARCHAR(200) INDEX                          │
│ collected_at        VARCHAR(30) ISO8601                         │
│                                                                  │
│ -- Saved ads (denormalized - no separate table) --              │
│ is_saved            BOOLEAN DEFAULT FALSE INDEX                 │
│ saved_at            VARCHAR(30) ISO8601 (nullable)              │
│ saved_notes         TEXT (nullable)                             │
│ saved_tags          JSON (list of tags, nullable)               │
│                                                                  │
│ -- Timestamps --                                                │
│ created_at          VARCHAR(30) ISO8601                         │
│ updated_at          VARCHAR(30) ISO8601                         │
│                                                                  │
│ UNIQUE(niche_id, meta_ad_id)                                    │
│                                                                  │
│ -- Access Pattern Indexes (GSIs in DynamoDB) --                 │
│ Index: niche-days-index (niche_id + days_active DESC)           │
│ Index: niche-page-index (niche_id + page_id)                    │
│ Index: niche-saved-index (niche_id + is_saved)                  │
│ Index: niche-cta-index (niche_id + cta_detected)                │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                          pages                                   │
│              (global page registry)                              │
├─────────────────────────────────────────────────────────────────┤
│ PK: page_id         VARCHAR(100) (partition key)                │
│ SK: "METADATA"      (sort key - constant)                       │
│ ─────────────────────────────────────────────────────────────── │
│ page_id             VARCHAR(100) PRIMARY KEY (Meta page ID)     │
│ page_name           VARCHAR(200)                                │
│ is_verified         BOOLEAN                                     │
│ first_seen          VARCHAR(30) ISO8601                         │
│ last_seen           VARCHAR(30) ISO8601                         │
│ created_at          VARCHAR(30) ISO8601                         │
│ updated_at          VARCHAR(30) ISO8601                         │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      niche_pages                                 │
│         (tracks pages per niche + competitor status)             │
├─────────────────────────────────────────────────────────────────┤
│ PK: niche_id        UUID (partition key)                        │
│ SK: page_id         "PAGE#<page_id>" (sort key)                 │
│ ─────────────────────────────────────────────────────────────── │
│ id                  UUID PRIMARY KEY                            │
│ niche_id            UUID INDEX                                  │
│ page_id             VARCHAR(100) INDEX                          │
│ page_name           VARCHAR(200) (denormalized)                 │
│ is_competitor       BOOLEAN DEFAULT FALSE                       │
│ notes               TEXT                                        │
│ total_ads_in_niche  INTEGER DEFAULT 0 (denormalized count)      │
│ added_at            VARCHAR(30) ISO8601                         │
│                                                                  │
│ UNIQUE(niche_id, page_id)                                       │
│                                                                  │
│ Index: page-niche-index (page_id + niche_id) -- reverse lookup  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    collection_runs                               │
│              (tracks data collection history)                    │
├─────────────────────────────────────────────────────────────────┤
│ PK: niche_id        UUID (partition key)                        │
│ SK: run_id          "RUN#<timestamp>#<uuid>" (sort key)         │
│ ─────────────────────────────────────────────────────────────── │
│ run_id              UUID PRIMARY KEY                            │
│ niche_id            UUID INDEX                                  │
│ keyword             VARCHAR(200)                                │
│ status              VARCHAR(20) (pending/running/completed/error│
│ ads_collected       INTEGER DEFAULT 0                           │
│ ads_new             INTEGER DEFAULT 0                           │
│ ads_updated         INTEGER DEFAULT 0                           │
│ error_message       TEXT                                        │
│ started_at          VARCHAR(30) ISO8601                         │
│ completed_at        VARCHAR(30) ISO8601                         │
│                                                                  │
│ Index: niche-status-index (niche_id + status)                   │
└─────────────────────────────────────────────────────────────────┘
```

#### Entity Relationships (Denormalized)

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│  ┌─────────┐         ┌─────────────────────────────────────┐    │
│  │  Niche  │────1:N──│  Ad (includes saved status/notes)   │    │
│  └─────────┘         │  (includes page_name, page_verified) │    │
│       │              └─────────────────────────────────────┘    │
│       │                                                          │
│       │              ┌─────────────────────────────────────┐    │
│       ├────1:N───────│  NichePage (competitor tracking)     │    │
│       │              │  (includes denormalized page_name)   │    │
│       │              └─────────────────────────────────────┘    │
│       │                                                          │
│       │              ┌─────────────────────────────────────┐    │
│       └────1:N───────│  CollectionRun (history)             │    │
│                      └─────────────────────────────────────┘    │
│                                                                  │
│  ┌─────────┐                                                     │
│  │  Page   │  (global registry - referenced by page_id)         │
│  └─────────┘                                                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

Note: No foreign keys. Relationships maintained via UUID matching.
      Data is denormalized to support single-query access patterns.
```

#### Access Patterns

| Access Pattern | Query Strategy | Index Used |
|----------------|----------------|------------|
| List all niches | Scan niches table | - |
| Get niche by slug | Query by slug | slug-index |
| Get all ads in niche | Query by niche_id | niche_id (PK) |
| Get ads sorted by days_active | Query niche_id, sort by days_active | niche-days-index |
| Get ads from specific page | Query niche_id + page_id | niche-page-index |
| Get saved ads in niche | Query niche_id + is_saved=true | niche-saved-index |
| Get related ads (variants) | Query niche_id + page_id, filter dates | niche-page-index |
| Get collection history | Query niche_id, sort by run_id | niche_id (PK) |

#### UUID Generation

```python
# backend/app/utils/ids.py
import uuid
from datetime import datetime

def generate_uuid() -> str:
    """Generate a new UUID4 string."""
    return str(uuid.uuid4())

def generate_sort_key(prefix: str, timestamp: datetime = None) -> str:
    """Generate a sort key with timestamp for ordering.

    Example: "RUN#2026-01-30T14:30:00Z#a1b2c3d4"
    """
    ts = timestamp or datetime.utcnow()
    return f"{prefix}#{ts.isoformat()}Z#{generate_uuid()[:8]}"

def now_iso8601() -> str:
    """Return current UTC time as ISO8601 string."""
    return datetime.utcnow().isoformat() + "Z"
```

#### Deliverables

- `backend/app/models/niche.py`
- `backend/app/models/ad.py` (with denormalized saved_ads and page data)
- `backend/app/models/page.py`
- `backend/app/models/niche_page.py`
- `backend/app/models/collection_run.py`
- `backend/app/utils/ids.py` (UUID generation utilities)
- Database migration files

---

### Day 3: Data Collection Integration

#### Tasks

- [ ] Integrate existing Meta API collector
- [ ] Integrate existing ad parser
- [ ] Create CLI command to run collection **per niche**
- [ ] Test end-to-end: API → Parser → Database
- [ ] Create sample niches with data

#### Sample Niches for Testing

```python
sample_niches = [
    {
        "name": "Video Editing Apps",
        "slug": "video-editing-apps",
        "description": "AI-powered video editing tools and competitors",
        "color": "#8B5CF6",  # Purple
        "icon": "🎬",
        "keywords": ["video editing ai", "ai video editor", "opus clip", "descript"],
        "countries": ["US", "BR"],
        "platforms": ["instagram", "facebook"]
    },
    {
        "name": "CRMs",
        "slug": "crms",
        "description": "CRM software like Pipedrive, HubSpot, Salesforce",
        "color": "#10B981",  # Green
        "icon": "📊",
        "keywords": ["pipedrive", "hubspot crm", "salesforce", "crm software"],
        "countries": ["US"],
        "platforms": ["instagram", "facebook"]
    }
]
```

#### CLI Commands (Updated)

```bash
# Create a new niche
python run.py niche create --name "Video Editing Apps" --keywords "video editing ai,opus clip"

# List all niches
python run.py niche list

# Collect ads for a specific niche
python run.py collect --niche "video-editing-apps" --limit 50

# Collect ads for all active niches
python run.py collect --all --limit 50

# Show niche stats
python run.py niche stats --niche "video-editing-apps"
```

#### Deliverables

- Working data collection pipeline (niche-aware)
- SQLite database with sample niches and data
- CLI commands for niche management

---

## Phase 2: Flask REST API Backend

**Duration:** Days 4-8 (extended by 1 day for niche endpoints)

### Day 4: Flask App Setup

#### Tasks

- [ ] Initialize Flask application factory
- [ ] Configure CORS for local development
- [ ] Set up environment configuration
- [ ] Create health check endpoint
- [ ] Set up error handling middleware

#### API Configuration

```python
# Config
FLASK_ENV=development
FLASK_DEBUG=True
DATABASE_URL=sqlite:///data/ads_intelligence.db
CORS_ORIGINS=http://localhost:5173
```

#### Endpoints (Day 4)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/stats` | Global database statistics |

#### Deliverables

- `backend/app/__init__.py` (app factory)
- `backend/app/config.py`
- `backend/run.py`
- Working `/api/health` endpoint

---

### Day 5: Niche Endpoints (NEW)

#### Tasks

- [ ] Implement niche CRUD service
- [ ] Create niche routes
- [ ] Add niche statistics endpoint
- [ ] Add collection trigger endpoint
- [ ] Write unit tests

#### Endpoints (Day 5)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/niches` | List all niches |
| POST | `/api/niches` | Create a new niche |
| GET | `/api/niches/:slug` | Get niche details |
| PATCH | `/api/niches/:slug` | Update niche |
| DELETE | `/api/niches/:slug` | Delete niche (soft delete) |
| GET | `/api/niches/:slug/stats` | Get niche statistics |
| POST | `/api/niches/:slug/collect` | Trigger collection for niche |

#### Niche Response Format

```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "Video Editing Apps",
    "slug": "video-editing-apps",
    "description": "AI-powered video editing tools",
    "color": "#8B5CF6",
    "icon": "🎬",
    "keywords": ["video editing ai", "opus clip", "descript"],
    "countries": ["US", "BR"],
    "platforms": ["instagram", "facebook"],
    "stats": {
      "total_ads": 342,
      "active_ads": 287,
      "saved_ads": 24,
      "unique_pages": 45,
      "last_collection": "2026-01-29T14:30:00Z"
    },
    "created_at": "2026-01-15T10:00:00Z"
  }
}
```

#### Niche List Response

```json
{
  "success": true,
  "data": {
    "niches": [
      {
        "id": 1,
        "name": "Video Editing Apps",
        "slug": "video-editing-apps",
        "color": "#8B5CF6",
        "icon": "🎬",
        "stats": {
          "total_ads": 342,
          "saved_ads": 24
        }
      },
      {
        "id": 2,
        "name": "CRMs",
        "slug": "crms",
        "color": "#10B981",
        "icon": "📊",
        "stats": {
          "total_ads": 187,
          "saved_ads": 12
        }
      }
    ]
  }
}
```

#### Deliverables

- `backend/app/services/niche_service.py`
- `backend/app/routes/niches.py`
- Unit tests for niche functionality

---

### Day 6: Search Endpoint (Niche-Scoped)

#### Tasks

- [ ] Implement search service with filtering (niche-scoped)
- [ ] Create search route with query parameters
- [ ] Add pagination support
- [ ] Add sorting options
- [ ] Write unit tests

#### Endpoints (Day 6)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/niches/:slug/ads/search` | Search ads within a niche |

#### Query Parameters

```
GET /api/niches/:slug/ads/search?
    q=video editing ai          # Search term (keyword)
    platform=instagram,facebook # Filter by platform
    country=US,BR               # Filter by country
    status=active               # active, inactive, all
    min_days=7                  # Minimum days active
    max_days=                   # Maximum days active
    cta=learn_more              # Filter by CTA type
    date_from=2025-01-01        # Start date filter
    date_to=2025-01-30          # End date filter
    page_id=                    # Filter by specific page
    sort=days_active            # Sort field
    order=desc                  # Sort order
    page=1                      # Page number
    per_page=20                 # Results per page
```

#### Response Format

```json
{
  "success": true,
  "data": {
    "niche": {
      "slug": "video-editing-apps",
      "name": "Video Editing Apps"
    },
    "ads": [
      {
        "id": 1,
        "ad_id": "abc123",
        "page_name": "OpusClip",
        "headline": "Turn long videos into viral clips",
        "body": "Stop spending hours editing...",
        "thumbnail_url": "https://...",
        "platforms": ["instagram", "facebook"],
        "days_active": 67,
        "is_active": true,
        "cta_detected": "learn_more",
        "start_date": "2025-12-01",
        "variant_count": 4,
        "is_saved": true
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 20,
      "total": 247,
      "total_pages": 13
    },
    "filters_applied": {
      "q": "video editing ai",
      "status": "active",
      "min_days": 7
    }
  }
}
```

#### Deliverables

- `backend/app/services/ad_service.py` (niche-aware)
- `backend/app/routes/ads.py` (niche-scoped)
- Unit tests for search functionality

---

### Day 7: Detail & Related Ads Endpoints

#### Tasks

- [ ] Implement ad detail endpoint (niche-scoped)
- [ ] Implement variant detection service
- [ ] Create related ads endpoint
- [ ] Add page ads endpoint
- [ ] Write unit tests

#### Endpoints (Day 7)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/niches/:slug/ads/:id` | Get ad details |
| GET | `/api/niches/:slug/ads/:id/related` | Get related ads/variants |
| GET | `/api/niches/:slug/pages` | List pages in niche |
| GET | `/api/niches/:slug/pages/:page_id/ads` | Get ads from a page |
| POST | `/api/niches/:slug/pages/:page_id/competitor` | Mark page as competitor |

#### Variant Detection Logic

```python
def find_related_ads(niche_id: int, ad_id: int) -> List[Ad]:
    """
    Find related ads (variants) within the same niche based on:
    1. Same page_id (required)
    2. Same niche_id (required)
    3. AND at least ONE of:
       - Launched within 14 days of each other
       - Text similarity > 70%
       - Same CTA type
       - Same landing page domain
    """
```

#### Related Ads Response

```json
{
  "success": true,
  "data": {
    "niche_slug": "video-editing-apps",
    "ad_id": 1,
    "related_count": 4,
    "insights": {
      "longest_running_days": 67,
      "newest_days_ago": 12,
      "common_cta": "learn_more",
      "testing_pattern": "Headlines differ (A/B testing hooks)"
    },
    "variants": [
      {
        "id": 1,
        "headline": "Turn long videos into viral clips",
        "days_active": 67,
        "is_longest": true,
        "is_newest": false,
        "platforms": ["instagram", "facebook"]
      },
      {
        "id": 5,
        "headline": "AI finds your best clips automatically",
        "days_active": 12,
        "is_longest": false,
        "is_newest": true,
        "platforms": ["instagram"]
      }
    ]
  }
}
```

#### Deliverables

- `backend/app/services/variant_service.py`
- Ad detail and related ads routes (niche-scoped)
- Unit tests

---

### Day 8: Saved Ads Endpoints (Niche-Scoped)

#### Tasks

- [ ] Implement saved ads operations (updates `is_saved` flag on ads)
- [ ] Create saved ads routes
- [ ] Add notes and tags support
- [ ] Write unit tests
- [ ] API documentation

#### Endpoints (Day 8)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/niches/:slug/saved` | Get saved ads in niche (where is_saved=true) |
| POST | `/api/niches/:slug/ads/:id/save` | Save an ad (set is_saved=true) |
| DELETE | `/api/niches/:slug/ads/:id/save` | Unsave an ad (set is_saved=false) |
| PATCH | `/api/niches/:slug/ads/:id/save` | Update saved notes/tags |

#### Saved Ad Response

Since saved status is denormalized into the ads table, the response includes the full ad with saved fields:

```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "niche_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "meta_ad_id": "abc123",
    "page_name": "OpusClip",
    "page_id": "123456789",
    "page_verified": true,
    "headline": "Turn long videos into viral clips",
    "body": "Stop spending hours editing...",
    "days_active": 67,
    "is_active": true,
    "platforms": ["instagram", "facebook"],
    "cta_detected": "learn_more",
    "is_saved": true,
    "saved_at": "2026-01-28T10:30:00Z",
    "saved_notes": "Great hook, consider using this angle",
    "saved_tags": ["winning-hook", "competitor", "review-later"],
    "created_at": "2026-01-15T08:00:00Z",
    "updated_at": "2026-01-28T10:30:00Z"
  }
}
```

#### Save/Unsave Request

```json
// POST /api/niches/:slug/ads/:id/save
{
  "notes": "Great hook, consider using this angle",
  "tags": ["winning-hook", "competitor"]
}

// Response: Full ad object with is_saved=true
```

#### Deliverables

- `backend/app/routes/saved.py` (niche-scoped, operates on ads table)
- Complete API documentation
- All backend unit tests passing

---

## Phase 3: Frontend Foundation

**Duration:** Days 9-12 (shifted by 1 day)

### Day 9: Vue Project Setup

#### Tasks

- [ ] Initialize Vue 3 project with Vite
- [ ] Install and configure Vue Router
- [ ] Install and configure Pinia (state management)
- [ ] Set up API service layer (axios)
- [ ] Configure proxy for backend API

#### Dependencies

```json
{
  "dependencies": {
    "vue": "^3.4.0",
    "vue-router": "^4.2.0",
    "pinia": "^2.1.0",
    "axios": "^1.6.0"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.0.0",
    "vite": "^5.0.0",
    "sass": "^1.69.0"
  }
}
```

#### Router Configuration (with Niches)

```javascript
// router/index.js
const routes = [
  {
    path: '/',
    name: 'NicheSelector',
    component: () => import('@/views/NicheSelectorView.vue')
  },
  {
    path: '/niches/new',
    name: 'CreateNiche',
    component: () => import('@/views/CreateNicheView.vue')
  },
  {
    path: '/n/:nicheSlug',
    name: 'NicheWorkspace',
    component: () => import('@/views/NicheWorkspaceView.vue'),
    children: [
      {
        path: '',
        name: 'NicheSearch',
        component: () => import('@/views/SearchView.vue')
      },
      {
        path: 'saved',
        name: 'NicheSaved',
        component: () => import('@/views/SavedView.vue')
      },
      {
        path: 'settings',
        name: 'NicheSettings',
        component: () => import('@/views/NicheSettingsView.vue')
      }
    ]
  }
]
```

#### Deliverables

- Working Vue project
- Router configuration with niche routes
- Pinia store setup
- API service layer

---

### Day 10: Niche Selector & Desktop Layout

#### Tasks

- [ ] Create NicheSelector view (landing page)
- [ ] Create NicheCard component
- [ ] Create CreateNiche view/modal
- [ ] Implement 3-column desktop layout for workspace
- [ ] Add header with niche indicator

#### Niche Selector Layout

```
┌──────────────────────────────────────────────────────────────────┐
│  HEADER                                    MetAds        [+ New] │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  YOUR NICHES                                                     │
│  ─────────────────────────────────────────────────────────────   │
│                                                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │ 🎬              │  │ 📊              │  │ 🗳️              │  │
│  │ Video Editing   │  │ CRMs            │  │ Election 2026   │  │
│  │ Apps            │  │                 │  │                 │  │
│  │                 │  │                 │  │                 │  │
│  │ 342 ads · 24 ⭐ │  │ 187 ads · 12 ⭐ │  │ 89 ads · 8 ⭐   │  │
│  │ Last: 2h ago    │  │ Last: 1d ago    │  │ Last: 3d ago    │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
│                                                                  │
│  ┌─────────────────┐                                            │
│  │       +         │                                            │
│  │  Create New     │                                            │
│  │     Niche       │                                            │
│  └─────────────────┘                                            │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

#### Workspace Layout (within Niche)

```
┌──────────────────────────────────────────────────────────────────┐
│  [← Niches]  🎬 Video Editing Apps              [⚙️]  [Collect]  │
├────────────────┬─────────────────────┬───────────────────────────┤
│  SearchPanel   │  ResultsList        │  AdDetail                 │
│  (250px fixed) │  (350px fixed)      │  (flex: 1, min 400px)     │
│                │                     │                           │
│  - Search box  │  - Result count     │  - Creative preview       │
│  - Filters     │  - Sort dropdown    │  - Page info              │
│                │  - Ad cards         │  - Metrics                │
│                │  - Load more        │  - Ad copy                │
│                │                     │  - Actions                │
└────────────────┴─────────────────────┴───────────────────────────┘
```

#### Deliverables

- `frontend/src/views/NicheSelectorView.vue`
- `frontend/src/views/CreateNicheView.vue`
- `frontend/src/views/NicheWorkspaceView.vue`
- `frontend/src/components/niches/NicheCard.vue`
- `frontend/src/components/niches/NicheForm.vue`
- `frontend/src/components/layout/WorkspaceHeader.vue`

---

### Day 11: Mobile Layout

#### Tasks

- [ ] Implement responsive breakpoints
- [ ] Create mobile niche selector
- [ ] Create mobile bottom tab navigation (within niche)
- [ ] Adapt SearchPanel for mobile (full screen)
- [ ] Adapt ResultsList for mobile (full screen)
- [ ] Create mobile AdDetail overlay
- [ ] Add touch-friendly interactions

#### Mobile Views

```
Mobile Breakpoint: < 768px

NICHE SELECTOR (Mobile)
┌─────────────────────────────────┐
│  ≡  MetAds              [+ New] │
├─────────────────────────────────┤
│  YOUR NICHES                    │
│                                 │
│  ┌───────────────────────────┐  │
│  │ 🎬 Video Editing Apps     │  │
│  │ 342 ads · 24 saved        │  │
│  │ Last collection: 2h ago   │  │
│  └───────────────────────────┘  │
│                                 │
│  ┌───────────────────────────┐  │
│  │ 📊 CRMs                   │  │
│  │ 187 ads · 12 saved        │  │
│  └───────────────────────────┘  │
│                                 │
└─────────────────────────────────┘

WORKSPACE (Mobile - within niche)
Tab 1: Search (full screen form)
Tab 2: Results (scrollable list)
Tab 3: Saved (saved ads list)

Ad Detail: Full screen overlay (slides up)
Related Ads: Slide-in panel from right
```

#### Deliverables

- `frontend/src/components/layout/MobileNav.vue`
- `frontend/src/components/niches/NicheListMobile.vue`
- Responsive CSS for all components
- Mobile-specific view adaptations

---

### Day 12: Styling & Design System

#### Tasks

- [ ] Define CSS custom properties (colors, spacing, typography)
- [ ] Add niche color support in design system
- [ ] Create base component styles
- [ ] Implement card component styles
- [ ] Add loading states and skeletons
- [ ] Add transitions and animations
- [ ] Test across screen sizes

#### Design Tokens

```css
:root {
  /* Colors */
  --color-primary: #2563eb;
  --color-primary-light: #dbeafe;
  --color-success: #22c55e;
  --color-warning: #f59e0b;
  --color-error: #ef4444;
  --color-gray-50: #f9fafb;
  --color-gray-100: #f3f4f6;
  --color-gray-200: #e5e7eb;
  --color-gray-500: #6b7280;
  --color-gray-700: #374151;
  --color-gray-900: #111827;

  /* Niche Colors (examples) */
  --niche-purple: #8B5CF6;
  --niche-green: #10B981;
  --niche-blue: #3B82F6;
  --niche-orange: #F59E0B;
  --niche-pink: #EC4899;
  --niche-teal: #14B8A6;

  /* Typography */
  --font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --font-size-xs: 12px;
  --font-size-sm: 14px;
  --font-size-base: 16px;
  --font-size-lg: 18px;

  /* Spacing */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-6: 24px;
  --space-8: 32px;

  /* Borders */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;

  /* Shadows */
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
  --shadow-md: 0 4px 6px rgba(0,0,0,0.1);
}
```

#### Deliverables

- `frontend/src/assets/styles/variables.scss`
- `frontend/src/assets/styles/base.scss`
- `frontend/src/assets/styles/components.scss`
- Polished visual design across all views

---

## Phase 4: Frontend Features

**Duration:** Days 13-17 (shifted by 1 day)

### Day 13: Niche Management & Search

#### Tasks

- [ ] Implement niche store (Pinia)
- [ ] Create niche CRUD functionality in UI
- [ ] Implement search form with all filter options
- [ ] Create search store (niche-scoped)
- [ ] Connect search form to API
- [ ] Add filter chips display

#### Niche Store

```javascript
// stores/niches.js
export const useNicheStore = defineStore('niches', {
  state: () => ({
    niches: [],
    currentNiche: null,
    loading: false
  }),
  getters: {
    getNicheBySlug: (state) => (slug) =>
      state.niches.find(n => n.slug === slug)
  },
  actions: {
    async fetchNiches() { /* ... */ },
    async createNiche(data) { /* ... */ },
    async updateNiche(slug, data) { /* ... */ },
    async deleteNiche(slug) { /* ... */ },
    setCurrentNiche(slug) { /* ... */ }
  }
})
```

#### Search Store (Niche-Scoped)

```javascript
// stores/search.js
export const useSearchStore = defineStore('search', {
  state: () => ({
    query: '',
    filters: {
      platform: 'all',
      country: [],
      status: 'active',
      minDays: 7,
      maxDays: null,
      dateFrom: null,
      dateTo: null
    },
    sort: {
      field: 'days_active',
      order: 'desc'
    }
  }),
  actions: {
    async search(nicheSlug) { /* ... */ },
    resetFilters() { /* ... */ }
  }
})
```

#### Deliverables

- `frontend/src/stores/niches.js`
- `frontend/src/stores/search.js`
- `frontend/src/components/search/SearchForm.vue`
- `frontend/src/components/search/FilterChips.vue`
- Working niche selection and search functionality

---

### Day 14: Results List

#### Tasks

- [ ] Create AdCard component
- [ ] Implement results list with virtual scrolling (if needed)
- [ ] Add card hover/selected states
- [ ] Implement sort dropdown
- [ ] Add "Load more" pagination
- [ ] Create loading skeleton cards
- [ ] Show niche context in results

#### AdCard Component

```vue
<!-- Components to build -->
- AdCard.vue (individual result card)
- AdCardSkeleton.vue (loading state)
- ResultsHeader.vue (count + sort + niche indicator)
- LoadMoreButton.vue
```

#### Deliverables

- `frontend/src/components/results/AdCard.vue`
- `frontend/src/components/results/AdCardSkeleton.vue`
- `frontend/src/stores/results.js`
- Fully functional results list

---

### Day 15: Ad Detail Panel

#### Tasks

- [ ] Create creative preview component (image/video)
- [ ] Build page info section
- [ ] Build metrics display (days active, platforms, status)
- [ ] Build ad copy section (headline, body, CTA)
- [ ] Add action buttons (View on Meta, Save to Niche, Copy)
- [ ] Implement "Related Ads" link

#### Detail Sections

```
┌─────────────────────────────────────┐
│  CREATIVE PREVIEW                   │
│  (Image/Video with aspect ratio)    │
├─────────────────────────────────────┤
│  PAGE INFO                          │
│  OpusClip · @opusclip · Verified    │
│  [★ Mark as Competitor]             │
├─────────────────────────────────────┤
│  METRICS                            │
│  Started: Dec 1, 2025               │
│  Days Active: 67                    │
│  Platforms: IG, FB                  │
│  Status: ● Active                   │
│  Related Ads: [4 variants →]        │
├─────────────────────────────────────┤
│  AD COPY                            │
│  Headline: "..."                    │
│  Body: "..."                        │
│  CTA: Learn More                    │
│  Link: opus.pro/get-started         │
├─────────────────────────────────────┤
│  [View on Meta]  [Save]  [Copy]     │
└─────────────────────────────────────┘
```

#### Deliverables

- `frontend/src/components/detail/CreativePreview.vue`
- `frontend/src/components/detail/PageInfo.vue`
- `frontend/src/components/detail/AdMetrics.vue`
- `frontend/src/components/detail/AdCopy.vue`
- `frontend/src/components/detail/AdActions.vue`

---

### Day 16: Related Ads / Variants

#### Tasks

- [ ] Create RelatedAdsPanel component
- [ ] Implement variant insights summary
- [ ] Create VariantCard component
- [ ] Add badges (LONGEST, NEWEST)
- [ ] Mobile slide-in panel behavior
- [ ] Connect to API endpoint

#### Variant Insights

```
┌─────────────────────────────────────┐
│  VARIANT INSIGHTS                   │
│  in "Video Editing Apps" niche      │
│  ─────────────────────────────────  │
│  Longest running: 67 days           │
│  All use same CTA: Learn More       │
│  Headlines differ (A/B testing)     │
├─────────────────────────────────────┤
│  VARIANTS (4)                       │
│  ┌─────────────────────────────────┐│
│  │ ★ LONGEST                       ││
│  │ "Turn long videos into..."      ││
│  │ 67 days · IG FB                 ││
│  └─────────────────────────────────┘│
│  ┌─────────────────────────────────┐│
│  │ ✦ NEWEST                        ││
│  │ "AI finds your best clips..."   ││
│  │ 12 days · IG                    ││
│  └─────────────────────────────────┘│
└─────────────────────────────────────┘
```

#### Deliverables

- `frontend/src/components/detail/RelatedAdsPanel.vue`
- `frontend/src/components/detail/VariantInsights.vue`
- `frontend/src/components/detail/VariantCard.vue`

---

### Day 17: Saved Ads & Niche Settings

#### Tasks

- [ ] Create SavedAds view/tab (niche-scoped)
- [ ] Implement save/unsave functionality with tags
- [ ] Add saved indicator to cards
- [ ] Create NicheSettings view (edit keywords, colors, etc.)
- [ ] Create empty states (no results, no saved)
- [ ] Implement error states and error handling
- [ ] Add toast notifications

#### Niche Settings View

```
┌─────────────────────────────────────┐
│  ← Back to Workspace                │
│                                     │
│  NICHE SETTINGS                     │
│  Video Editing Apps                 │
│  ─────────────────────────────────  │
│                                     │
│  Name                               │
│  ┌─────────────────────────────────┐│
│  │ Video Editing Apps              ││
│  └─────────────────────────────────┘│
│                                     │
│  Description                        │
│  ┌─────────────────────────────────┐│
│  │ AI-powered video editing tools  ││
│  └─────────────────────────────────┘│
│                                     │
│  Color                              │
│  [●] [●] [●] [●] [●] [●]           │
│                                     │
│  Keywords (for collection)          │
│  ┌─────────────────────────────────┐│
│  │ video editing ai                ││
│  │ opus clip                       ││
│  │ descript                        ││
│  │ [+ Add keyword]                 ││
│  └─────────────────────────────────┘│
│                                     │
│  Default Countries                  │
│  [US ×] [BR ×] [+ Add]             │
│                                     │
│  ─────────────────────────────────  │
│  [Save Changes]  [Delete Niche]     │
└─────────────────────────────────────┘
```

#### Empty & Error States

```
NO RESULTS                    ERROR STATE
┌─────────────────────────┐   ┌─────────────────────────┐
│         🔍              │   │         ⚠️              │
│   No ads found in       │   │   Something went wrong  │
│   "Video Editing Apps"  │   │   [Try Again]           │
│   Try adjusting filters │   │                         │
│   [Clear Filters]       │   │                         │
└─────────────────────────┘   └─────────────────────────┘

NO SAVED ADS IN NICHE
┌─────────────────────────┐
│         ⭐              │
│   No saved ads yet in   │
│   "Video Editing Apps"  │
│   [Start Searching]     │
└─────────────────────────┘
```

#### Saved Ads Store

Since saved status is denormalized into ads, the saved store filters ads by `is_saved=true`:

```javascript
// stores/saved.js
export const useSavedStore = defineStore('saved', {
  state: () => ({
    savedAds: [],
    loading: false
  }),
  actions: {
    async fetchSavedAds(nicheSlug) {
      // GET /api/niches/:slug/saved
      // Returns ads where is_saved=true
    },
    async saveAd(nicheSlug, adId, notes = '', tags = []) {
      // POST /api/niches/:slug/ads/:id/save
      // Updates ad.is_saved=true, ad.saved_notes, ad.saved_tags
    },
    async unsaveAd(nicheSlug, adId) {
      // DELETE /api/niches/:slug/ads/:id/save
      // Updates ad.is_saved=false
    },
    async updateSavedNotes(nicheSlug, adId, notes, tags) {
      // PATCH /api/niches/:slug/ads/:id/save
    }
  }
})
```

#### Deliverables

- `frontend/src/views/SavedView.vue` (niche-scoped)
- `frontend/src/views/NicheSettingsView.vue`
- `frontend/src/stores/saved.js` (filters ads by is_saved)
- `frontend/src/components/common/EmptyState.vue`
- `frontend/src/components/common/ErrorState.vue`
- `frontend/src/components/common/Toast.vue`
- `frontend/src/components/detail/SaveNotesModal.vue`

---

## Phase 5: Integration & Polish

**Duration:** Days 18-21 (shifted by 1 day)

### Day 18: End-to-End Testing

#### Tasks

- [ ] Test complete user flows
- [ ] Test niche creation → collection → search → save flow
- [ ] Test switching between niches
- [ ] Test save/unsave functionality
- [ ] Test filter combinations
- [ ] Test mobile responsiveness
- [ ] Fix bugs discovered during testing

#### Test Scenarios

1. Create new niche "Test Niche" → Add keywords → Trigger collection → View results
2. Switch between niches → Verify data isolation
3. Search in "Video Editing Apps" → View ad → View related → Save ad
4. Apply multiple filters → Clear filters → Search again
5. Mobile: Navigate between niches → Open workspace → View ad detail
6. Edit niche settings → Verify changes persist
7. Empty state: Search with no results → Clear filters
8. Error handling: API timeout → Retry

#### Deliverables

- Bug fixes
- Stable end-to-end flows

---

### Day 19: Performance Optimization

#### Tasks

- [ ] Implement pagination/infinite scroll
- [ ] Add debounce to search input
- [ ] Optimize API queries (indexes, query optimization)
- [ ] Lazy load images
- [ ] Add request caching where appropriate
- [ ] Test with larger dataset (500+ ads across multiple niches)

#### Deliverables

- Smooth performance with large datasets
- Optimized database queries

---

### Day 20: Data Pipeline Integration

#### Tasks

- [ ] Create collection management CLI (niche-aware)
- [ ] Add scheduled collection script per niche
- [ ] Implement incremental updates (don't duplicate ads)
- [ ] Add collection status tracking per niche
- [ ] Test full pipeline: Collect → Parse → Store → Display
- [ ] Add "Collect Now" button in UI

#### CLI Commands (Final)

```bash
# Niche management
python run.py niche create --name "Video Editing Apps" --keywords "video editing ai,opus clip"
python run.py niche list
python run.py niche stats --niche "video-editing-apps"
python run.py niche delete --niche "video-editing-apps"

# Collection
python run.py collect --niche "video-editing-apps" --limit 100
python run.py collect --niche "video-editing-apps" --keyword "new keyword" --limit 50
python run.py collect --all --limit 50  # All active niches

# Updates
python run.py update --niche "video-editing-apps"  # Refresh status/days
python run.py update --all

# Global stats
python run.py stats
```

#### Deliverables

- Working CLI commands (niche-aware)
- Collection pipeline integrated with niches
- UI trigger for collection

---

### Day 21: Documentation & Wrap-up

#### Tasks

- [ ] Write README with setup instructions
- [ ] Document API endpoints (with niche context)
- [ ] Create local development guide
- [ ] Add inline code comments where needed
- [ ] Final testing and bug fixes
- [ ] Tag v0.1.0 release

#### README Sections

```markdown
# MetAds

## Quick Start
## Requirements
## Installation
## Running Locally
## Project Structure
## Concepts
  ### Niches
  ### Ads
  ### Variants
## API Documentation
## Data Collection
## CLI Commands
## Contributing
```

#### Deliverables

- Complete README.md
- API documentation
- Working first draft (MVP) with niche support

---

## API Endpoint Summary

| Method | Endpoint | Description | Phase |
|--------|----------|-------------|-------|
| GET | `/api/health` | Health check | 2 |
| GET | `/api/stats` | Global database statistics | 2 |
| **Niches** |  |  |  |
| GET | `/api/niches` | List all niches | 2 |
| POST | `/api/niches` | Create a new niche | 2 |
| GET | `/api/niches/:slug` | Get niche details | 2 |
| PATCH | `/api/niches/:slug` | Update niche | 2 |
| DELETE | `/api/niches/:slug` | Delete niche | 2 |
| GET | `/api/niches/:slug/stats` | Get niche statistics | 2 |
| POST | `/api/niches/:slug/collect` | Trigger collection | 2 |
| **Ads (Niche-Scoped)** |  |  |  |
| GET | `/api/niches/:slug/ads/search` | Search ads in niche | 2 |
| GET | `/api/niches/:slug/ads/:id` | Get ad details | 2 |
| GET | `/api/niches/:slug/ads/:id/related` | Get related ads/variants | 2 |
| **Pages (Niche-Scoped)** |  |  |  |
| GET | `/api/niches/:slug/pages` | List pages in niche | 2 |
| GET | `/api/niches/:slug/pages/:page_id/ads` | Get ads from a page | 2 |
| POST | `/api/niches/:slug/pages/:page_id/competitor` | Mark as competitor | 2 |
| **Saved Ads (Niche-Scoped)** |  |  |  |
| GET | `/api/niches/:slug/saved` | Get saved ads (is_saved=true) | 2 |
| POST | `/api/niches/:slug/ads/:id/save` | Save an ad | 2 |
| DELETE | `/api/niches/:slug/ads/:id/save` | Unsave an ad | 2 |
| PATCH | `/api/niches/:slug/ads/:id/save` | Update saved notes/tags | 2 |

---

## Component Inventory

### Niche Components
- `NicheCard.vue`
- `NicheForm.vue`
- `NicheListMobile.vue`
- `NicheColorPicker.vue`
- `KeywordInput.vue`

### Layout Components
- `AppHeader.vue`
- `WorkspaceHeader.vue`
- `MobileNav.vue`
- `MainView.vue`

### Search Components
- `SearchPanel.vue`
- `SearchForm.vue`
- `FilterChips.vue`

### Results Components
- `ResultsList.vue`
- `ResultsHeader.vue`
- `AdCard.vue` (includes saved indicator)
- `AdCardSkeleton.vue`
- `LoadMoreButton.vue`

### Detail Components
- `AdDetail.vue`
- `CreativePreview.vue`
- `PageInfo.vue`
- `AdMetrics.vue`
- `AdCopy.vue`
- `AdActions.vue` (save/unsave, notes, tags)
- `RelatedAdsPanel.vue`
- `VariantInsights.vue`
- `VariantCard.vue`
- `SaveNotesModal.vue` (for editing saved notes/tags)

### Common Components
- `EmptyState.vue`
- `ErrorState.vue`
- `Toast.vue`
- `Badge.vue`
- `Button.vue`
- `Dropdown.vue`
- `Modal.vue`
- `TagInput.vue`

## Model Files

### Backend Models (SQLAlchemy + DynamoDB-ready)
- `backend/app/models/niche.py`
- `backend/app/models/ad.py` (includes denormalized saved fields)
- `backend/app/models/page.py`
- `backend/app/models/niche_page.py`
- `backend/app/models/collection_run.py`
- `backend/app/utils/ids.py` (UUID generation)

---

## Milestones

| Milestone | Target Date | Description |
|-----------|-------------|-------------|
| M1: Database Ready | Day 3 | Schema with niches, models, sample data |
| M2: API Complete | Day 8 | All endpoints working (including niches) |
| M3: UI Foundation | Day 12 | Layouts, niche selector, styling |
| M4: Feature Complete | Day 17 | All features implemented |
| M5: MVP Ready | Day 21 | First draft complete |

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Meta API rate limits | Implement caching, batch collection per niche |
| Complex variant detection | Start with simple temporal matching, iterate |
| Mobile layout complexity | Use established patterns from wireframes |
| Scope creep | Stick to MVP features, defer enhancements |
| Niche data isolation | Clear foreign key relationships, scoped queries |

---

## Post-MVP Enhancements (Future)

- [ ] User authentication (multi-user with personal niches)
- [ ] Export to CSV/PDF (per niche)
- [ ] Advanced analytics dashboard per niche
- [ ] Email alerts for new competitor ads in niche
- [ ] Chrome extension for quick saves to specific niche
- [ ] Image similarity detection for variants
- [ ] Niche templates (pre-configured for common industries)
- [ ] Niche sharing/collaboration
- [ ] Deployment to cloud (AWS/Vercel)

---

## User Flow with Niches

```
                         ┌─────────────────┐
                         │  NICHE SELECTOR │
                         │  (Landing Page) │
                         └────────┬────────┘
                                  │
              ┌───────────────────┼───────────────────┐
              │                   │                   │
              ▼                   ▼                   ▼
       ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
       │   Niche 1   │    │   Niche 2   │    │  + Create   │
       │   Video Ed  │    │    CRMs     │    │    New      │
       └──────┬──────┘    └──────┬──────┘    └──────┬──────┘
              │                  │                   │
              └────────┬─────────┘                   │
                       │                             ▼
                       ▼                     ┌─────────────┐
              ┌─────────────────┐            │ Create Form │
              │    WORKSPACE    │            │  - Name     │
              │  (3-col layout) │            │  - Keywords │
              └────────┬────────┘            │  - Color    │
                       │                     └─────────────┘
       ┌───────────────┼───────────────┐
       │               │               │
       ▼               ▼               ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│   SEARCH    │ │   SAVED     │ │  SETTINGS   │
│   (in niche)│ │  (in niche) │ │  (niche)    │
└──────┬──────┘ └─────────────┘ └─────────────┘
       │
       ▼
┌─────────────┐
│   RESULTS   │
│  (in niche) │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  AD DETAIL  │
│  + Related  │
│  + Save     │
└─────────────┘
```

---

## DynamoDB Migration Path

The schema is designed for easy migration from SQLite to DynamoDB. Here's the mapping:

### Table Mapping

| SQLite Table | DynamoDB Table | Partition Key | Sort Key |
|--------------|----------------|---------------|----------|
| `niches` | `metads-niches` | `niche_id` | `"METADATA"` |
| `ads` | `metads-ads` | `niche_id` | `AD#<meta_ad_id>` |
| `pages` | `metads-pages` | `page_id` | `"METADATA"` |
| `niche_pages` | `metads-niche-pages` | `niche_id` | `PAGE#<page_id>` |
| `collection_runs` | `metads-collection-runs` | `niche_id` | `RUN#<timestamp>#<uuid>` |

### Index Mapping

| SQLite Index | DynamoDB GSI | Purpose |
|--------------|--------------|---------|
| `slug` on niches | `slug-index` | Get niche by slug |
| `niche_id + days_active` on ads | `niche-days-gsi` | Sort by performance |
| `niche_id + page_id` on ads | `niche-page-gsi` | Get ads by page |
| `niche_id + is_saved` on ads | `niche-saved-gsi` | Get saved ads |
| `niche_id + cta_detected` on ads | `niche-cta-gsi` | Filter by CTA |

### Code Changes for Migration

```python
# SQLite (current)
from sqlalchemy import create_engine
db = create_engine('sqlite:///data/ads.db')

# DynamoDB (future)
import boto3
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('metads-ads')

# Query pattern remains similar:
# SQLite: SELECT * FROM ads WHERE niche_id = ? AND is_saved = true
# DynamoDB: table.query(KeyConditionExpression=Key('niche_id').eq(niche_id),
#                       FilterExpression=Attr('is_saved').eq(True))
```

### Data Type Mapping

| SQLite Type | DynamoDB Type | Notes |
|-------------|---------------|-------|
| `UUID` (VARCHAR) | `S` (String) | Same format |
| `VARCHAR(n)` | `S` (String) | Same |
| `TEXT` | `S` (String) | Same |
| `INTEGER` | `N` (Number) | Same |
| `BOOLEAN` | `BOOL` | Same |
| `JSON` (text) | `L` (List) or `M` (Map) | Native types |
| ISO8601 dates (VARCHAR) | `S` (String) | Same format |

### Migration Checklist

- [ ] Create DynamoDB tables with correct key schema
- [ ] Create Global Secondary Indexes
- [ ] Replace SQLAlchemy with boto3 DynamoDB client
- [ ] Convert JSON text fields to native Lists/Maps
- [ ] Update query logic for DynamoDB patterns
- [ ] Test all access patterns
- [ ] Migrate data from SQLite to DynamoDB

---

*Document Version: 1.2*
*Created: January 30, 2026*
*Updated: January 30, 2026 - DynamoDB-compatible schema*
*Status: Planning*
