# MetAds Implementation Plan v2

## Table of Contents

1. [Changelog from v1](#changelog-from-v1)
2. [Project Overview](#project-overview)
   - [Tech Stack](#tech-stack)
   - [Architecture](#architecture)
   - [Authentication Flow](#authentication-flow)
   - [Data Organization with Niches](#data-organization-with-niches-user-scoped)
3. [Phase 1: Foundation, Database & Authentication (Days 1-4)](#phase-1-foundation-database--authentication)
   - [Day 1: Project Structure & Dependencies](#day-1-project-structure--dependencies)
   - [Day 2: Clerk Integration (Backend)](#day-2-clerk-integration-backend)
   - [Day 3: Database Models (with User Scoping)](#day-3-database-models-with-user-scoping)
   - [Day 4: Data Collection Integration](#day-4-data-collection-integration)
4. [Phase 2: Flask REST API Backend (Days 5-9)](#phase-2-flask-rest-api-backend)
   - [Day 5: Flask App Setup](#day-5-flask-app-setup)
   - [Day 6: Niche Endpoints (User-Scoped)](#day-6-niche-endpoints-user-scoped)
   - [Day 7: Search Endpoint (Niche-Scoped)](#day-7-search-endpoint-niche-scoped)
   - [Day 8: Detail & Related Ads Endpoints](#day-8-detail--related-ads-endpoints)
   - [Day 9: Saved Ads Endpoints (Niche-Scoped)](#day-9-saved-ads-endpoints-niche-scoped)
5. [Phase 3: Frontend Foundation (Days 10-14)](#phase-3-frontend-foundation)
   - [Day 10: Vue Project Setup with Clerk](#day-10-vue-project-setup-with-clerk)
   - [Day 11: Auth Views & Niche Selector](#day-11-auth-views--niche-selector)
   - [Day 12: Desktop Layout](#day-12-desktop-layout)
   - [Day 13: Mobile Layout](#day-13-mobile-layout)
   - [Day 14: Styling & Design System](#day-14-styling--design-system)
6. [Phase 4: Frontend Features (Days 15-19)](#phase-4-frontend-features)
   - [Day 15: Niche Management & Search](#day-15-niche-management--search)
   - [Day 16: Results List](#day-16-results-list)
   - [Day 17: Ad Detail Panel](#day-17-ad-detail-panel)
   - [Day 18: Related Ads / Variants](#day-18-related-ads--variants)
   - [Day 19: Saved Ads & Niche Settings](#day-19-saved-ads--niche-settings)
7. [Phase 5: Integration & Polish (Days 20-23)](#phase-5-integration--polish)
   - [Day 20: End-to-End Testing](#day-20-end-to-end-testing)
   - [Day 21: Performance Optimization](#day-21-performance-optimization)
   - [Day 22: Data Pipeline Integration](#day-22-data-pipeline-integration)
   - [Day 23: Documentation & Wrap-up](#day-23-documentation--wrap-up)
8. [API Endpoint Summary](#api-endpoint-summary)
9. [Component Inventory](#component-inventory)
10. [Model Files](#model-files)
11. [Milestones](#milestones)
12. [Risk Mitigation](#risk-mitigation)
13. [Post-MVP Enhancements (Future)](#post-mvp-enhancements-future)
14. [Clerk Setup Checklist](#clerk-setup-checklist)

---

## Changelog from v1
- **Added Clerk Authentication** throughout all phases
- **Added `user_id`** to database schema for multi-tenancy
- **Added auth endpoints** and middleware to backend
- **Added login/signup flows** to frontend
- **Extended timeline** by 2 days (now 23 days) to accommodate auth implementation

---

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
| **Authentication** | **Clerk** (OAuth, social logins, session management) |
| **Database** | SQLite (local development) |
| **Data Collection** | Meta Ad Library API + custom collectors/parsers |

### Architecture

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│  Meta Ad        │      │  Flask Backend  │      │  Vue Frontend   │
│  Library API    │ ───► │  (REST API)     │ ◄─── │  (SPA)          │
└─────────────────┘      └────────┬────────┘      └────────┬────────┘
        │                         │                        │
        │                ┌────────▼────────┐      ┌────────▼────────┐
        │                │    SQLite       │      │     Clerk       │
        │                │    Database     │      │   (Auth Provider)│
        │                └─────────────────┘      └─────────────────┘
        │                         ▲                        │
        │                         │                        │
        └─────────────────────────┘                        │
              Data Collection Pipeline                     │
                      (per niche)                          │
                                                           │
                      localhost:5000 ◄─────────────────────┘
                      localhost:5173 (Vite dev server)
```

### Authentication Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     CLERK AUTHENTICATION FLOW                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. User visits MetAds                                          │
│     └── Clerk checks session                                    │
│         ├── No session → Redirect to /sign-in                   │
│         └── Valid session → Load app with user context          │
│                                                                  │
│  2. Sign-in Options (via Clerk)                                 │
│     ├── Email + Password                                        │
│     ├── Google OAuth                                            │
│     ├── GitHub OAuth                                            │
│     └── Magic Link (email)                                      │
│                                                                  │
│  3. After Authentication                                        │
│     ├── Clerk provides JWT token                                │
│     ├── Frontend sends token in Authorization header            │
│     ├── Backend validates token with Clerk SDK                  │
│     └── User ID extracted for data scoping                      │
│                                                                  │
│  4. Protected Routes                                            │
│     ├── Frontend: Vue Router guards check Clerk session         │
│     └── Backend: Flask middleware validates JWT on every request│
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Data Organization with Niches (User-Scoped)

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER: john@example.com                        │
├─────────────────────────────────────────────────────────────────┤
│                         NICHES                                   │
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

┌─────────────────────────────────────────────────────────────────┐
│                    USER: jane@example.com                        │
├─────────────────────────────────────────────────────────────────┤
│                         NICHES                                   │
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐                     │
│  │ Fitness Apps     │  │ E-commerce       │                     │
│  │                  │  │ Fashion          │                     │
│  └──────────────────┘  └──────────────────┘                     │
│                                                                  │
│  (Each user's niches are completely isolated)                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Foundation, Database & Authentication

**Duration:** Days 1-4 (extended by 1 day for Clerk setup)

### Day 1: Project Structure & Dependencies

#### Tasks

- [ ] Create project folder structure
- [ ] Set up Python virtual environment
- [ ] Install backend dependencies (including Clerk SDK)
- [ ] Initialize Vue project with Vite
- [ ] Configure ESLint, Prettier for frontend
- [ ] **Create Clerk account and application**
- [ ] **Configure Clerk dashboard (OAuth providers, branding)**

#### Folder Structure

```
metaAds/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── middleware/              # NEW: Auth middleware
│   │   │   ├── __init__.py
│   │   │   └── auth.py              # Clerk JWT validation
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py              # NEW: User model (synced from Clerk)
│   │   │   ├── niche.py
│   │   │   ├── ad.py
│   │   │   ├── saved_ad.py
│   │   │   └── page.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py              # NEW: Auth webhooks from Clerk
│   │   │   ├── niches.py
│   │   │   ├── ads.py
│   │   │   └── saved.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── user_service.py      # NEW: User sync service
│   │   │   ├── niche_service.py
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
│   │   │   ├── auth/                # NEW: Auth components
│   │   │   │   ├── UserButton.vue
│   │   │   │   └── ProtectedRoute.vue
│   │   │   ├── common/
│   │   │   ├── niches/
│   │   │   ├── search/
│   │   │   ├── results/
│   │   │   └── detail/
│   │   ├── composables/
│   │   │   └── useAuth.js           # NEW: Auth composable
│   │   ├── router/
│   │   │   └── index.js             # Updated with auth guards
│   │   ├── stores/
│   │   │   └── auth.js              # NEW: Auth store
│   │   ├── views/
│   │   │   ├── SignInView.vue       # NEW
│   │   │   ├── SignUpView.vue       # NEW
│   │   │   └── ...
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

#### Clerk Configuration

```bash
# Clerk Dashboard Setup:
# 1. Go to https://dashboard.clerk.com
# 2. Create new application: "MetAds"
# 3. Enable authentication methods:
#    - Email + Password
#    - Google OAuth
#    - GitHub OAuth (optional)
# 4. Configure redirect URLs:
#    - Development: http://localhost:5173
#    - Production: https://your-domain.com
# 5. Copy API keys to .env files
```

#### Environment Variables

```bash
# backend/.env
FLASK_ENV=development
FLASK_DEBUG=True
DATABASE_URL=sqlite:///data/ads_intelligence.db
CORS_ORIGINS=http://localhost:5173

# Clerk (Backend)
CLERK_SECRET_KEY=sk_test_xxxxxxxxxxxxx
CLERK_PUBLISHABLE_KEY=pk_test_xxxxxxxxxxxxx
CLERK_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxx

# Meta API
FB_ACCESS_TOKEN=your_meta_access_token
```

```bash
# frontend/.env
VITE_API_URL=http://localhost:5000/api
VITE_CLERK_PUBLISHABLE_KEY=pk_test_xxxxxxxxxxxxx
```

#### Deliverables

- `backend/requirements.txt` (with clerk-sdk-python)
- `frontend/package.json` (with @clerk/vue)
- Working folder structure
- Clerk application configured

---

### Day 2: Clerk Integration (Backend)

#### Tasks

- [ ] Install and configure Clerk Python SDK
- [ ] Create auth middleware for JWT validation
- [ ] Create user model (synced from Clerk)
- [ ] Set up Clerk webhook endpoint for user sync
- [ ] Create protected route decorator
- [ ] Test auth flow with Postman/curl

#### Backend Dependencies

```txt
# requirements.txt (additions)
clerk-sdk-python==0.1.0
PyJWT==2.8.0
```

#### Auth Middleware

```python
# backend/app/middleware/auth.py
from functools import wraps
from flask import request, g, jsonify
from clerk_sdk_python import Clerk
from app.config import Config

clerk = Clerk(secret_key=Config.CLERK_SECRET_KEY)

def require_auth(f):
    """
    Decorator to protect routes with Clerk authentication.
    Extracts user_id from JWT and adds to Flask's g object.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')

        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({
                'success': False,
                'error': 'Missing or invalid authorization header'
            }), 401

        token = auth_header.split(' ')[1]

        try:
            # Verify JWT with Clerk
            session = clerk.sessions.verify_token(token)

            # Extract user info
            g.user_id = session.user_id
            g.session_id = session.id

            return f(*args, **kwargs)

        except Exception as e:
            return jsonify({
                'success': False,
                'error': 'Invalid or expired token'
            }), 401

    return decorated_function


def get_current_user_id() -> str:
    """Get the current authenticated user's ID from Flask g object."""
    return getattr(g, 'user_id', None)
```

#### User Model

```python
# backend/app/models/user.py
from sqlalchemy import Column, String, Boolean, Text
from app.utils.ids import generate_uuid, now_iso8601
from app import db

class User(db.Model):
    """
    User model - synced from Clerk via webhooks.
    We store minimal user data for query efficiency.
    """
    __tablename__ = 'users'

    # Primary key matches Clerk user ID
    id = Column(String(100), primary_key=True)  # Clerk user_id

    # Basic info (synced from Clerk)
    email = Column(String(255), unique=True, nullable=False, index=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    image_url = Column(Text, nullable=True)

    # Account status
    is_active = Column(Boolean, default=True)

    # Timestamps (ISO8601 strings)
    created_at = Column(String(30), default=now_iso8601)
    updated_at = Column(String(30), default=now_iso8601, onupdate=now_iso8601)
    last_sign_in_at = Column(String(30), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'image_url': self.image_url,
            'created_at': self.created_at
        }
```

#### Clerk Webhook Handler

```python
# backend/app/routes/auth.py
from flask import Blueprint, request, jsonify
from clerk_sdk_python import Clerk
from app.config import Config
from app.models.user import User
from app.utils.ids import now_iso8601
from app import db
import hmac
import hashlib

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')
clerk = Clerk(secret_key=Config.CLERK_SECRET_KEY)

@auth_bp.route('/webhook', methods=['POST'])
def clerk_webhook():
    """
    Handle Clerk webhooks for user sync.
    Events: user.created, user.updated, user.deleted
    """
    # Verify webhook signature
    payload = request.get_data()
    signature = request.headers.get('svix-signature')

    if not verify_webhook_signature(payload, signature):
        return jsonify({'error': 'Invalid signature'}), 401

    event = request.json
    event_type = event.get('type')
    user_data = event.get('data', {})

    if event_type == 'user.created':
        user = User(
            id=user_data['id'],
            email=user_data['email_addresses'][0]['email_address'],
            first_name=user_data.get('first_name'),
            last_name=user_data.get('last_name'),
            image_url=user_data.get('image_url'),
            created_at=now_iso8601()
        )
        db.session.add(user)
        db.session.commit()

    elif event_type == 'user.updated':
        user = User.query.get(user_data['id'])
        if user:
            user.email = user_data['email_addresses'][0]['email_address']
            user.first_name = user_data.get('first_name')
            user.last_name = user_data.get('last_name')
            user.image_url = user_data.get('image_url')
            user.updated_at = now_iso8601()
            db.session.commit()

    elif event_type == 'user.deleted':
        user = User.query.get(user_data['id'])
        if user:
            user.is_active = False
            user.updated_at = now_iso8601()
            db.session.commit()

    return jsonify({'received': True}), 200


def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """Verify Clerk webhook signature."""
    if not signature:
        return False

    expected = hmac.new(
        Config.CLERK_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(signature, expected)


@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    """
    Get current user info.
    This is called after Clerk auth to sync user data.
    """
    from app.middleware.auth import require_auth, get_current_user_id

    @require_auth
    def _get_user():
        user_id = get_current_user_id()
        user = User.query.get(user_id)

        if not user:
            # User authenticated via Clerk but not in our DB yet
            # This can happen if webhook hasn't fired yet
            # Create user from Clerk data
            clerk_user = clerk.users.get(user_id)
            user = User(
                id=clerk_user.id,
                email=clerk_user.email_addresses[0].email_address,
                first_name=clerk_user.first_name,
                last_name=clerk_user.last_name,
                image_url=clerk_user.image_url,
                created_at=now_iso8601()
            )
            db.session.add(user)
            db.session.commit()

        return jsonify({
            'success': True,
            'data': user.to_dict()
        })

    return _get_user()
```

#### Deliverables

- `backend/app/middleware/auth.py`
- `backend/app/models/user.py`
- `backend/app/routes/auth.py`
- Working JWT validation

---

### Day 3: Database Models (with User Scoping)

#### Tasks

- [ ] Define SQLAlchemy models with UUID primary keys
- [ ] **Add user_id to niches table for multi-tenancy**
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
| **User scoping** | `user_id` on niches; all queries filter by user |
| **Composite keys ready** | PK + SK pattern (user_id + niche_id + entity_id) |
| **Denormalization** | Embed related data to avoid JOINs |
| **Native lists** | Store as JSON in SQLite, native Lists in DynamoDB |
| **ISO8601 dates** | String format for cross-database compatibility |

#### Database Schema

```
┌─────────────────────────────────────────────────────────────────┐
│                           users                                  │
│              (synced from Clerk via webhooks)                    │
├─────────────────────────────────────────────────────────────────┤
│ PK: id              VARCHAR(100) (Clerk user ID)                │
│ ─────────────────────────────────────────────────────────────── │
│ id                  VARCHAR(100) PRIMARY KEY (Clerk user_id)    │
│ email               VARCHAR(255) UNIQUE INDEX                   │
│ first_name          VARCHAR(100)                                │
│ last_name           VARCHAR(100)                                │
│ image_url           TEXT                                        │
│ is_active           BOOLEAN DEFAULT TRUE                        │
│ created_at          VARCHAR(30) ISO8601                         │
│ updated_at          VARCHAR(30) ISO8601                         │
│ last_sign_in_at     VARCHAR(30) ISO8601                         │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                           niches                                 │
├─────────────────────────────────────────────────────────────────┤
│ PK: user_id         VARCHAR(100) (partition key)                │
│ SK: niche_id        UUID (sort key)                             │
│ ─────────────────────────────────────────────────────────────── │
│ niche_id            UUID PRIMARY KEY                            │
│ user_id             VARCHAR(100) INDEX (Clerk user ID)          │
│ slug                VARCHAR(200) INDEX                          │
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
│ UNIQUE(user_id, slug) -- slug unique per user                   │
│                                                                  │
│ Index: user-slug-index (user_id + slug → niche_id)              │
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
│  │  User   │────1:N──│  Niche                               │    │
│  └─────────┘         │  (user_id scopes all niches)         │    │
│                      └───────────────┬─────────────────────┘    │
│                                      │                          │
│                                      │                          │
│  ┌─────────┐         ┌───────────────▼─────────────────────┐    │
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
      User scoping is enforced at the niche level.
```

#### Access Patterns

| Access Pattern | Query Strategy | Index Used |
|----------------|----------------|------------|
| List user's niches | Query by user_id | user_id (PK) |
| Get niche by slug (for user) | Query by user_id + slug | user-slug-index |
| Get all ads in niche | Query by niche_id | niche_id (PK) |
| Get ads sorted by days_active | Query niche_id, sort by days_active | niche-days-index |
| Get ads from specific page | Query niche_id + page_id | niche-page-index |
| Get saved ads in niche | Query niche_id + is_saved=true | niche-saved-index |
| Get related ads (variants) | Query niche_id + page_id, filter dates | niche-page-index |
| Get collection history | Query niche_id, sort by run_id | niche_id (PK) |

#### Deliverables

- `backend/app/models/user.py`
- `backend/app/models/niche.py` (with user_id)
- `backend/app/models/ad.py` (with denormalized saved_ads and page data)
- `backend/app/models/page.py`
- `backend/app/models/niche_page.py`
- `backend/app/models/collection_run.py`
- `backend/app/utils/ids.py` (UUID generation utilities)
- Database migration files

---

### Day 4: Data Collection Integration

#### Tasks

- [ ] Integrate existing Meta API collector
- [ ] Integrate existing ad parser
- [ ] Create CLI command to run collection **per niche**
- [ ] Test end-to-end: API → Parser → Database
- [ ] Create sample users and niches with data

#### CLI Commands (Updated)

```bash
# Create a new niche (requires user_id for CLI operations)
python run.py niche create --user "user_xxx" --name "Video Editing Apps" --keywords "video editing ai,opus clip"

# List all niches for a user
python run.py niche list --user "user_xxx"

# Collect ads for a specific niche
python run.py collect --niche "video-editing-apps" --user "user_xxx" --limit 50

# Collect ads for all active niches (for a user)
python run.py collect --all --user "user_xxx" --limit 50

# Show niche stats
python run.py niche stats --niche "video-editing-apps" --user "user_xxx"
```

#### Deliverables

- Working data collection pipeline (niche-aware, user-scoped)
- SQLite database with sample users, niches, and data
- CLI commands for niche management

---

## Phase 2: Flask REST API Backend

**Duration:** Days 5-9 (shifted by 1 day)

### Day 5: Flask App Setup

#### Tasks

- [ ] Initialize Flask application factory
- [ ] Configure CORS for local development
- [ ] Set up environment configuration
- [ ] **Register auth blueprint and middleware**
- [ ] Create health check endpoint
- [ ] Set up error handling middleware

#### API Configuration

```python
# Config
FLASK_ENV=development
FLASK_DEBUG=True
DATABASE_URL=sqlite:///data/ads_intelligence.db
CORS_ORIGINS=http://localhost:5173

# Clerk
CLERK_SECRET_KEY=sk_test_xxxxxxxxxxxxx
CLERK_PUBLISHABLE_KEY=pk_test_xxxxxxxxxxxxx
```

#### Endpoints (Day 5)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/health` | No | Health check |
| GET | `/api/stats` | Yes | Global database statistics (for user) |
| POST | `/api/auth/webhook` | No* | Clerk webhook (verified by signature) |
| GET | `/api/auth/me` | Yes | Get current user |

#### Deliverables

- `backend/app/__init__.py` (app factory with Clerk)
- `backend/app/config.py`
- `backend/run.py`
- Working `/api/health` and `/api/auth/me` endpoints

---

### Day 6: Niche Endpoints (User-Scoped)

#### Tasks

- [ ] Implement niche CRUD service (user-scoped)
- [ ] Create niche routes with auth middleware
- [ ] Add niche statistics endpoint
- [ ] Add collection trigger endpoint
- [ ] Write unit tests

#### Endpoints (Day 6)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/niches` | Yes | List user's niches |
| POST | `/api/niches` | Yes | Create a new niche |
| GET | `/api/niches/:slug` | Yes | Get niche details |
| PATCH | `/api/niches/:slug` | Yes | Update niche |
| DELETE | `/api/niches/:slug` | Yes | Delete niche (soft delete) |
| GET | `/api/niches/:slug/stats` | Yes | Get niche statistics |
| POST | `/api/niches/:slug/collect` | Yes | Trigger collection for niche |

#### Niche Service (User-Scoped)

```python
# backend/app/services/niche_service.py
from app.models.niche import Niche
from app.middleware.auth import get_current_user_id
from app.utils.ids import generate_uuid, now_iso8601
from app import db

class NicheService:

    @staticmethod
    def get_user_niches():
        """Get all niches for the current user."""
        user_id = get_current_user_id()
        return Niche.query.filter_by(
            user_id=user_id,
            is_active=True
        ).all()

    @staticmethod
    def get_niche_by_slug(slug: str):
        """Get a niche by slug for the current user."""
        user_id = get_current_user_id()
        return Niche.query.filter_by(
            user_id=user_id,
            slug=slug,
            is_active=True
        ).first()

    @staticmethod
    def create_niche(data: dict):
        """Create a new niche for the current user."""
        user_id = get_current_user_id()

        # Check if slug already exists for this user
        existing = Niche.query.filter_by(
            user_id=user_id,
            slug=data['slug']
        ).first()

        if existing:
            raise ValueError(f"Niche with slug '{data['slug']}' already exists")

        niche = Niche(
            niche_id=generate_uuid(),
            user_id=user_id,
            slug=data['slug'],
            name=data['name'],
            description=data.get('description'),
            color=data.get('color', '#8B5CF6'),
            icon=data.get('icon', '📊'),
            keywords=data.get('keywords', []),
            countries=data.get('countries', ['US']),
            platforms=data.get('platforms', ['instagram', 'facebook']),
            created_at=now_iso8601()
        )

        db.session.add(niche)
        db.session.commit()

        return niche
```

#### Niche Response Format

```json
{
  "success": true,
  "data": {
    "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
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

#### Deliverables

- `backend/app/services/niche_service.py` (user-scoped)
- `backend/app/routes/niches.py` (with @require_auth)
- Unit tests for niche functionality

---

### Day 7: Search Endpoint (Niche-Scoped)

#### Tasks

- [ ] Implement search service with filtering (niche-scoped)
- [ ] Create search route with query parameters
- [ ] Add pagination support
- [ ] Add sorting options
- [ ] **Verify niche ownership before search**
- [ ] Write unit tests

#### Endpoints (Day 7)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/niches/:slug/ads/search` | Yes | Search ads within a niche |

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

#### Deliverables

- `backend/app/services/ad_service.py` (niche-aware, user-scoped)
- `backend/app/routes/ads.py` (niche-scoped with auth)
- Unit tests for search functionality

---

### Day 8: Detail & Related Ads Endpoints

#### Tasks

- [ ] Implement ad detail endpoint (niche-scoped)
- [ ] Implement variant detection service
- [ ] Create related ads endpoint
- [ ] Add page ads endpoint
- [ ] **Verify niche ownership for all operations**
- [ ] Write unit tests

#### Endpoints (Day 8)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/niches/:slug/ads/:id` | Yes | Get ad details |
| GET | `/api/niches/:slug/ads/:id/related` | Yes | Get related ads/variants |
| GET | `/api/niches/:slug/pages` | Yes | List pages in niche |
| GET | `/api/niches/:slug/pages/:page_id/ads` | Yes | Get ads from a page |
| POST | `/api/niches/:slug/pages/:page_id/competitor` | Yes | Mark page as competitor |

#### Deliverables

- `backend/app/services/variant_service.py`
- Ad detail and related ads routes (niche-scoped with auth)
- Unit tests

---

### Day 9: Saved Ads Endpoints (Niche-Scoped)

#### Tasks

- [ ] Implement saved ads operations (updates `is_saved` flag on ads)
- [ ] Create saved ads routes with auth
- [ ] Add notes and tags support
- [ ] Write unit tests
- [ ] API documentation

#### Endpoints (Day 9)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/niches/:slug/saved` | Yes | Get saved ads in niche |
| POST | `/api/niches/:slug/ads/:id/save` | Yes | Save an ad |
| DELETE | `/api/niches/:slug/ads/:id/save` | Yes | Unsave an ad |
| PATCH | `/api/niches/:slug/ads/:id/save` | Yes | Update saved notes/tags |

#### Deliverables

- `backend/app/routes/saved.py` (niche-scoped with auth)
- Complete API documentation
- All backend unit tests passing

---

## Phase 3: Frontend Foundation

**Duration:** Days 10-14 (shifted by 2 days)

### Day 10: Vue Project Setup with Clerk

#### Tasks

- [ ] Initialize Vue 3 project with Vite
- [ ] **Install and configure @clerk/vue**
- [ ] Install and configure Vue Router
- [ ] Install and configure Pinia (state management)
- [ ] Set up API service layer (axios with auth headers)
- [ ] Configure proxy for backend API
- [ ] **Set up Clerk provider in App.vue**

#### Dependencies

```json
{
  "dependencies": {
    "vue": "^3.4.0",
    "vue-router": "^4.2.0",
    "pinia": "^2.1.0",
    "axios": "^1.6.0",
    "@clerk/vue": "^1.0.0"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.0.0",
    "vite": "^5.0.0",
    "sass": "^1.69.0"
  }
}
```

#### Clerk Vue Setup

```javascript
// main.js
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { clerkPlugin } from '@clerk/vue'
import App from './App.vue'
import router from './router'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(clerkPlugin, {
  publishableKey: import.meta.env.VITE_CLERK_PUBLISHABLE_KEY
})

app.mount('#app')
```

```vue
<!-- App.vue -->
<template>
  <ClerkProvider>
    <RouterView />
  </ClerkProvider>
</template>

<script setup>
import { ClerkProvider } from '@clerk/vue'
</script>
```

#### Router Configuration (with Auth Guards)

```javascript
// router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import { useAuth } from '@clerk/vue'

const routes = [
  // Public routes
  {
    path: '/sign-in',
    name: 'SignIn',
    component: () => import('@/views/SignInView.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/sign-up',
    name: 'SignUp',
    component: () => import('@/views/SignUpView.vue'),
    meta: { requiresAuth: false }
  },

  // Protected routes
  {
    path: '/',
    name: 'NicheSelector',
    component: () => import('@/views/NicheSelectorView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/niches/new',
    name: 'CreateNiche',
    component: () => import('@/views/CreateNicheView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/n/:nicheSlug',
    name: 'NicheWorkspace',
    component: () => import('@/views/NicheWorkspaceView.vue'),
    meta: { requiresAuth: true },
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

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Auth navigation guard
router.beforeEach(async (to, from, next) => {
  const { isSignedIn, isLoaded } = useAuth()

  // Wait for Clerk to load
  if (!isLoaded.value) {
    // Could show loading state here
    await new Promise(resolve => {
      const unwatch = watch(isLoaded, (loaded) => {
        if (loaded) {
          unwatch()
          resolve()
        }
      })
    })
  }

  const requiresAuth = to.meta.requiresAuth !== false

  if (requiresAuth && !isSignedIn.value) {
    // Redirect to sign-in with return URL
    next({
      name: 'SignIn',
      query: { redirect: to.fullPath }
    })
  } else if (!requiresAuth && isSignedIn.value) {
    // Redirect authenticated users away from auth pages
    next({ name: 'NicheSelector' })
  } else {
    next()
  }
})

export default router
```

#### API Service with Auth

```javascript
// services/api.js
import axios from 'axios'
import { useAuth } from '@clerk/vue'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:5000/api'
})

// Add auth token to requests
api.interceptors.request.use(async (config) => {
  const { getToken } = useAuth()
  const token = await getToken()

  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }

  return config
})

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid - Clerk will handle refresh
      window.location.href = '/sign-in'
    }
    return Promise.reject(error)
  }
)

export default api
```

#### Deliverables

- Working Vue project with Clerk
- Router configuration with auth guards
- Pinia store setup
- API service layer with auth headers

---

### Day 11: Auth Views & Niche Selector

#### Tasks

- [ ] **Create SignIn view with Clerk components**
- [ ] **Create SignUp view with Clerk components**
- [ ] Create NicheSelector view (landing page)
- [ ] Create NicheCard component
- [ ] Create CreateNiche view/modal
- [ ] **Add UserButton to header**

#### Sign In View

```vue
<!-- views/SignInView.vue -->
<template>
  <div class="auth-page">
    <div class="auth-container">
      <div class="auth-header">
        <h1>MetAds</h1>
        <p>Competitive intelligence for Meta Ads</p>
      </div>

      <SignIn
        :routing="'path'"
        :path="'/sign-in'"
        :signUpUrl="'/sign-up'"
        :afterSignInUrl="redirectUrl"
      />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { SignIn } from '@clerk/vue'

const route = useRoute()

const redirectUrl = computed(() => {
  return route.query.redirect || '/'
})
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.auth-container {
  background: white;
  padding: 2rem;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0,0,0,0.2);
  max-width: 400px;
  width: 100%;
}

.auth-header {
  text-align: center;
  margin-bottom: 2rem;
}

.auth-header h1 {
  font-size: 2rem;
  color: #1a1a2e;
  margin-bottom: 0.5rem;
}

.auth-header p {
  color: #6b7280;
}
</style>
```

#### User Button in Header

```vue
<!-- components/layout/AppHeader.vue -->
<template>
  <header class="app-header">
    <div class="header-left">
      <router-link to="/" class="logo">
        MetAds
      </router-link>
    </div>

    <div class="header-right">
      <UserButton
        :afterSignOutUrl="'/sign-in'"
        :appearance="{
          elements: {
            avatarBox: 'w-10 h-10'
          }
        }"
      />
    </div>
  </header>
</template>

<script setup>
import { UserButton } from '@clerk/vue'
</script>
```

#### Deliverables

- `frontend/src/views/SignInView.vue`
- `frontend/src/views/SignUpView.vue`
- `frontend/src/views/NicheSelectorView.vue`
- `frontend/src/components/niches/NicheCard.vue`
- `frontend/src/components/niches/NicheForm.vue`
- `frontend/src/components/layout/AppHeader.vue` (with UserButton)

---

### Day 12: Desktop Layout

#### Tasks

- [ ] Implement 3-column desktop layout for workspace
- [ ] Add header with niche indicator and user menu
- [ ] Create WorkspaceHeader with user context

#### Workspace Layout (within Niche)

```
┌──────────────────────────────────────────────────────────────────┐
│  [← Niches]  🎬 Video Editing Apps    [⚙️]  [Collect]  [Avatar▼] │
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

- `frontend/src/views/NicheWorkspaceView.vue`
- `frontend/src/components/layout/WorkspaceHeader.vue`

---

### Day 13: Mobile Layout

#### Tasks

- [ ] Implement responsive breakpoints
- [ ] Create mobile niche selector
- [ ] Create mobile bottom tab navigation (within niche)
- [ ] Adapt SearchPanel for mobile (full screen)
- [ ] Adapt ResultsList for mobile (full screen)
- [ ] Create mobile AdDetail overlay
- [ ] Add touch-friendly interactions

#### Deliverables

- `frontend/src/components/layout/MobileNav.vue`
- `frontend/src/components/niches/NicheListMobile.vue`
- Responsive CSS for all components
- Mobile-specific view adaptations

---

### Day 14: Styling & Design System

#### Tasks

- [ ] Define CSS custom properties (colors, spacing, typography)
- [ ] Add niche color support in design system
- [ ] Create base component styles
- [ ] Implement card component styles
- [ ] Add loading states and skeletons
- [ ] Add transitions and animations
- [ ] **Style Clerk components to match app theme**
- [ ] Test across screen sizes

#### Clerk Theme Customization

```javascript
// In ClerkProvider or signIn/signUp components
const clerkAppearance = {
  baseTheme: undefined,
  variables: {
    colorPrimary: '#2563eb',
    colorBackground: '#ffffff',
    colorInputBackground: '#f9fafb',
    colorInputText: '#111827',
    borderRadius: '8px',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
  },
  elements: {
    card: 'shadow-none',
    formButtonPrimary: 'bg-primary-600 hover:bg-primary-700',
    socialButtonsBlockButton: 'border-gray-200 hover:bg-gray-50'
  }
}
```

#### Deliverables

- `frontend/src/assets/styles/variables.scss`
- `frontend/src/assets/styles/base.scss`
- `frontend/src/assets/styles/components.scss`
- Polished visual design across all views

---

## Phase 4: Frontend Features

**Duration:** Days 15-19 (shifted by 2 days)

### Day 15: Niche Management & Search

#### Tasks

- [ ] Implement niche store (Pinia)
- [ ] Create niche CRUD functionality in UI
- [ ] Implement search form with all filter options
- [ ] Create search store (niche-scoped)
- [ ] Connect search form to API (with auth)
- [ ] Add filter chips display

#### Auth Store

```javascript
// stores/auth.js
import { defineStore } from 'pinia'
import { useAuth, useUser } from '@clerk/vue'
import api from '@/services/api'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    loading: true
  }),

  getters: {
    isAuthenticated: (state) => !!state.user,
    userName: (state) => {
      if (!state.user) return ''
      return state.user.first_name || state.user.email.split('@')[0]
    }
  },

  actions: {
    async fetchUser() {
      const { isSignedIn } = useAuth()

      if (!isSignedIn.value) {
        this.user = null
        this.loading = false
        return
      }

      try {
        const response = await api.get('/auth/me')
        this.user = response.data.data
      } catch (error) {
        console.error('Failed to fetch user:', error)
        this.user = null
      } finally {
        this.loading = false
      }
    },

    clearUser() {
      this.user = null
    }
  }
})
```

#### Deliverables

- `frontend/src/stores/auth.js`
- `frontend/src/stores/niches.js`
- `frontend/src/stores/search.js`
- `frontend/src/components/search/SearchForm.vue`
- `frontend/src/components/search/FilterChips.vue`
- Working niche selection and search functionality

---

### Day 16: Results List

#### Tasks

- [ ] Create AdCard component
- [ ] Implement results list with virtual scrolling (if needed)
- [ ] Add card hover/selected states
- [ ] Implement sort dropdown
- [ ] Add "Load more" pagination
- [ ] Create loading skeleton cards
- [ ] Show niche context in results

#### Deliverables

- `frontend/src/components/results/AdCard.vue`
- `frontend/src/components/results/AdCardSkeleton.vue`
- `frontend/src/stores/results.js`
- Fully functional results list

---

### Day 17: Ad Detail Panel

#### Tasks

- [ ] Create creative preview component (image/video)
- [ ] Build page info section
- [ ] Build metrics display (days active, platforms, status)
- [ ] Build ad copy section (headline, body, CTA)
- [ ] Add action buttons (View on Meta, Save to Niche, Copy)
- [ ] Implement "Related Ads" link

#### Deliverables

- `frontend/src/components/detail/CreativePreview.vue`
- `frontend/src/components/detail/PageInfo.vue`
- `frontend/src/components/detail/AdMetrics.vue`
- `frontend/src/components/detail/AdCopy.vue`
- `frontend/src/components/detail/AdActions.vue`

---

### Day 18: Related Ads / Variants

#### Tasks

- [ ] Create RelatedAdsPanel component
- [ ] Implement variant insights summary
- [ ] Create VariantCard component
- [ ] Add badges (LONGEST, NEWEST)
- [ ] Mobile slide-in panel behavior
- [ ] Connect to API endpoint

#### Deliverables

- `frontend/src/components/detail/RelatedAdsPanel.vue`
- `frontend/src/components/detail/VariantInsights.vue`
- `frontend/src/components/detail/VariantCard.vue`

---

### Day 19: Saved Ads & Niche Settings

#### Tasks

- [ ] Create SavedAds view/tab (niche-scoped)
- [ ] Implement save/unsave functionality with tags
- [ ] Add saved indicator to cards
- [ ] Create NicheSettings view (edit keywords, colors, etc.)
- [ ] Create empty states (no results, no saved)
- [ ] Implement error states and error handling
- [ ] Add toast notifications

#### Deliverables

- `frontend/src/views/SavedView.vue` (niche-scoped)
- `frontend/src/views/NicheSettingsView.vue`
- `frontend/src/stores/saved.js`
- `frontend/src/components/common/EmptyState.vue`
- `frontend/src/components/common/ErrorState.vue`
- `frontend/src/components/common/Toast.vue`
- `frontend/src/components/detail/SaveNotesModal.vue`

---

## Phase 5: Integration & Polish

**Duration:** Days 20-23 (shifted by 2 days)

### Day 20: End-to-End Testing

#### Tasks

- [ ] Test complete user flows (including auth)
- [ ] **Test sign-in → niche creation → search → save flow**
- [ ] **Test sign-out and session expiry**
- [ ] Test switching between niches
- [ ] Test save/unsave functionality
- [ ] Test filter combinations
- [ ] Test mobile responsiveness
- [ ] Fix bugs discovered during testing

#### Test Scenarios

1. **Sign up flow**: Create account → Verify email → Land on Niche Selector
2. **Sign in flow**: Sign in → Redirect to saved location
3. Create new niche "Test Niche" → Add keywords → Trigger collection → View results
4. Switch between niches → Verify data isolation
5. Search in "Video Editing Apps" → View ad → View related → Save ad
6. Apply multiple filters → Clear filters → Search again
7. Mobile: Navigate between niches → Open workspace → View ad detail
8. Edit niche settings → Verify changes persist
9. Empty state: Search with no results → Clear filters
10. Error handling: API timeout → Retry
11. **Sign out**: Click sign out → Redirect to sign-in page
12. **Session expiry**: Token expires → Redirect to sign-in

#### Deliverables

- Bug fixes
- Stable end-to-end flows (including auth)

---

### Day 21: Performance Optimization

#### Tasks

- [ ] Implement pagination/infinite scroll
- [ ] Add debounce to search input
- [ ] Optimize API queries (indexes, query optimization)
- [ ] Lazy load images
- [ ] Add request caching where appropriate
- [ ] **Optimize Clerk token refresh**
- [ ] Test with larger dataset (500+ ads across multiple niches)

#### Deliverables

- Smooth performance with large datasets
- Optimized database queries
- Efficient auth token management

---

### Day 22: Data Pipeline Integration

#### Tasks

- [ ] Create collection management CLI (niche-aware)
- [ ] Add scheduled collection script per niche
- [ ] Implement incremental updates (don't duplicate ads)
- [ ] Add collection status tracking per niche
- [ ] Test full pipeline: Collect → Parse → Store → Display
- [ ] Add "Collect Now" button in UI

#### Deliverables

- Working CLI commands (niche-aware)
- Collection pipeline integrated with niches
- UI trigger for collection

---

### Day 23: Documentation & Wrap-up

#### Tasks

- [ ] Write README with setup instructions (including Clerk setup)
- [ ] Document API endpoints (with auth requirements)
- [ ] **Document Clerk configuration**
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
## Environment Setup
  ### Clerk Configuration
  ### Meta API Setup
## Running Locally
## Project Structure
## Concepts
  ### Authentication
  ### Niches
  ### Ads
  ### Variants
## API Documentation
  ### Authentication
  ### Protected Endpoints
## Data Collection
## CLI Commands
## Contributing
```

#### Deliverables

- Complete README.md
- API documentation (with auth)
- Clerk setup guide
- Working first draft (MVP) with authentication

---

## API Endpoint Summary

| Method | Endpoint | Auth | Description | Phase |
|--------|----------|------|-------------|-------|
| GET | `/api/health` | No | Health check | 2 |
| **Auth** |  |  |  |  |
| POST | `/api/auth/webhook` | No* | Clerk webhook | 2 |
| GET | `/api/auth/me` | Yes | Get current user | 2 |
| GET | `/api/stats` | Yes | Global database statistics | 2 |
| **Niches** |  |  |  |  |
| GET | `/api/niches` | Yes | List user's niches | 2 |
| POST | `/api/niches` | Yes | Create a new niche | 2 |
| GET | `/api/niches/:slug` | Yes | Get niche details | 2 |
| PATCH | `/api/niches/:slug` | Yes | Update niche | 2 |
| DELETE | `/api/niches/:slug` | Yes | Delete niche | 2 |
| GET | `/api/niches/:slug/stats` | Yes | Get niche statistics | 2 |
| POST | `/api/niches/:slug/collect` | Yes | Trigger collection | 2 |
| **Ads (Niche-Scoped)** |  |  |  |  |
| GET | `/api/niches/:slug/ads/search` | Yes | Search ads in niche | 2 |
| GET | `/api/niches/:slug/ads/:id` | Yes | Get ad details | 2 |
| GET | `/api/niches/:slug/ads/:id/related` | Yes | Get related ads/variants | 2 |
| **Pages (Niche-Scoped)** |  |  |  |  |
| GET | `/api/niches/:slug/pages` | Yes | List pages in niche | 2 |
| GET | `/api/niches/:slug/pages/:page_id/ads` | Yes | Get ads from a page | 2 |
| POST | `/api/niches/:slug/pages/:page_id/competitor` | Yes | Mark as competitor | 2 |
| **Saved Ads (Niche-Scoped)** |  |  |  |  |
| GET | `/api/niches/:slug/saved` | Yes | Get saved ads | 2 |
| POST | `/api/niches/:slug/ads/:id/save` | Yes | Save an ad | 2 |
| DELETE | `/api/niches/:slug/ads/:id/save` | Yes | Unsave an ad | 2 |
| PATCH | `/api/niches/:slug/ads/:id/save` | Yes | Update saved notes/tags | 2 |

*Webhook endpoint is verified by Clerk signature, not Bearer token

---

## Component Inventory

### Auth Components (NEW)
- `SignInView.vue`
- `SignUpView.vue`
- `UserButton.vue` (from @clerk/vue)
- `ProtectedRoute.vue`

### Niche Components
- `NicheCard.vue`
- `NicheForm.vue`
- `NicheListMobile.vue`
- `NicheColorPicker.vue`
- `KeywordInput.vue`

### Layout Components
- `AppHeader.vue` (with UserButton)
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
- `SaveNotesModal.vue`

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
- `backend/app/models/user.py` (NEW - synced from Clerk)
- `backend/app/models/niche.py` (with user_id)
- `backend/app/models/ad.py` (includes denormalized saved fields)
- `backend/app/models/page.py`
- `backend/app/models/niche_page.py`
- `backend/app/models/collection_run.py`
- `backend/app/utils/ids.py` (UUID generation)
- `backend/app/middleware/auth.py` (NEW - Clerk JWT validation)

---

## Milestones

| Milestone | Target Date | Description |
|-----------|-------------|-------------|
| M1: Auth & Database Ready | Day 4 | Clerk integrated, schema with users/niches |
| M2: API Complete | Day 9 | All endpoints working (with auth) |
| M3: UI Foundation | Day 14 | Auth views, layouts, niche selector, styling |
| M4: Feature Complete | Day 19 | All features implemented |
| M5: MVP Ready | Day 23 | First draft complete with authentication |

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Clerk integration complexity | Use official @clerk/vue package, follow docs |
| Token expiry edge cases | Implement proper refresh flow, test thoroughly |
| Meta API rate limits | Implement caching, batch collection per niche |
| Complex variant detection | Start with simple temporal matching, iterate |
| Mobile layout complexity | Use established patterns from wireframes |
| Scope creep | Stick to MVP features, defer enhancements |
| Niche data isolation | User-scoped queries, auth middleware on all routes |

---

## Post-MVP Enhancements (Future)

- [x] ~~User authentication (multi-user with personal niches)~~ **Included in MVP**
- [ ] Team workspaces (shared niches with role-based access)
- [ ] Export to CSV/PDF (per niche)
- [ ] Advanced analytics dashboard per niche
- [ ] Email alerts for new competitor ads in niche
- [ ] Chrome extension for quick saves to specific niche
- [ ] Image similarity detection for variants
- [ ] Niche templates (pre-configured for common industries)
- [ ] Niche sharing/collaboration
- [ ] Deployment to cloud (AWS/Vercel)
- [ ] Billing integration (Stripe) for premium features

---

## Clerk Setup Checklist

### 1. Create Clerk Application

1. Go to [dashboard.clerk.com](https://dashboard.clerk.com)
2. Create new application: "MetAds"
3. Select authentication methods:
   - [x] Email + Password
   - [x] Google OAuth
   - [ ] GitHub OAuth (optional)
   - [x] Magic Link

### 2. Configure OAuth Providers

**Google OAuth:**
1. Go to Google Cloud Console
2. Create OAuth 2.0 credentials
3. Add authorized redirect URI: `https://clerk.your-domain.com/v1/oauth_callback`
4. Copy Client ID and Secret to Clerk dashboard

### 3. Configure Webhooks

1. In Clerk dashboard, go to Webhooks
2. Add endpoint: `https://your-api-domain.com/api/auth/webhook`
3. Select events:
   - `user.created`
   - `user.updated`
   - `user.deleted`
4. Copy Signing Secret to backend `.env`

### 4. Configure Redirect URLs

**Development:**
- Sign-in: `http://localhost:5173/sign-in`
- Sign-up: `http://localhost:5173/sign-up`
- After sign-in: `http://localhost:5173/`
- After sign-up: `http://localhost:5173/`

**Production:**
- Update all URLs to use production domain

### 5. Customize Appearance

1. In Clerk dashboard, go to Customization
2. Upload logo
3. Set brand colors to match MetAds theme
4. Customize email templates

---

*Document Version: 2.0*
*Created: January 30, 2026*
*Updated: January 31, 2026 - Added Clerk OAuth authentication*
*Status: Planning*
