# MetAds UI/UX Wireframes

## Design Philosophy

**Core Principle:** Clean, focused, progressive disclosure - the opposite of BigSpy's information overload.

**Key Concept: Niches** - Users organize their research into separate "niches" (analysis projects), each containing its own collection of ads, saved items, and insights. This provides clear context and data isolation for different research areas.

**Key Metrics to Highlight:**
- Days Active (proxy for ad performance)
- Related Ads / Variants (shows active A/B testing)
- Creative Preview (visual-first approach)
- Page/Advertiser Name
- Platform Distribution
- CTA Type

---

## 0. NICHE SELECTOR (Landing Page)

The Niche Selector is the entry point to the application. Users must select or create a niche before accessing the search workspace.

### 0A. Desktop: Niche Selector

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│  HEADER                                                   MetAds          [+ New]    │
├──────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  YOUR NICHES                                                                         │
│  ─────────────────────────────────────────────────────────────────────────────────   │
│                                                                                      │
│  ┌────────────────────────┐  ┌────────────────────────┐  ┌────────────────────────┐ │
│  │ 🎬                     │  │ 📊                     │  │ 🗳️                     │ │
│  │                        │  │                        │  │                        │ │
│  │ Video Editing Apps     │  │ CRMs                   │  │ Election 2026          │ │
│  │                        │  │                        │  │                        │ │
│  │ ─────────────────────  │  │ ─────────────────────  │  │ ─────────────────────  │ │
│  │                        │  │                        │  │                        │ │
│  │ 342 ads · 24 saved     │  │ 187 ads · 12 saved     │  │ 89 ads · 8 saved       │ │
│  │ Last collected: 2h ago │  │ Last collected: 1d ago │  │ Last collected: 3d ago │ │
│  │                        │  │                        │  │                        │ │
│  └────────────────────────┘  └────────────────────────┘  └────────────────────────┘ │
│         (purple accent)            (green accent)              (blue accent)         │
│                                                                                      │
│  ┌────────────────────────┐                                                         │
│  │                        │                                                         │
│  │          +             │                                                         │
│  │                        │                                                         │
│  │    Create New Niche    │                                                         │
│  │                        │                                                         │
│  └────────────────────────┘                                                         │
│       (dashed border)                                                               │
│                                                                                      │
├──────────────────────────────────────────────────────────────────────────────────────┤
│  FOOTER                                                              © 2026 MetAds   │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

### 0B. Mobile: Niche Selector

```
┌─────────────────────────────────┐
│  ≡  MetAds              [+ New] │
├─────────────────────────────────┤
│                                 │
│  YOUR NICHES                    │
│  ─────────────────────────────  │
│                                 │
│  ┌───────────────────────────┐  │
│  │ 🎬 Video Editing Apps     │  │
│  │ ─────────────────────────  │  │
│  │ 342 ads · 24 saved        │  │
│  │ Last collected: 2h ago    │  │
│  └───────────────────────────┘  │
│       (purple left border)      │
│                                 │
│  ┌───────────────────────────┐  │
│  │ 📊 CRMs                   │  │
│  │ ─────────────────────────  │  │
│  │ 187 ads · 12 saved        │  │
│  │ Last collected: 1d ago    │  │
│  └───────────────────────────┘  │
│       (green left border)       │
│                                 │
│  ┌───────────────────────────┐  │
│  │ 🗳️ Election 2026          │  │
│  │ ─────────────────────────  │  │
│  │ 89 ads · 8 saved          │  │
│  │ Last collected: 3d ago    │  │
│  └───────────────────────────┘  │
│       (blue left border)        │
│                                 │
│  ┌───────────────────────────┐  │
│  │           +               │  │
│  │    Create New Niche       │  │
│  └───────────────────────────┘  │
│                                 │
└─────────────────────────────────┘
```

### 0C. Niche Card Component

```
┌───────────────────────────────────────────────────────┐
│                                                       │
│  NICHE CARD SPECIFICATIONS                            │
│  ───────────────────────────────────────────────────  │
│                                                       │
│  Desktop card:   280px width, 180px height            │
│  Mobile card:    100% width - 32px, 100px height      │
│                                                       │
│  Elements:                                            │
│  - Icon/Emoji:   32px (desktop), 24px (mobile)        │
│  - Name:         18px semibold                        │
│  - Stats:        14px regular, gray                   │
│  - Last collect: 12px regular, light gray             │
│                                                       │
│  Color accent:                                        │
│  - Desktop: Full card has subtle tint of niche color  │
│  - Mobile: 4px left border in niche color             │
│                                                       │
│  Hover state:                                         │
│  - Slight elevation (shadow)                          │
│  - Cursor pointer                                     │
│                                                       │
└───────────────────────────────────────────────────────┘
```

### 0D. Create Niche Modal

```
┌─────────────────────────────────────────────────────┐
│  CREATE NEW NICHE                              [×]  │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Name *                                             │
│  ┌─────────────────────────────────────────────┐   │
│  │ e.g., Video Editing Apps                    │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  Description                                        │
│  ┌─────────────────────────────────────────────┐   │
│  │ e.g., AI-powered video editing tools and    │   │
│  │ competitor analysis                         │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  Icon                                               │
│  ┌─────────────────────────────────────────────┐   │
│  │ [🎬] [📊] [🗳️] [💰] [🏠] [🎮] [📱] [more ▼] │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  Color                                              │
│  ┌─────────────────────────────────────────────┐   │
│  │ [●] [●] [●] [●] [●] [●] [●] [●]             │   │
│  │ purple green blue orange pink teal red gray │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  Keywords (for data collection)                     │
│  ┌─────────────────────────────────────────────┐   │
│  │ video editing ai, opus clip, descript       │   │
│  │ (comma separated)                           │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  Default Countries                                  │
│  ┌─────────────────────────────────────────────┐   │
│  │ [US ×] [BR ×] [+ Add]                       │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  ─────────────────────────────────────────────────  │
│                                                     │
│                      [Cancel]  [Create Niche]       │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### 0E. Empty State: No Niches

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│                       📁                            │
│                                                     │
│           Welcome to MetAds!                        │
│                                                     │
│     Create your first niche to start               │
│     collecting and analyzing ads.                   │
│                                                     │
│     A niche is a research project focused           │
│     on a specific market or topic.                  │
│                                                     │
│         ┌─────────────────────────┐                │
│         │   Create Your First     │                │
│         │        Niche            │                │
│         └─────────────────────────┘                │
│                                                     │
│     Examples:                                       │
│     • "Video Editing Apps"                          │
│     • "E-commerce Fashion Brands"                   │
│     • "SaaS Productivity Tools"                     │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## 1. DESKTOP LAYOUT (>1024px)

Three-column layout with persistent views, **scoped to the selected niche**.

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│  [← Niches]  🎬 Video Editing Apps                              [⚙️]  [🔄 Collect]   │
├────────────────────┬───────────────────────────────┬─────────────────────────────────┤
│                    │                               │                                 │
│  SEARCH PANEL      │  RESULTS LIST                 │  AD DETAIL                      │
│  ────────────────  │  ────────────────────────     │  ────────────────────────────   │
│                    │                               │                                 │
│  ┌──────────────┐  │  Found: 247 ads               │  ┌─────────────────────────┐   │
│  │ Search...    │  │  Sorted by: Days Active ▼     │  │                         │   │
│  └──────────────┘  │                               │  │                         │   │
│                    │  ┌─────────────────────────┐  │  │    CREATIVE PREVIEW     │   │
│  FILTERS           │  │┌───┐                    │  │  │                         │   │
│  ────────────────  │  ││ ◻ │ OpusClip        ⭐ │  │  │    (Large image/video   │   │
│                    │  │└───┘ Turn long videos...│  │  │     preview area)       │   │
│  Platform          │  │      IG FB · 67 days    │  │  │                         │   │
│  ○ All             │  │      [Learn More]       │  │  │                         │   │
│  ○ Instagram       │  └─────────────────────────┘  │  └─────────────────────────┘   │
│  ○ Facebook        │                               │                                 │
│  ○ Messenger       │  ┌─────────────────────────┐  │  PAGE                           │
│                    │  │┌───┐                    │  │  ─────────────────────────────  │
│  Country           │  ││ ◻ │ Descript           │  │  OpusClip                       │
│  [US, BR      ▼]   │  │└───┘ Edit videos as...  │  │  @opusclip · Verified           │
│                    │  │      IG · 45 days       │  │  [★ Mark as Competitor]         │
│  Status            │  │      [Try Free]         │  │                                 │
│  ○ All             │  └─────────────────────────┘  │  METRICS                        │
│  ● Active          │                               │  ─────────────────────────────  │
│  ○ Inactive        │  ┌─────────────────────────┐  │  Started: Dec 1, 2025           │
│                    │  │┌───┐                    │  │  Days Active: 67                │
│  Days Active       │  ││ ◻ │ Captions.ai        │  │  Platforms: IG, FB              │
│  Min: [7   ]       │  │└───┘ Auto-generate...   │  │  Status: ● Active               │
│  Max: [    ]       │  │      IG FB · 34 days    │  │  Related Ads: [4 variants →]    │
│                    │  │      [Get Started]      │  │                                 │
│  Date Range        │  └─────────────────────────┘  │  AD COPY                        │
│  [Last 30 days ▼]  │                               │  ─────────────────────────────  │
│                    │  ┌─────────────────────────┐  │  Headline:                      │
│                    │  │┌───┐                    │  │  "Turn long videos into         │
│  ┌──────────────┐  │  ││ ◻ │ Kapwing            │  │   viral clips in one click"     │
│  │   SEARCH     │  │  │└───┘ Create content...  │  │                                 │
│  └──────────────┘  │  │      IG · 28 days       │  │  Body:                          │
│                    │  │      [Sign Up]          │  │  "Stop spending hours editing.  │
│                    │  └─────────────────────────┘  │   OpusClip uses AI to find the  │
│                    │                               │   best moments in your long     │
│                    │  ─────────────────────────    │   videos..."                    │
│                    │  Load more results...         │                                 │
│                    │                               │  CTA: Learn More                │
│                    │                               │  Link: opus.pro/get-started     │
│                    │                               │                                 │
│                    │                               │  ─────────────────────────────  │
│                    │                               │                                 │
│                    │                               │  [View on Meta]  [Save]  [Copy] │
│                    │                               │                                 │
├────────────────────┴───────────────────────────────┴─────────────────────────────────┤
│  FOOTER                                                              © 2026 MetAds   │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

### Desktop Header (Workspace)

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                      │
│  WORKSPACE HEADER SPECIFICATIONS                                                     │
│  ──────────────────────────────────────────────────────────────────────────────────  │
│                                                                                      │
│  [← Niches]           Back navigation to Niche Selector                              │
│                                                                                      │
│  🎬 Video Editing Apps   Niche icon + name (with niche color accent underline)       │
│                                                                                      │
│  [⚙️]                  Niche Settings (edit name, keywords, colors)                  │
│                                                                                      │
│  [🔄 Collect]          Trigger data collection for this niche                        │
│                        - Shows spinner while collecting                              │
│                        - Shows "Collecting... 23 new" during progress                │
│                        - Shows "Last: 2h ago" when idle                              │
│                                                                                      │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

### Desktop Column Widths
- Search Panel: ~250px (fixed)
- Results List: ~350px (fixed)
- Ad Detail: remaining space (flexible, min 400px)

---

## 2. TABLET LAYOUT (768px - 1024px)

Two-column layout with collapsible search, **scoped to the selected niche**.

```
┌────────────────────────────────────────────────────────────────────┐
│  [← Niches]  🎬 Video Editing Apps                 [⚙️] [Collect]  │
├────────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────────────┐    │
│  │ 🔍 video editing ai                          [Filters ▼]   │    │
│  └────────────────────────────────────────────────────────────┘    │
├─────────────────────────────┬──────────────────────────────────────┤
│                             │                                      │
│  RESULTS LIST               │  AD DETAIL                           │
│  ─────────────────────────  │  ──────────────────────────────────  │
│                             │                                      │
│  247 ads · Active · US, BR  │  ┌──────────────────────────────┐   │
│                             │  │                              │   │
│  ┌───────────────────────┐  │  │                              │   │
│  │┌───┐                  │  │  │      CREATIVE PREVIEW        │   │
│  ││   │ OpusClip      ⭐ │  │  │                              │   │
│  ││ ◻ │ Turn long vid... │  │  │                              │   │
│  │└───┘ IG FB · 67 days  │  │  │                              │   │
│  └───────────────────────┘  │  └──────────────────────────────┘   │
│                             │                                      │
│  ┌───────────────────────┐  │  OpusClip · @opusclip                │
│  │┌───┐                  │  │  [★ Mark as Competitor]              │
│  ││   │ Descript         │  │  ────────────────────────────────   │
│  ││ ◻ │ Edit videos...   │  │                                      │
│  │└───┘ IG · 45 days     │  │  ● Active · 67 days · IG, FB         │
│  └───────────────────────┘  │  Started: Dec 1, 2025                │
│                             │  Related Ads: [4 variants →]         │
│  ┌───────────────────────┐  │                                      │
│  │┌───┐                  │  │  HEADLINE                            │
│  ││   │ Captions.ai      │  │  "Turn long videos into viral        │
│  ││ ◻ │ Auto-generate... │  │   clips in one click"                │
│  │└───┘ IG FB · 34 days  │  │                                      │
│  └───────────────────────┘  │  BODY                                │
│                             │  "Stop spending hours editing..."    │
│  ┌───────────────────────┐  │                                      │
│  │┌───┐                  │  │  CTA: [Learn More]                   │
│  ││   │ Kapwing          │  │  Link: opus.pro/get-started          │
│  ││ ◻ │ Create content..│  │                                      │
│  │└───┘ IG · 28 days     │  │  ──────────────────────────────────  │
│  └───────────────────────┘  │  [View on Meta]  [Save]  [Copy]      │
│                             │                                      │
│  Load more...               │                                      │
│                             │                                      │
├─────────────────────────────┴──────────────────────────────────────┤
│  FOOTER                                                            │
└────────────────────────────────────────────────────────────────────┘
```

### Tablet Filter Drawer (Expanded)

```
┌────────────────────────────────────────────────────────────────────┐
│  ┌────────────────────────────────────────────────────────────┐    │
│  │ 🔍 video editing ai                          [Filters ▲]   │    │
│  └────────────────────────────────────────────────────────────┘    │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │                                                            │    │
│  │  Platform        Country         Status        Days Active │    │
│  │  [All      ▼]    [US, BR    ▼]   [Active ▼]   [7+     ▼]  │    │
│  │                                                            │    │
│  │  Date Range                      [Apply Filters]  [Reset]  │    │
│  │  [Last 30 days ▼]                                          │    │
│  │                                                            │    │
│  └────────────────────────────────────────────────────────────┘    │
├────────────────────────────────────────────────────────────────────┤
```

---

## 3. MOBILE LAYOUT - iPhone (<768px)

Single column with bottom tab navigation, **scoped to the selected niche**.

### 3A. Mobile: Search View (Tab 1)

```
┌─────────────────────────────────┐
│  ←  🎬 Video Editing      [⚙️]  │
├─────────────────────────────────┤
│                                 │
│  SEARCH                         │
│  ─────────────────────────────  │
│                                 │
│  ┌───────────────────────────┐  │
│  │ 🔍 Search keywords...     │  │
│  └───────────────────────────┘  │
│                                 │
│  Platform                       │
│  ┌───────────────────────────┐  │
│  │ All platforms           ▼ │  │
│  └───────────────────────────┘  │
│                                 │
│  Country                        │
│  ┌───────────────────────────┐  │
│  │ Select countries...     ▼ │  │
│  └───────────────────────────┘  │
│                                 │
│  Status                         │
│  ┌───────────────────────────┐  │
│  │ Active only             ▼ │  │
│  └───────────────────────────┘  │
│                                 │
│  Minimum Days Active            │
│  ┌───────────────────────────┐  │
│  │ 7 days                  ▼ │  │
│  └───────────────────────────┘  │
│                                 │
│  Date Range                     │
│  ┌───────────────────────────┐  │
│  │ Last 30 days            ▼ │  │
│  └───────────────────────────┘  │
│                                 │
│  ┌───────────────────────────┐  │
│  │                           │  │
│  │         SEARCH            │  │
│  │                           │  │
│  └───────────────────────────┘  │
│                                 │
│                                 │
│                                 │
├─────────────────────────────────┤
│  [🔍 Search]  [📋 Results]  [⭐]│
│     active                      │
└─────────────────────────────────┘
```

### 3B. Mobile: Results View (Tab 2)

```
┌─────────────────────────────────┐
│  ←  🎬 Video Editing      [⚙️]  │
├─────────────────────────────────┤
│                                 │
│  "video editing ai"             │
│  247 results · Active · US, BR  │
│  ─────────────────────────────  │
│                                 │
│  ┌───────────────────────────┐  │
│  │ ┌─────┐                   │  │
│  │ │     │  OpusClip      ⭐ │  │
│  │ │  ◻  │  ───────────────  │  │
│  │ │     │  Turn long videos │  │
│  │ └─────┘  into viral cli...│  │
│  │                           │  │
│  │  IG FB  67 days  4 var >  │  │
│  └───────────────────────────┘  │
│                                 │
│  ┌───────────────────────────┐  │
│  │ ┌─────┐                   │  │
│  │ │     │  Descript         │  │
│  │ │  ◻  │  ───────────────  │  │
│  │ │     │  Edit videos as   │  │
│  │ └─────┘  easily as doc... │  │
│  │                           │  │
│  │  IG       45 days    >    │  │
│  └───────────────────────────┘  │
│                                 │
│  ┌───────────────────────────┐  │
│  │ ┌─────┐                   │  │
│  │ │     │  Captions.ai      │  │
│  │ │  ◻  │  ───────────────  │  │
│  │ │     │  Auto-generate    │  │
│  │ └─────┘  captions and...  │  │
│  │                           │  │
│  │  IG FB  34 days  2 var >  │  │
│  └───────────────────────────┘  │
│                                 │
│  ┌───────────────────────────┐  │
│  │      Load more ads...     │  │
│  └───────────────────────────┘  │
│                                 │
├─────────────────────────────────┤
│  [🔍 Search]  [📋 Results]  [⭐]│
│                  active         │
└─────────────────────────────────┘
```

### 3C. Mobile: Ad Detail View (Full Screen Overlay)

```
┌─────────────────────────────────┐
│  ←  Ad Detail           [Save]  │
├─────────────────────────────────┤
│                                 │
│  ┌───────────────────────────┐  │
│  │                           │  │
│  │                           │  │
│  │                           │  │
│  │     CREATIVE PREVIEW      │  │
│  │                           │  │
│  │     (Full-width image     │  │
│  │      or video player)     │  │
│  │                           │  │
│  │                           │  │
│  │                           │  │
│  └───────────────────────────┘  │
│                                 │
│  OpusClip                       │
│  @opusclip · Verified           │
│  [★ Mark as Competitor]         │
│  ─────────────────────────────  │
│                                 │
│  ┌─────────┬─────────┬───────┐  │
│  │ 67 days │  IG FB  │ Active│  │
│  │ active  │         │   ●   │  │
│  └─────────┴─────────┴───────┘  │
│                                 │
│  Started: December 1, 2025      │
│                                 │
│  RELATED ADS                    │
│  ─────────────────────────────  │
│  ┌───────────────────────────┐  │
│  │  [4 variants from this    │  │
│  │   advertiser →]           │  │
│  │   Longest: 67 days        │  │
│  │   Newest: 12 days ago     │  │
│  └───────────────────────────┘  │
│                                 │
│  HEADLINE                       │
│  ─────────────────────────────  │
│  "Turn long videos into viral   │
│   clips in one click"           │
│                                 │
│  BODY                           │
│  ─────────────────────────────  │
│  "Stop spending hours editing.  │
│   OpusClip uses AI to find the  │
│   best moments in your long     │
│   videos and turns them into    │
│   viral shorts automatically.   │
│   Try it free today!"           │
│                                 │
│  CTA                            │
│  ─────────────────────────────  │
│  [Learn More]                   │
│                                 │
│  LANDING PAGE                   │
│  ─────────────────────────────  │
│  opus.pro/get-started           │
│                                 │
│  ─────────────────────────────  │
│                                 │
│  ┌───────────┐  ┌─────────────┐ │
│  │View on    │  │  Copy Ad    │ │
│  │   Meta    │  │    Text     │ │
│  └───────────┘  └─────────────┘ │
│                                 │
└─────────────────────────────────┘
```

### 3D. Mobile: Related Ads View (Slide-in Panel)

```
┌─────────────────────────────────┐
│  ←  Related Ads (4)     OpusClip│
├─────────────────────────────────┤
│                                 │
│  VARIANT INSIGHTS               │
│  in "Video Editing Apps"        │
│  ─────────────────────────────  │
│  Longest running: 67 days       │
│  All use same CTA: Learn More   │
│  Headlines differ (A/B test)    │
│                                 │
│  ─────────────────────────────  │
│                                 │
│  ┌───────────────────────────┐  │
│  │ ┌─────┐  ★ LONGEST        │  │
│  │ │     │  ───────────────  │  │
│  │ │  ◻  │  "Turn long       │  │
│  │ │     │   videos into..." │  │
│  │ └─────┘                   │  │
│  │  67 days · IG FB          │  │
│  └───────────────────────────┘  │
│                                 │
│  ┌───────────────────────────┐  │
│  │ ┌─────┐                   │  │
│  │ │     │  ───────────────  │  │
│  │ │  ◻  │  "Stop wasting    │  │
│  │ │     │   hours on..."    │  │
│  │ └─────┘                   │  │
│  │  45 days · IG FB          │  │
│  └───────────────────────────┘  │
│                                 │
│  ┌───────────────────────────┐  │
│  │ ┌─────┐  ✦ NEWEST         │  │
│  │ │     │  ───────────────  │  │
│  │ │  ◻  │  "AI finds your   │  │
│  │ │     │   best clips..."  │  │
│  │ └─────┘                   │  │
│  │  12 days · IG             │  │
│  └───────────────────────────┘  │
│                                 │
│  ┌───────────────────────────┐  │
│  │ ┌─────┐                   │  │
│  │ │     │  ───────────────  │  │
│  │ │  ◻  │  "Go viral with   │  │
│  │ │     │   one click..."   │  │
│  │ └─────┘                   │  │
│  │  28 days · FB             │  │
│  └───────────────────────────┘  │
│                                 │
├─────────────────────────────────┤
│  [🔍 Search]  [📋 Results]  [⭐]│
└─────────────────────────────────┘
```

### 3E. Mobile: Saved Ads View (Tab 3)

```
┌─────────────────────────────────┐
│  ←  🎬 Video Editing      [⚙️]  │
├─────────────────────────────────┤
│                                 │
│  SAVED ADS                      │
│  in "Video Editing Apps"        │
│  12 ads saved                   │
│  ─────────────────────────────  │
│                                 │
│  ┌───────────────────────────┐  │
│  │ ┌─────┐                   │  │
│  │ │     │  OpusClip         │  │
│  │ │  ◻  │  ───────────────  │  │
│  │ │     │  Turn long videos │  │
│  │ └─────┘  Saved: Jan 28    │  │
│  │         "Great hook!"     │  │
│  │  IG FB    67 days    >    │  │
│  └───────────────────────────┘  │
│                                 │
│  ┌───────────────────────────┐  │
│  │ ┌─────┐                   │  │
│  │ │     │  Runway ML        │  │
│  │ │  ◻  │  ───────────────  │  │
│  │ │     │  AI video gen...  │  │
│  │ └─────┘  Saved: Jan 25    │  │
│  │                           │  │
│  │  IG       52 days    >    │  │
│  └───────────────────────────┘  │
│                                 │
│  (empty state if no saved)     │
│  ┌───────────────────────────┐  │
│  │                           │  │
│  │   ⭐ No saved ads yet     │  │
│  │   in "Video Editing Apps" │  │
│  │                           │  │
│  │   Tap the save icon on    │  │
│  │   any ad to bookmark it   │  │
│  │   for later.              │  │
│  │                           │  │
│  │   [Start Searching]       │  │
│  │                           │  │
│  └───────────────────────────┘  │
│                                 │
├─────────────────────────────────┤
│  [🔍 Search]  [📋 Results]  [⭐]│
│                          active │
└─────────────────────────────────┘
```

### 3F. Mobile: Niche Settings View

```
┌─────────────────────────────────┐
│  ←  Niche Settings              │
├─────────────────────────────────┤
│                                 │
│  🎬 VIDEO EDITING APPS          │
│  ─────────────────────────────  │
│                                 │
│  Name                           │
│  ┌───────────────────────────┐  │
│  │ Video Editing Apps        │  │
│  └───────────────────────────┘  │
│                                 │
│  Description                    │
│  ┌───────────────────────────┐  │
│  │ AI-powered video editing  │  │
│  │ tools and competitor      │  │
│  │ analysis                  │  │
│  └───────────────────────────┘  │
│                                 │
│  Icon                           │
│  [🎬] [📊] [🗳️] [💰] [🏠] [more]│
│                                 │
│  Color                          │
│  [●] [●] [●] [●] [●] [●]       │
│   ▲ selected                    │
│                                 │
│  Keywords                       │
│  ─────────────────────────────  │
│  ┌───────────────────────────┐  │
│  │ video editing ai     [×]  │  │
│  │ opus clip            [×]  │  │
│  │ descript             [×]  │  │
│  │ [+ Add keyword]           │  │
│  └───────────────────────────┘  │
│                                 │
│  Default Countries              │
│  [US ×] [BR ×] [+ Add]         │
│                                 │
│  ─────────────────────────────  │
│                                 │
│  COLLECTION HISTORY             │
│  ─────────────────────────────  │
│  Today 2:30 PM    +23 new ads  │
│  Yesterday        +45 new ads  │
│  Jan 28           +12 new ads  │
│                                 │
│  ─────────────────────────────  │
│                                 │
│  ┌───────────────────────────┐  │
│  │      Save Changes         │  │
│  └───────────────────────────┘  │
│                                 │
│  ┌───────────────────────────┐  │
│  │      Delete Niche         │  │
│  └───────────────────────────┘  │
│         (red text)              │
│                                 │
└─────────────────────────────────┘
```

---

## 4. INTERACTION PATTERNS

### 4A. Result Card States

```
NORMAL STATE                    HOVER/FOCUS STATE
┌───────────────────────────┐   ┌───────────────────────────┐
│ ┌─────┐                   │   │ ┌─────┐                   │
│ │     │  Page Name        │   │ │     │  Page Name        │
│ │  ◻  │  Headline text... │   │ │  ◻  │  Headline text... │
│ └─────┘  IG · 45 days     │   │ └─────┘  IG · 45 days     │
└───────────────────────────┘   └───────────────────────────┘
 Border: none                    Border: 2px primary color
 Background: white               Background: light highlight


SELECTED STATE                  LOADING STATE
┌───────────────────────────┐   ┌───────────────────────────┐
│ ┌─────┐                   │   │ ┌─────┐                   │
│ │     │  Page Name        │   │ │ ░░░ │  ░░░░░░░░░░░░░░  │
│ │  ◻  │  Headline text... │   │ │ ░░░ │  ░░░░░░░░░░░░░░  │
│ └─────┘  IG · 45 days     │   │ └─────┘  ░░░░░░░░░░░░░░  │
└───────────────────────────┘   └───────────────────────────┘
 Border: 2px primary color       Skeleton loading animation
 Background: primary light
 Left bar: 4px primary color


SAVED STATE (additional indicator)
┌───────────────────────────┐
│ ┌─────┐               ⭐  │
│ │     │  Page Name        │
│ │  ◻  │  Headline text... │
│ └─────┘  IG · 45 days     │
└───────────────────────────┘
 Star icon in top-right
 Indicates ad is saved in this niche
```

### 4B. Filter Chips (Mobile/Tablet)

```
Active filters shown as dismissible chips:

┌─────────────────────────────────────────────────────────┐
│  [Active ×]  [US ×]  [BR ×]  [7+ days ×]  [+ Filters]  │
└─────────────────────────────────────────────────────────┘
```

### 4C. Empty States

```
NO RESULTS                      ERROR STATE
┌───────────────────────────┐   ┌───────────────────────────┐
│                           │   │                           │
│         🔍                │   │         ⚠️                │
│                           │   │                           │
│   No ads found in         │   │   Something went wrong    │
│   "Video Editing Apps"    │   │                           │
│                           │   │   We couldn't load the    │
│   Try adjusting your      │   │   results. Please check   │
│   filters or search       │   │   your connection.        │
│   for different keywords  │   │                           │
│                           │   │   [Try Again]             │
│   [Clear Filters]         │   │                           │
│                           │   │                           │
└───────────────────────────┘   └───────────────────────────┘


NO SAVED ADS IN NICHE
┌───────────────────────────┐
│                           │
│         ⭐                │
│                           │
│   No saved ads yet in     │
│   "Video Editing Apps"    │
│                           │
│   Tap the save icon on    │
│   any ad to bookmark it   │
│   for later.              │
│                           │
│   [Start Searching]       │
│                           │
└───────────────────────────┘
```

### 4D. Collection Status Indicator

```
IDLE STATE                      COLLECTING STATE
┌───────────────────────────┐   ┌───────────────────────────┐
│                           │   │                           │
│   [🔄 Collect]            │   │   [⏳ Collecting...]      │
│                           │   │   23 new ads found        │
│   Last: 2 hours ago       │   │                           │
│                           │   │                           │
└───────────────────────────┘   └───────────────────────────┘

COMPLETED STATE (briefly shown)
┌───────────────────────────┐
│                           │
│   [✓ Done]                │
│   +45 new ads collected   │
│                           │
└───────────────────────────┘
 (reverts to idle after 3s)
```

---

## 5. VISUAL HIERARCHY

### Color Usage

```
PRIMARY ACTIONS     METRICS/BADGES       STATUS INDICATORS
┌─────────────┐    ┌──────────────┐     ┌─────────────────┐
│   Search    │    │  67 days     │     │  ● Active       │
│   Button    │    │  (prominent) │     │  (green)        │
└─────────────┘    └──────────────┘     │                 │
 Blue/Primary       Dark text on        │  ○ Inactive     │
                    light background    │  (gray)         │
                                        └─────────────────┘

NICHE COLORS (user-selectable)
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  Purple: #8B5CF6   Green: #10B981   Blue: #3B82F6      │
│  Orange: #F59E0B   Pink: #EC4899    Teal: #14B8A6      │
│  Red: #EF4444      Gray: #6B7280                       │
│                                                         │
│  Used for:                                              │
│  - Niche card accent/border                             │
│  - Workspace header underline                           │
│  - Save indicator tint                                  │
│                                                         │
└─────────────────────────────────────────────────────────┘

PLATFORM ICONS              VARIANT BADGE
┌─────────────────────────┐ ┌─────────────────────────────┐
│  [IG]  [FB]  [MSG]  [AN]│ │  [4 var]                    │
│                         │ │                             │
│  Each platform gets a   │ │  Shows number of related    │
│  subtle icon or badge   │ │  ads/variants found         │
└─────────────────────────┘ └─────────────────────────────┘

SAVED INDICATOR
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  ⭐ (filled star)  - Ad is saved in current niche      │
│  ☆ (empty star)    - Ad is not saved                   │
│                                                         │
│  The star uses the niche color as accent               │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Typography Scale

```
DESKTOP                          MOBILE
─────────────────────────────    ─────────────────────────────
Niche Name:    20px semibold     Niche Name:    18px semibold
Page Name:     16px semibold     Page Name:     15px semibold
Headline:      14px regular      Headline:      14px regular
Meta info:     12px regular      Meta info:     12px regular
Days badge:    14px bold         Days badge:    14px bold
Variant badge: 12px medium       Variant badge: 12px medium

Section headers: 13px uppercase  Section headers: 12px uppercase
Body text:       14px regular    Body text:       14px regular
```

---

## 6. COMPONENT SPECIFICATIONS

### 6A. Ad Result Card

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  DIMENSIONS                                             │
│  ─────────────────────────────────────────────────────  │
│                                                         │
│  Desktop card:   350px width, auto height               │
│  Tablet card:    100% of column, auto height            │
│  Mobile card:    100% width - 32px padding              │
│                                                         │
│  Thumbnail:      60x60px (desktop/tablet)               │
│                  80x80px (mobile - larger touch target) │
│                                                         │
│  SPACING                                                │
│  ─────────────────────────────────────────────────────  │
│                                                         │
│  Card padding:   16px                                   │
│  Card margin:    8px bottom                             │
│  Card radius:    8px                                    │
│                                                         │
│  Thumb margin:   12px right                             │
│  Text spacing:   4px between lines                      │
│  Badge spacing:  8px between badges                     │
│                                                         │
│  SAVED INDICATOR                                        │
│  ─────────────────────────────────────────────────────  │
│                                                         │
│  Position:       Top-right corner, 8px from edges       │
│  Size:           16px (desktop), 20px (mobile)          │
│  Color:          Niche accent color when saved          │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 6B. Detail Panel Creative Preview

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  CREATIVE PREVIEW AREA                                  │
│  ─────────────────────────────────────────────────────  │
│                                                         │
│  Desktop:    400px max width, 16:9 or 1:1 aspect        │
│  Tablet:     100% width, maintain aspect ratio          │
│  Mobile:     100% width, maintain aspect ratio          │
│                                                         │
│  Types supported:                                       │
│  - Static image (most common)                           │
│  - Video with play button overlay                       │
│  - Carousel with dots indicator                         │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │                                                 │   │
│  │                                                 │   │
│  │               [▶ Play]                          │   │
│  │            (video overlay)                      │   │
│  │                                                 │   │
│  │                                                 │   │
│  └─────────────────────────────────────────────────┘   │
│                    ● ○ ○ ○                              │
│               (carousel dots)                           │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 6C. Niche Card

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  NICHE CARD COMPONENT                                   │
│  ─────────────────────────────────────────────────────  │
│                                                         │
│  Desktop:                                               │
│  - Width: 280px                                         │
│  - Height: 180px                                        │
│  - Background: White with subtle niche color tint       │
│  - Border: 1px solid gray-200                           │
│  - Border-radius: 12px                                  │
│  - Hover: elevation shadow, slight scale (1.02)         │
│                                                         │
│  Mobile:                                                │
│  - Width: 100% - 32px margin                            │
│  - Height: 100px                                        │
│  - Left border: 4px solid niche color                   │
│  - Background: White                                    │
│                                                         │
│  Content:                                               │
│  - Icon: 32px (desktop), 24px (mobile)                  │
│  - Name: 18px semibold, gray-900                        │
│  - Stats: 14px regular, gray-600                        │
│  - Last collected: 12px regular, gray-400               │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 7. RELATED ADS / VARIANTS FEATURE

### 7A. Feature Overview

The Related Ads feature helps users identify A/B testing patterns and find winning ad variations by grouping ads from the same advertiser that are likely part of the same campaign. **Variants are scoped to the current niche.**

### 7B. What This Feature Enables

| Insight | Value for Reverse Engineering |
|---------|-------------------------------|
| "This ad has 4 variants" | Shows advertiser is actively testing - serious player |
| "This is the longest-running variant" | Likely the winner - study this one closely |
| "Newest variant launched 3 days ago" | They're still iterating - angle is working |
| "All variants use same CTA" | That CTA is validated across tests |
| "Headlines differ but body is same" | They're testing hooks, not core message |

### 7C. Implementation Approaches (Complexity vs Value Tradeoff)

| Approach | Implementation Effort | Detection Accuracy | Recommended Phase |
|----------|----------------------|-------------------|-------------------|
| **Temporal + Same Advertiser** | Low | Medium | MVP - Phase 1 |
| Same Page ID + ads launched within 14 days of each other | Simple date comparison | May group unrelated campaigns | Start here |
| **Add Text Similarity** | Medium | Good | Phase 2 |
| Above + compare headlines/body text for 70%+ similarity | Requires text processing | Catches true variants | Add after MVP |
| **Add Visual Similarity** | High | Excellent | Phase 3 (Premium) |
| Above + perceptual image hashing to detect similar creatives | Requires image processing | Catches creative refreshes | Future feature |

### 7D. Variant Grouping Logic

For a given ad, related ads are identified where:

1. **Same Page ID** (required - must be same advertiser)
2. **Same Niche** (required - scoped to current niche)

   AND at least ONE of:

3. **Launched within 14 days** of each other
4. **Text similarity score > 70%** (headlines or body)
5. **Same CTA button** type
6. **Same landing page URL** domain

### 7E. UI Display Rules

**In Results List (Card):**
- Show variant count badge only if > 1 variant exists
- Format: "4 var" (abbreviated for space)

**In Ad Detail Panel:**
- Show "Related Ads" section with clickable link
- Display summary: total variants, longest running, newest

**In Related Ads View:**
- Mark longest-running variant with ★ LONGEST badge
- Mark most recent variant with ✦ NEWEST badge
- Show insight summary at top (common CTA, differing elements)
- Show niche context: "in [Niche Name]"

### 7F. Variant Card Component

```
┌───────────────────────────────────────────────────────┐
│                                                       │
│  VARIANT CARD (in Related Ads list)                   │
│  ───────────────────────────────────────────────────  │
│                                                       │
│  ┌─────────────────────────────────────────────────┐  │
│  │ ┌─────┐  ★ LONGEST (or ✦ NEWEST)               │  │
│  │ │     │  ─────────────────────────────────────  │  │
│  │ │  ◻  │  "Headline text preview that may       │  │
│  │ │     │   wrap to two lines..."                │  │
│  │ └─────┘                                        │  │
│  │  45 days · IG FB · Learn More                  │  │
│  └─────────────────────────────────────────────────┘  │
│                                                       │
│  Badge shown only for:                                │
│  - ★ LONGEST = highest days_active in group          │
│  - ✦ NEWEST = most recent start_date in group        │
│                                                       │
└───────────────────────────────────────────────────────┘
```

### 7G. Variant Insights Summary

```
┌───────────────────────────────────────────────────────┐
│                                                       │
│  VARIANT INSIGHTS (top of Related Ads view)           │
│  in "Video Editing Apps"                              │
│  ───────────────────────────────────────────────────  │
│                                                       │
│  Displayed insights (when applicable):                │
│                                                       │
│  • "Longest running: 67 days"                         │
│  • "All use same CTA: Learn More"                     │
│  • "Headlines differ (A/B testing hooks)"             │
│  • "Same landing page across variants"                │
│  • "Testing across IG and FB"                         │
│                                                       │
│  These insights help users quickly understand         │
│  what the advertiser is testing and what's working.   │
│                                                       │
└───────────────────────────────────────────────────────┘
```

---

## 8. USER FLOW DIAGRAM

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
  │  Video Ed   │    │    CRMs     │    │    New      │
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
┌──────┐   ┌──────────┐   ┌──────────┐
│SEARCH│   │  SAVED   │   │ SETTINGS │
│(tab) │   │  (tab)   │   │ (button) │
└──┬───┘   └──────────┘   └──────────┘
   │
   ▼
┌─────────────┐
│   SEARCH    │──────────────┐
│  RESULTS    │              │
└──────┬──────┘              │
       │                     │
User taps                No results
a result                     │
       │                     ▼
       ▼              ┌─────────────┐
┌─────────────┐       │   EMPTY     │
│  AD DETAIL  │       │   STATE     │
│   (View)    │       └──────┬──────┘
└──────┬──────┘              │
       │              Adjust filters
       │                     │
┌──────┼──────────────────┐  │
│      │                  │  │
▼      ▼                  ▼  │
┌────┐ ┌────┐      ┌────────┐
│VIEW│ │SAVE│      │  COPY  │
│REL.│ │ AD │      │  TEXT  │
│ADS │ └──┬─┘      └────────┘
└─┬──┘    │
  │       ▼
  │  ┌──────────┐
  │  │  SAVED   │◄───────────┘
  │  │  ADS     │
  │  │(in niche)│
  │  └──────────┘
  │
  ▼
┌──────────┐
│ RELATED  │
│ ADS LIST │
│(in niche)│
└────┬─────┘
     │
Tap a variant
     │
     ▼
┌──────────┐
│AD DETAIL │
│(Variant) │
└──────────┘
```

---

## 9. KEY DIFFERENCES FROM BIGSPY

| Aspect | BigSpy | MetAds (Our Approach) |
|--------|--------|----------------------|
| Information density | Very high - everything visible | Progressive disclosure |
| Primary navigation | Complex menu system | Niche-first, then 3-tab mobile / 3-column desktop |
| Data organization | Single global pool | **Organized by Niches (research projects)** |
| Filters | Always expanded, many options | Collapsible, focused on key filters |
| Creative preview | Small thumbnails | Large, prominent previews |
| Key metric | Multiple metrics competing | "Days Active" as primary signal |
| Variant detection | Not prominently featured | Core feature with dedicated view |
| Mobile experience | Desktop-first, cramped on mobile | Mobile-first, native feel |
| Visual style | Data-table aesthetic | Card-based, modern UI |
| Cognitive load | High - need to scan everything | Low - clear hierarchy |
| Saved ads | Global saved list | **Per-niche saved ads with notes/tags** |

---

## 10. NEXT STEPS

1. **Implement Niche Selector** - Create the landing page and niche management
2. **Update workspace header** - Add niche context and navigation
3. **Validate with real data** - Mock up with actual Meta Ad Library results
4. **Test on devices** - Verify touch targets and readability on iPhone
5. **Define color palette** - Finalize niche color options
6. **Create component library** - Build reusable UI components
7. **Prototype interactions** - Add transitions and micro-animations
8. **Implement variant detection** - Start with temporal + same advertiser approach
9. **Design variant insights algorithm** - Define rules for insight generation

---

*Document Version: 2.0*
*Created: January 30, 2026*
*Updated: January 30, 2026 - Added Niches layer throughout UI*
*Status: Ideation Phase*
