# MetAds Figma Preparation Package

This folder contains everything you need to build the MetAds UI in Figma efficiently.

## Contents

```
figma/
├── README.md                  ← You are here
├── design-tokens.json         ← Colors, typography, spacing values
├── setup-guide.md             ← Step-by-step Figma instructions
└── assets/
    ├── components/            ← SVG component templates
    │   ├── ad-card-mobile.svg
    │   ├── ad-card-desktop.svg
    │   ├── button-primary.svg
    │   ├── button-secondary.svg
    │   ├── input-search.svg
    │   ├── badge-days.svg
    │   ├── badge-variants.svg
    │   ├── badge-longest.svg
    │   ├── badge-newest.svg
    │   ├── badge-platform-ig.svg
    │   ├── badge-platform-fb.svg
    │   ├── status-active.svg
    │   ├── status-inactive.svg
    │   ├── metrics-row.svg
    │   └── related-ads-card.svg
    └── icons/                 ← UI icons (24x24)
        ├── search.svg
        ├── list.svg
        ├── star.svg
        ├── star-filled.svg
        ├── arrow-left.svg
        ├── arrow-right.svg
        ├── chevron-down.svg
        ├── menu.svg
        ├── bookmark.svg
        ├── bookmark-filled.svg
        ├── copy.svg
        ├── external-link.svg
        ├── filter.svg
        ├── play.svg
        ├── user.svg
        ├── x-close.svg
        ├── instagram.svg
        └── facebook.svg
```

## Quick Start

### 1. Read the Setup Guide
Open `setup-guide.md` for step-by-step instructions on building each screen in Figma.

### 2. Reference Design Tokens
Use `design-tokens.json` to copy exact color values, font sizes, and spacing into Figma's style system.

### 3. Import SVG Assets
Drag and drop SVG files directly into Figma:
- They will appear as editable vector shapes
- You can modify colors, sizes, and convert to components

## How to Import SVGs into Figma

1. Open your Figma file
2. Drag SVG files from this folder onto the Figma canvas
3. The vectors will appear as grouped shapes
4. Right-click → "Create component" to make them reusable

## Figma File Organization

With your 3 free files, organize as follows:

| File | Purpose |
|------|---------|
| **MetAds - Mobile** | All 5 mobile screens |
| **MetAds - Desktop & Tablet** | Desktop 3-column + Tablet 2-column layouts |
| **MetAds - Components** | Reusable UI components and style definitions |

## Key Design Decisions

### Colors
- **Primary**: Indigo (#6366F1) - Actions, links, selected states
- **Success**: Green (#10B981) - Active status, longest variant badge
- **Warning**: Amber (#F59E0B) - Variant count badge
- **Platforms**: IG Pink (#E4405F), FB Blue (#1877F2)

### Typography
- **Font**: Inter (free from Google Fonts)
- **Page names**: 16px Semibold
- **Body text**: 14px Regular
- **Badges/Labels**: 12px Semibold

### Spacing
- **Card padding**: 16px
- **Card gap**: 8px
- **Section gap**: 24px
- **Border radius**: 8px (cards, buttons, inputs)

## Tips for Figma Beginners

1. **Use Auto Layout** (Shift+A) for everything that stacks vertically or horizontally
2. **Create components** early - you'll reuse cards and badges many times
3. **Use color styles** - define once, update everywhere
4. **Name layers properly** - makes handoff easier later

## Related Documentation

- `docs/wireframes.md` - Full wireframe specifications and feature details
- `docs/Meta_Ads_Reverse_Engineering.md` - Project overview and technical architecture

---

*Package Version: 1.0*
*Created: January 30, 2026*
