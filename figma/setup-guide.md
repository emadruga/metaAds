# MetAds Figma Setup Guide

This guide walks you through creating the MetAds design in Figma, step by step.

## Table of Contents

1. [Initial Setup](#1-initial-setup)
2. [File 1: Mobile App](#2-file-1-mobile-app)
3. [File 2: Desktop & Tablet](#3-file-2-desktop--tablet)
4. [File 3: Component Library](#4-file-3-component-library)
5. [Pro Tips](#5-pro-tips)

---

## 1. Initial Setup

### 1.1 Create Your Files

1. Go to [figma.com](https://figma.com) and log in
2. Click **"New design file"** three times to create:
   - `MetAds - Mobile`
   - `MetAds - Desktop & Tablet`
   - `MetAds - Components`

### 1.2 Set Up Color Styles (Do this in Components file first)

1. Open `MetAds - Components`
2. Draw a small rectangle
3. Set fill to `#6366F1` (primary-500)
4. Right-click the color → **"Create style"**
5. Name it `primary/500`
6. Repeat for all colors from `design-tokens.json`:

```
Primary Colors:
- primary/50:  #EEF2FF
- primary/100: #E0E7FF
- primary/500: #6366F1
- primary/600: #4F46E5
- primary/700: #4338CA

Grays:
- gray/50:  #F9FAFB
- gray/100: #F3F4F6
- gray/200: #E5E7EB
- gray/500: #6B7280
- gray/800: #1F2937
- gray/900: #111827

Status:
- success/main: #10B981
- warning/main: #F59E0B
- error/main:   #EF4444

Platforms:
- platform/instagram: #E4405F
- platform/facebook:  #1877F2
```

### 1.3 Set Up Text Styles

1. Create a text layer
2. Set font to **Inter** (install from Google Fonts if needed)
3. For each style below, create a text style:

```
heading/h1:     24px, Bold (700)
heading/h2:     20px, Semibold (600)
heading/h3:     16px, Semibold (600)
body/large:     16px, Regular (400)
body/default:   14px, Regular (400)
body/small:     12px, Regular (400)
label/default:  12px, Medium (500), UPPERCASE, 5% letter spacing
badge/text:     12px, Semibold (600)
```

### 1.4 Import SVG Assets

1. Drag the SVG files from `figma/assets/` into your Figma file
2. They will appear as vector shapes you can reuse

---

## 2. File 1: Mobile App

### 2.1 Frame Setup

Create these frames (press **F** for frame tool):

| Frame Name | Size | Description |
|------------|------|-------------|
| `Mobile/Search` | 390 × 844 | iPhone 14 Pro size |
| `Mobile/Results` | 390 × 844 | Results list |
| `Mobile/AdDetail` | 390 × 844 | Full ad detail |
| `Mobile/RelatedAds` | 390 × 844 | Variants panel |
| `Mobile/SavedAds` | 390 × 844 | Saved ads list |

### 2.2 Build: Mobile Header

1. Create frame: 390 × 56px
2. Background: `#FFFFFF`
3. Add bottom border: 1px `gray/200`
4. Left: Hamburger icon (≡) - 24×24px
5. Center: "MetAds" text - `heading/h3`
6. Right: User avatar circle - 32×32px

```
┌─────────────────────────────────────┐
│  ≡        MetAds            [👤]    │  56px height
└─────────────────────────────────────┘
```

### 2.3 Build: Mobile Bottom Navigation

1. Create frame: 390 × 56px
2. Background: `#FFFFFF`
3. Top border: 1px `gray/200`
4. Three equal sections (130px each):
   - Search icon + "Search"
   - List icon + "Results"
   - Star icon + "Saved"
5. Active state: `primary/600` color
6. Inactive state: `gray/400` color

```
┌─────────────────────────────────────┐
│  [🔍 Search]  [📋 Results]  [⭐ Saved] │  56px height
└─────────────────────────────────────┘
```

### 2.4 Build: Ad Result Card (Mobile)

1. Create frame: 358 × auto (390 - 32px padding)
2. Background: `#FFFFFF`
3. Border radius: 8px
4. Shadow: `0 1px 2px rgba(0,0,0,0.05)`
5. Padding: 16px

**Structure:**
```
┌───────────────────────────────────┐
│ ┌──────┐                          │
│ │      │  Page Name (h3)          │
│ │ 80×80│  ─────────────────────   │
│ │      │  Headline text preview   │
│ └──────┘  that wraps to two...    │
│                                   │
│  [IG] [FB]   67 days   4 var  >   │
└───────────────────────────────────┘
```

**Elements:**
- Thumbnail: 80×80px, rounded 8px, gray placeholder
- Page Name: `heading/h3`, `gray/900`
- Headline: `body/default`, `gray/600`, max 2 lines
- Platform badges: 24×24px icons
- Days badge: `badge/text`, background `primary/50`, text `primary/700`
- Variants badge: `badge/text`, background `warning/light`, text `warning/dark`
- Chevron: 20×20px, `gray/400`

### 2.5 Build: Ad Detail Screen (Mobile)

**Layout from top to bottom:**

1. **Header** (56px)
   - Back arrow (←)
   - "Ad Detail" title
   - Save icon (bookmark)

2. **Creative Preview** (full width, 1:1 aspect ratio)
   - 358×358px placeholder
   - Rounded corners: 8px
   - Gray background with play icon centered (for video)

3. **Page Info Section**
   - Page Name: `heading/h2`
   - Handle: `body/small`, `gray/500`
   - Verified badge (optional)

4. **Metrics Row** (3 columns)
   ```
   ┌─────────┬─────────┬─────────┐
   │ 67 days │  IG FB  │ Active  │
   │ active  │         │   ●     │
   └─────────┴─────────┴─────────┘
   ```
   - Background: `gray/50`
   - Border radius: 8px
   - Padding: 12px

5. **Related Ads Card** (NEW!)
   ```
   ┌─────────────────────────────────┐
   │  RELATED ADS                    │
   │  ─────────────────────────────  │
   │  [4 variants from this →]       │
   │  advertiser                     │
   │  Longest: 67 days               │
   │  Newest: 12 days ago            │
   └─────────────────────────────────┘
   ```
   - Background: `gray/50`
   - Border: 1px `gray/200`
   - Clickable (hand cursor)

6. **Content Sections**
   - Each with: Label (`label/default`) + Content (`body/default`)
   - Sections: Headline, Body, CTA, Landing Page

7. **Action Buttons**
   - Two buttons side by side
   - "View on Meta" - outlined style
   - "Copy Ad Text" - outlined style

### 2.6 Build: Related Ads Screen (Mobile)

**Layout:**

1. **Header**
   - Back arrow
   - "Related Ads (4)"
   - Page name on right

2. **Variant Insights Card**
   ```
   ┌─────────────────────────────────┐
   │  VARIANT INSIGHTS               │
   │  ─────────────────────────────  │
   │  Longest running: 67 days       │
   │  All use same CTA: Learn More   │
   │  Headlines differ (A/B test)    │
   └─────────────────────────────────┘
   ```
   - Background: `primary/50`
   - Border radius: 8px

3. **Variant Cards List**
   - Same as Ad Result Card but with special badges:
   - ★ LONGEST - `success/light` background
   - ✦ NEWEST - `primary/100` background

---

## 3. File 2: Desktop & Tablet

### 3.1 Frame Setup

| Frame Name | Size | Description |
|------------|------|-------------|
| `Desktop/Main` | 1440 × 900 | Full desktop view |
| `Tablet/Main` | 1024 × 768 | Tablet landscape |
| `Tablet/FiltersOpen` | 1024 × 768 | With filter drawer |

### 3.2 Build: Desktop 3-Column Layout

**Overall structure:**
```
┌────────────────────────────────────────────────────────────┐
│  HEADER (64px)                                             │
├──────────┬─────────────────┬───────────────────────────────┤
│  SEARCH  │  RESULTS LIST   │  AD DETAIL                    │
│  PANEL   │                 │                               │
│  250px   │  350px          │  Flexible (min 400px)         │
│          │                 │                               │
└──────────┴─────────────────┴───────────────────────────────┘
```

**Search Panel (250px width):**
1. Search input (full width - 32px padding)
2. Filter sections:
   - Platform (radio buttons)
   - Country (dropdown)
   - Status (radio buttons)
   - Days Active (min/max inputs)
   - Date Range (dropdown)
3. Search button (full width)

**Results List (350px width):**
1. Header: "Found: 247 ads" + Sort dropdown
2. Scrollable list of Ad Result Cards (desktop version - 60×60 thumbnails)
3. "Load more results..." at bottom

**Ad Detail Panel (flexible):**
1. Creative Preview (max 400px width)
2. Page info
3. Metrics section with Related Ads link
4. Ad Copy sections
5. Action buttons

### 3.3 Build: Tablet 2-Column Layout

**Structure:**
```
┌────────────────────────────────────────────────────────────┐
│  HEADER + SEARCH BAR + FILTERS TOGGLE                      │
├─────────────────────┬──────────────────────────────────────┤
│  RESULTS LIST       │  AD DETAIL                           │
│  ~40% width         │  ~60% width                          │
└─────────────────────┴──────────────────────────────────────┘
```

- Collapsible filter drawer that slides down
- Results and Detail split the remaining space

---

## 4. File 3: Component Library

### 4.1 Components to Create

Use Figma's **Component** feature (Ctrl/Cmd + Alt + K):

**Buttons:**
- `Button/Primary` - Filled, primary color
- `Button/Secondary` - Outlined
- `Button/Ghost` - Text only

**Inputs:**
- `Input/Text` - Standard text input
- `Input/Dropdown` - With chevron
- `Input/Search` - With search icon

**Cards:**
- `Card/AdResult/Mobile` - 80px thumbnail
- `Card/AdResult/Desktop` - 60px thumbnail
- `Card/AdDetail/Section` - Label + content

**Badges:**
- `Badge/Days` - Primary colors
- `Badge/Variants` - Warning colors
- `Badge/Platform/IG` - Instagram pink
- `Badge/Platform/FB` - Facebook blue
- `Badge/Status/Active` - Green dot
- `Badge/Status/Inactive` - Gray dot
- `Badge/Longest` - Star + green
- `Badge/Newest` - Sparkle + blue

**Navigation:**
- `Nav/Header/Mobile`
- `Nav/Header/Desktop`
- `Nav/BottomBar`
- `Nav/TabItem`

### 4.2 Using Variants

For components with states, use Figma Variants:

1. Select your component
2. Click "Add variant" in right panel
3. Create variants for:
   - **Button**: Default, Hover, Pressed, Disabled
   - **Card**: Default, Hover, Selected
   - **Input**: Default, Focus, Error
   - **TabItem**: Active, Inactive

---

## 5. Pro Tips

### 5.1 Keyboard Shortcuts

| Action | Mac | Windows |
|--------|-----|---------|
| Create frame | F | F |
| Create rectangle | R | R |
| Create text | T | T |
| Create component | ⌘⌥K | Ctrl+Alt+K |
| Duplicate | ⌘D | Ctrl+D |
| Group | ⌘G | Ctrl+G |
| Auto layout | ⇧A | Shift+A |

### 5.2 Auto Layout Tips

Use Auto Layout for:
- Cards (vertical stack)
- Button content (horizontal, centered)
- Badge content (horizontal, padding)
- Lists (vertical, gap 8px)

### 5.3 Naming Convention

Use `/` for hierarchy:
```
Components/Card/AdResult/Mobile
Components/Badge/Platform/Instagram
Screens/Mobile/Search
Screens/Desktop/Main
```

### 5.4 Prototype Connections

To make it interactive:
1. Select a frame or element
2. Go to "Prototype" tab (right panel)
3. Drag connection to destination frame
4. Set trigger (On tap) and animation (Smart animate)

**Key flows to connect:**
- Results card → Ad Detail
- Related Ads link → Related Ads panel
- Bottom nav tabs → respective screens
- Back arrows → previous screens

### 5.5 Exporting for Development

When ready to hand off:
1. Select frames/components
2. Right panel → Export section
3. Add export settings:
   - 1x PNG for previews
   - 2x PNG for retina
   - SVG for icons

---

## Quick Reference: Key Dimensions

| Element | Mobile | Desktop |
|---------|--------|---------|
| Screen width | 390px | 1440px |
| Header height | 56px | 64px |
| Bottom nav | 56px | N/A |
| Card thumbnail | 80×80px | 60×60px |
| Card padding | 16px | 16px |
| Section gap | 24px | 24px |
| Border radius | 8px | 8px |
| Input height | 44px | 44px |
| Button height | 44px | 44px |

---

*Guide Version: 1.0*
*For use with: design-tokens.json*
