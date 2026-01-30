# AdSpy UI/UX Wireframes

## Design Philosophy

**Core Principle:** Clean, focused, progressive disclosure - the opposite of BigSpy's information overload.

**Key Metrics to Highlight:**
- Days Active (proxy for ad performance)
- Creative Preview (visual-first approach)
- Page/Advertiser Name
- Platform Distribution
- CTA Type

---

## 1. DESKTOP LAYOUT (>1024px)

Three-column layout with persistent views.

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│  HEADER                                                            [Logo]  [Account] │
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
│  ────────────────  │  ││ ◻ │ OpusClip           │  │  │    (Large image/video   │   │
│                    │  │└───┘ Turn long videos...│  │  │     preview area)       │   │
│  Platform          │  │      IG FB · 67 days    │  │  │                         │   │
│  ○ All             │  │      [Learn More]       │  │  │                         │   │
│  ○ Instagram       │  └─────────────────────────┘  │  └─────────────────────────┘   │
│  ○ Facebook        │                               │                                 │
│  ○ Messenger       │  ┌─────────────────────────┐  │  PAGE                           │
│                    │  │┌───┐                    │  │  ─────────────────────────────  │
│  Country           │  ││ ◻ │ Descript           │  │  OpusClip                       │
│  [US, BR      ▼]   │  │└───┘ Edit videos as...  │  │  @opusclip · Verified           │
│                    │  │      IG · 45 days       │  │                                 │
│  Status            │  │      [Try Free]         │  │  METRICS                        │
│  ○ All             │  └─────────────────────────┘  │  ─────────────────────────────  │
│  ● Active          │                               │  Started: Dec 1, 2025           │
│  ○ Inactive        │  ┌─────────────────────────┐  │  Days Active: 67                │
│                    │  │┌───┐                    │  │  Platforms: IG, FB              │
│  Days Active       │  ││ ◻ │ Captions.ai        │  │  Status: ● Active               │
│  Min: [7   ]       │  │└───┘ Auto-generate...   │  │                                 │
│  Max: [    ]       │  │      IG FB · 34 days    │  │  AD COPY                        │
│                    │  │      [Get Started]      │  │  ─────────────────────────────  │
│  Date Range        │  └─────────────────────────┘  │  Headline:                      │
│  [Last 30 days ▼]  │                               │  "Turn long videos into         │
│                    │  ┌─────────────────────────┐  │   viral clips in one click"     │
│                    │  │┌───┐                    │  │                                 │
│  ┌──────────────┐  │  ││ ◻ │ Kapwing            │  │  Body:                          │
│  │   SEARCH     │  │  │└───┘ Create content...  │  │  "Stop spending hours editing.  │
│  └──────────────┘  │  │      IG · 28 days       │  │   OpusClip uses AI to find the  │
│                    │  │      [Sign Up]          │  │   best moments in your long     │
│                    │  └─────────────────────────┘  │   videos and turns them into    │
│                    │                               │   viral shorts automatically."  │
│                    │  ┌─────────────────────────┐  │                                 │
│                    │  │┌───┐                    │  │  CTA: Learn More                │
│                    │  ││ ◻ │ InVideo            │  │  Link: opus.pro/get-started     │
│                    │  │└───┘ Make videos in...  │  │                                 │
│                    │  │      FB · 21 days       │  │  ─────────────────────────────  │
│                    │  │      [Try Now]          │  │                                 │
│                    │  └─────────────────────────┘  │  [View on Meta]  [Save]  [Copy] │
│                    │                               │                                 │
│                    │  ─────────────────────────    │                                 │
│                    │  Load more results...         │                                 │
│                    │                               │                                 │
├────────────────────┴───────────────────────────────┴─────────────────────────────────┤
│  FOOTER                                                              © 2026 MetAds   │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

### Desktop Column Widths
- Search Panel: ~250px (fixed)
- Results List: ~350px (fixed)
- Ad Detail: remaining space (flexible, min 400px)

---

## 2. TABLET LAYOUT (768px - 1024px)

Two-column layout with collapsible search.

```
┌────────────────────────────────────────────────────────────────────┐
│  HEADER                                        [Logo]   [Account]  │
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
│  ││   │ OpusClip         │  │  │                              │   │
│  ││ ◻ │ Turn long vid... │  │  │                              │   │
│  │└───┘ IG FB · 67 days  │  │  │                              │   │
│  └───────────────────────┘  │  └──────────────────────────────┘   │
│                             │                                      │
│  ┌───────────────────────┐  │  OpusClip · @opusclip                │
│  │┌───┐                  │  │  ────────────────────────────────   │
│  ││   │ Descript         │  │                                      │
│  ││ ◻ │ Edit videos...   │  │  ● Active · 67 days · IG, FB         │
│  │└───┘ IG · 45 days     │  │  Started: Dec 1, 2025                │
│  └───────────────────────┘  │                                      │
│                             │  HEADLINE                            │
│  ┌───────────────────────┐  │  "Turn long videos into viral        │
│  │┌───┐                  │  │   clips in one click"                │
│  ││   │ Captions.ai      │  │                                      │
│  ││ ◻ │ Auto-generate... │  │  BODY                                │
│  │└───┘ IG FB · 34 days  │  │  "Stop spending hours editing.       │
│  └───────────────────────┘  │   OpusClip uses AI to find the       │
│                             │   best moments in your long videos   │
│  ┌───────────────────────┐  │   and turns them into viral shorts   │
│  │┌───┐                  │  │   automatically."                    │
│  ││   │ Kapwing          │  │                                      │
│  ││ ◻ │ Create content..│  │  CTA: [Learn More]                   │
│  │└───┘ IG · 28 days     │  │  Link: opus.pro/get-started          │
│  └───────────────────────┘  │                                      │
│                             │  ──────────────────────────────────  │
│  Load more...               │  [View on Meta]  [Save]  [Copy]      │
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

Single column with bottom tab navigation.

### 3A. Mobile: Search View (Tab 1)

```
┌─────────────────────────────────┐
│  ≡  MetAds              [User]  │
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
│  ≡  MetAds              [User]  │
├─────────────────────────────────┤
│                                 │
│  "video editing ai"             │
│  247 results · Active · US, BR  │
│  ─────────────────────────────  │
│                                 │
│  ┌───────────────────────────┐  │
│  │ ┌─────┐                   │  │
│  │ │     │  OpusClip         │  │
│  │ │  ◻  │  ───────────────  │  │
│  │ │     │  Turn long videos │  │
│  │ └─────┘  into viral cli...│  │
│  │                           │  │
│  │  IG FB    67 days   >     │  │
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
│  │  IG FB    34 days    >    │  │
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
│  ─────────────────────────────  │
│                                 │
│  ┌─────────┬─────────┬───────┐  │
│  │ 67 days │  IG FB  │ Active│  │
│  │ active  │         │   ●   │  │
│  └─────────┴─────────┴───────┘  │
│                                 │
│  Started: December 1, 2025      │
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

### 3D. Mobile: Saved Ads View (Tab 3)

```
┌─────────────────────────────────┐
│  ≡  MetAds              [User]  │
├─────────────────────────────────┤
│                                 │
│  SAVED ADS                      │
│  12 ads saved                   │
│  ─────────────────────────────  │
│                                 │
│  ┌───────────────────────────┐  │
│  │ ┌─────┐                   │  │
│  │ │     │  OpusClip         │  │
│  │ │  ◻  │  ───────────────  │  │
│  │ │     │  Turn long videos │  │
│  │ └─────┘  Saved: Jan 28    │  │
│  │                           │  │
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
│   No ads found for        │   │   Something went wrong    │
│   "your search term"      │   │                           │
│                           │   │   We couldn't load the    │
│   Try adjusting your      │   │   results. Please check   │
│   filters or search       │   │   your connection.        │
│   for different keywords  │   │                           │
│                           │   │   [Try Again]             │
│   [Clear Filters]         │   │                           │
│                           │   │                           │
└───────────────────────────┘   └───────────────────────────┘
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

PLATFORM ICONS
┌─────────────────────────────────┐
│  [IG]  [FB]  [MSG]  [AN]        │
│                                 │
│  Each platform gets a subtle    │
│  icon or abbreviated badge      │
└─────────────────────────────────┘
```

### Typography Scale

```
DESKTOP                          MOBILE
─────────────────────────────    ─────────────────────────────
Page Name:     16px semibold     Page Name:     15px semibold
Headline:      14px regular      Headline:      14px regular
Meta info:     12px regular      Meta info:     12px regular
Days badge:    14px bold         Days badge:    14px bold

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

---

## 7. USER FLOW DIAGRAM

```
                    ┌─────────────┐
                    │   LANDING   │
                    │   (Search)  │
                    └──────┬──────┘
                           │
                    User enters
                    search query
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
              ┌────────────┼────────────┐       │
              │            │            │       │
              ▼            ▼            ▼       │
        ┌──────────┐ ┌──────────┐ ┌──────────┐ │
        │  SAVE    │ │  VIEW    │ │  COPY    │ │
        │  AD      │ │  ON META │ │  TEXT    │ │
        └────┬─────┘ └──────────┘ └──────────┘ │
             │                                  │
             ▼                                  │
        ┌──────────┐                           │
        │  SAVED   │◄──────────────────────────┘
        │  ADS     │
        └──────────┘
```

---

## 8. KEY DIFFERENCES FROM BIGSPY

| Aspect | BigSpy | MetAds (Our Approach) |
|--------|--------|----------------------|
| Information density | Very high - everything visible | Progressive disclosure |
| Primary navigation | Complex menu system | Simple 3-tab mobile, 3-column desktop |
| Filters | Always expanded, many options | Collapsible, focused on key filters |
| Creative preview | Small thumbnails | Large, prominent previews |
| Key metric | Multiple metrics competing | "Days Active" as primary signal |
| Mobile experience | Desktop-first, cramped on mobile | Mobile-first, native feel |
| Visual style | Data-table aesthetic | Card-based, modern UI |
| Cognitive load | High - need to scan everything | Low - clear hierarchy |

---

## 9. NEXT STEPS

1. **Validate with real data** - Mock up with actual Meta Ad Library results
2. **Test on devices** - Verify touch targets and readability on iPhone
3. **Define color palette** - Choose primary, secondary, and status colors
4. **Create component library** - Build reusable UI components
5. **Prototype interactions** - Add transitions and micro-animations

---

*Document Version: 1.0*
*Created: January 30, 2026*
*Status: Ideation Phase*
